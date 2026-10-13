"""Central policy helpers for explicit online, degraded, and offline execution.

`offline` means external network calls are rejected rather than silently retried.
`degraded` prefers local models where available but may use remote services.
"""
from __future__ import annotations

import os
from typing import Optional

NETWORK_MODES = frozenset({"online", "degraded", "offline"})


class NetworkAccessDisabledError(RuntimeError):
    """Raised when a caller attempts an external request in offline mode."""


def get_network_mode(override: Optional[str] = None) -> str:
    raw = (
        os.getenv("FINAI_NETWORK_MODE", "online")
        if override is None
        else override
    )
    mode = str(raw).strip().lower()
    if not mode:
        mode = "online"
    if mode not in NETWORK_MODES:
        raise ValueError(
            "FINAI_NETWORK_MODE must be one of: online, degraded, offline."
        )
    return mode


def assert_external_network_allowed(
    operation: str,
    *,
    network_mode: Optional[str] = None,
) -> None:
    """Fail before any external call when the effective mode is offline."""
    mode = get_network_mode(network_mode)
    if mode == "offline":
        raise NetworkAccessDisabledError(
            f"External network access is disabled in offline mode; "
            f"operation '{operation}' was not attempted. Use available local "
            "artifacts/caches or explicitly switch FINAI_NETWORK_MODE to "
            "'degraded' or 'online'."
        )
