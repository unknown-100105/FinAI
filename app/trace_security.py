"""Opt-in boundary for sensitive explainability trace endpoints."""
from __future__ import annotations

import os

from fastapi import HTTPException


def require_trace_api_enabled() -> None:
    """Only expose trace APIs when explicitly enabled behind bearer auth."""
    enabled = os.getenv("FINAI_ENABLE_XAI_TRACE_API", "").strip().casefold()
    mode = os.getenv("FINAI_API_AUTH_MODE", "development").strip().casefold()
    environment = os.getenv("FINAI_ENV", "development").strip().casefold()

    if enabled not in {"1", "true", "yes", "on"}:
        raise HTTPException(status_code=404, detail="XAI trace API is disabled.")

    # A shared bearer is only a deployment boundary, not per-user identity.
    # Do not allow trace APIs in open development mode; use a verified identity
    # gateway/principal-aware authorization before exposing traces to multiple users.
    if mode != "bearer":
        raise HTTPException(
            status_code=404,
            detail="XAI trace API requires FINAI_API_AUTH_MODE=bearer and a verified identity gateway for multi-user deployments.",
        )
