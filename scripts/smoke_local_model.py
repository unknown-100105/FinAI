"""End-to-end local Colibri smoke test for an already-running FinAI API.

This script calls only a loopback FinAI API. It checks that the backend is in
offline mode, explicitly probes the configured local model list, then sends a
synthetic non-sensitive chat request with the local model ID pinned. It never
calls cloud providers directly.
"""
from __future__ import annotations

import argparse
import os
import sys
from uuid import uuid4
from urllib.parse import urlparse

import requests

DEFAULT_API = "http://127.0.0.1:8000"
LOCAL_MODEL_ID = "colibri-local"
SUCCESS_STATUSES = {"GENERATED", "GENERATED_VERIFIED"}


def loopback_base_url(value: str) -> str:
    parsed = urlparse(value.strip())
    if parsed.scheme not in {"http", "https"} or parsed.hostname not in {
        "127.0.0.1", "localhost", "::1"
    }:
        raise ValueError("FinAI API base URL must be a loopback URL (localhost/127.0.0.1/::1).")
    if parsed.username or parsed.password or parsed.query or parsed.fragment:
        raise ValueError("FinAI API base URL must not contain credentials, query, or fragment.")
    return value.rstrip("/")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--api-base-url",
        default=os.getenv("FINAI_API_BASE_URL", DEFAULT_API),
        help="Loopback FinAI API URL (default: %(default)s).",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=180.0,
        help="Maximum seconds for the chat generation call (default: %(default)s).",
    )
    args = parser.parse_args()

    if args.timeout <= 0 or args.timeout > 600:
        print("FAIL: --timeout must be greater than 0 and at most 600 seconds.", file=sys.stderr)
        return 2
    try:
        base_url = loopback_base_url(args.api_base_url)
    except ValueError as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 2

    headers = {"Accept": "application/json", "Content-Type": "application/json"}
    bearer = os.getenv("FINAI_API_BEARER_TOKEN", "").strip()
    if bearer:
        headers["Authorization"] = f"Bearer {bearer}"

    try:
        health = requests.get(f"{base_url}/health", headers=headers, timeout=3, allow_redirects=False)
        health.raise_for_status()
    except requests.RequestException:
        print("FAIL: FinAI API health check failed. Start the API on loopback first.", file=sys.stderr)
        return 1

    try:
        brain_response = requests.get(
            f"{base_url}/api/v1/system/brain-status",
            headers=headers,
            timeout=5,
            allow_redirects=False,
        )
        brain_response.raise_for_status()
        brain = brain_response.json()
    except (requests.RequestException, ValueError):
        print("FAIL: Could not read FinAI Brain diagnostics.", file=sys.stderr)
        return 1

    layers = {
        item.get("id"): item
        for item in brain.get("layers", [])
        if isinstance(item, dict)
    }
    offline = layers.get("offline_inference", {})
    network_mode = str(offline.get("network_mode", "")).strip().lower()
    if network_mode != "offline":
        print(
            "FAIL: FinAI backend is not configured with FINAI_NETWORK_MODE=offline. "
            f"Reported mode: {network_mode or 'unknown'}.",
            file=sys.stderr,
        )
        return 1

    try:
        status_response = requests.get(
            f"{base_url}/api/v1/system/local-model-status?probe=true",
            headers=headers,
            timeout=5,
            allow_redirects=False,
        )
        status_response.raise_for_status()
        local_status = status_response.json()
    except (requests.RequestException, ValueError):
        print("FAIL: Could not probe the local Colibri model endpoint.", file=sys.stderr)
        return 1

    if local_status.get("status") != "model_listed_not_inference_verified":
        print(
            "FAIL: Configured local model was not found by the server model-list probe. "
            f"Status: {local_status.get('status', 'unknown')}.",
            file=sys.stderr,
        )
        return 1

    payload = {
        "message": (
            "This is a local inference smoke test, not a request for live market data. "
            "Explain compound interest in one short sentence and include the marker "
            "FINAI_LOCAL_INFERENCE_SMOKE_OK."
        ),
        "session_id": "local-smoke-" + uuid4().hex,
        "language": "English",
        "persona": "neutral",
        "generate_response": True,
        "max_new_tokens": 96,
        "model_id": LOCAL_MODEL_ID,
    }

    try:
        response = requests.post(
            f"{base_url}/api/v1/chat",
            headers=headers,
            json=payload,
            timeout=args.timeout,
            allow_redirects=False,
        )
        response.raise_for_status()
        result = response.json()
    except requests.Timeout:
        print("FAIL: FinAI local generation timed out. Check runtime/model load and timeout settings.", file=sys.stderr)
        return 1
    except requests.RequestException:
        print("FAIL: FinAI chat API request failed. Review the local API logs for the server-side cause.", file=sys.stderr)
        return 1
    except ValueError:
        print("FAIL: FinAI chat API returned a non-JSON response.", file=sys.stderr)
        return 1

    generation = result.get("response_generation")
    if not isinstance(generation, dict):
        print(
            "FAIL: Chat response did not include response_generation; "
            "the request may have been routed to a non-generative or blocked path.",
            file=sys.stderr,
        )
        print(f"Overall status: {result.get('status', 'unknown')}", file=sys.stderr)
        return 1

    status = str(generation.get("status", "")).upper()
    model_id = str(generation.get("model_id", ""))
    text = str(generation.get("response", "")).strip()
    if status not in SUCCESS_STATUSES or not text:
        print(
            "FAIL: Local model did not produce a successful generated response. "
            f"Generation status: {status or 'unknown'}.",
            file=sys.stderr,
        )
        return 1
    if model_id and model_id != LOCAL_MODEL_ID:
        print(
            f"FAIL: Expected {LOCAL_MODEL_ID}, but response metadata reports {model_id}.",
            file=sys.stderr,
        )
        return 1

    print("PASS: FinAI API health check succeeded.")
    print("PASS: Brain diagnostics report offline mode.")
    print("PASS: Configured local model ID was returned by the loopback server.")
    print(f"PASS: FinAI generated a response with status {status} via {model_id or LOCAL_MODEL_ID}.")
    print(f"Response preview: {text[:240]}")
    print("Scope: this verifies one local smoke request only, not model quality or financial accuracy.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
