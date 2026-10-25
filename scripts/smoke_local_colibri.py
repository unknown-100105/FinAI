"""Opt-in-cost, loopback-only generation smoke test for the FinAI Colibrì adapter.

Loads repository .env without overriding explicit shell variables. This script
calls only the separately managed local inference server; it never falls back
to a cloud provider and never prints prompts, generated text, or API keys.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = None


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--timeout-seconds",
        type=float,
        default=120.0,
        help="Maximum local completion timeout for this synthetic smoke test.",
    )
    parser.add_argument(
        "--required",
        action="store_true",
        help="Return a nonzero exit code when Colibrì is not configured.",
    )
    args = parser.parse_args()
    if args.timeout_seconds <= 0:
        parser.error("--timeout-seconds must be positive")

    if load_dotenv is not None:
        load_dotenv(ROOT / ".env", override=False)

    base_url = os.getenv("FINAI_COLIBRI_BASE_URL", "").strip()
    if not base_url:
        report = {
            "status": "skipped_unconfigured",
            "provider": "local_colibri",
            "network_calls": 0,
            "reason": "FINAI_COLIBRI_BASE_URL is not set; no model request was made.",
        }
        print(json.dumps(report, indent=2))
        return 2 if args.required else 0

    # The adapter enforces localhost / 127.0.0.1 / ::1 and rejects redirects.
    # Set a bounded timeout for this test rather than trusting an arbitrarily
    # long runtime timeout configured for interactive use, then restore it.
    original_timeout = os.environ.get("FINAI_COLIBRI_TIMEOUT_SECONDS")
    os.environ["FINAI_COLIBRI_TIMEOUT_SECONDS"] = format(args.timeout_seconds, "g")
    try:
        try:
            from llm.colibri_adapter import ColibriResponseAdapter

            adapter = ColibriResponseAdapter()
            started = time.perf_counter()
            result = adapter.generate(
                user_text="Define revenue in one short sentence.",
                intent="GENERAL_FINANCE",
                verified_result={
                    "smoke_test": True,
                    "synthetic": True,
                    "purpose": "local_runtime_connectivity_only",
                },
                source="synthetic_local_colibri_smoke",
                language="English",
                persona="neutral",
                max_new_tokens=48,
            )
            latency_ms = round((time.perf_counter() - started) * 1000, 1)
            response_text = str(result.get("response", "")).strip()
            if result.get("status") != "GENERATED" or not response_text:
                raise RuntimeError("Local runtime returned no completed response.")

            usage = result.get("usage") or {}
            report = {
                "status": "passed",
                "provider": "local_colibri",
                "model": str(result.get("model_name", os.getenv("FINAI_COLIBRI_MODEL", "unknown"))),
                "latency_ms": latency_ms,
                "response_characters": len(response_text),
                "prompt_tokens": usage.get("prompt_tokens"),
                "completion_tokens": usage.get("completion_tokens"),
                "network_target": "loopback_only",
                "cloud_fallback_used": False,
                "response_text_printed": False,
            }
            print(json.dumps(report, indent=2))
            return 0
        except Exception as exc:
            # Surface only safe diagnostic metadata. Never print exception messages:
            # third-party errors occasionally include request configuration details.
            print(json.dumps({
                "status": "failed",
                "provider": "local_colibri",
                "error_type": type(exc).__name__,
                "network_target": "loopback_only",
                "cloud_fallback_used": False,
                "response_text_printed": False,
            }, indent=2))
            return 1
    finally:
        if original_timeout is None:
            os.environ.pop("FINAI_COLIBRI_TIMEOUT_SECONDS", None)
        else:
            os.environ["FINAI_COLIBRI_TIMEOUT_SECONDS"] = original_timeout


if __name__ == "__main__":
    raise SystemExit(main())
