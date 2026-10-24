"""Explicit, bounded health probe for the optional loopback Colibri runtime.

The default response is configuration-only. Network I/O occurs only when
the probe query parameter is explicitly enabled, and non-loopback endpoints
are rejected by the existing adapter URL validator.
"""
from __future__ import annotations

import os
from typing import Any
from urllib.parse import urlparse

import requests
from fastapi import APIRouter, Query

from llm.colibri_adapter import ColibriResponseAdapter

router = APIRouter(prefix="/api/v1/system", tags=["system"])


@router.get("/local-model-status")
def local_model_status(probe: bool = Query(default=False)) -> dict[str, Any]:
    """Report local model configuration; optionally probe the server's model list."""
    base_url = os.getenv("FINAI_COLIBRI_BASE_URL", "").strip()
    model_id = os.getenv("FINAI_COLIBRI_MODEL", "olmoe-colibri").strip()
    if not base_url:
        return {
            "status": "unconfigured",
            "provider": "local_colibri",
            "configured": False,
            "probe_requested": probe,
            "reachable": False,
            "model_available": False,
            "message": "Set FINAI_COLIBRI_BASE_URL after starting the local server.",
        }

    try:
        models_url = ColibriResponseAdapter._chat_completions_url(base_url)
    except (ValueError, RuntimeError):
        return {
            "status": "invalid_configuration",
            "provider": "local_colibri",
            "configured": False,
            "probe_requested": probe,
            "reachable": False,
            "model_available": False,
            "message": "The local endpoint configuration is invalid; use a loopback /v1 URL.",
        }

    parsed = urlparse(models_url)
    models_url = f"{parsed.scheme}://{parsed.netloc}/v1/models"
    result: dict[str, Any] = {
        "status": "configured_not_probed",
        "provider": "local_colibri",
        "configured": True,
        "model_id": model_id,
        "probe_requested": probe,
        "reachable": False,
        "model_available": False,
        "message": "Configuration is present; server reachability and inference are not verified.",
    }
    if not probe:
        return result

    headers = {"Accept": "application/json"}
    api_key = os.getenv("FINAI_COLIBRI_API_KEY", "").strip()
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    try:
        response = requests.get(
            models_url,
            headers=headers,
            timeout=2.5,
            allow_redirects=False,
        )
        if not 200 <= response.status_code < 300:
            result.update(
                status="server_error",
                message=f"Local model server returned HTTP {response.status_code}.",
            )
            return result
        body = response.json()
    except requests.RequestException:
        result.update(
            status="unreachable",
            message="Could not reach the local model server; check that it is running.",
        )
        return result
    except ValueError:
        result.update(
            status="invalid_server_response",
            message="Local model server returned a non-JSON model list.",
        )
        return result

    entries = body.get("data") if isinstance(body, dict) else None
    if not isinstance(entries, list):
        result.update(
            status="invalid_server_response",
            reachable=True,
            message="The server response does not contain a compatible model list.",
        )
        return result

    available_ids = {
        entry.get("id")
        for entry in entries
        if isinstance(entry, dict) and isinstance(entry.get("id"), str)
    }
    available = model_id in available_ids
    result.update(
        status="model_listed_not_inference_verified" if available else "model_not_found",
        reachable=True,
        model_available=available,
        message=(
            "Configured model ID was returned by the local server. Run a test generation to verify inference."
            if available
            else "The configured model ID was not found in the local server's model list."
        ),
    )
    return result
