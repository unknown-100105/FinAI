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


def assert_cloud_provider_allowed(
    provider: str,
    *,
    network_mode: Optional[str] = None,
    data_sensitivity: Optional[str] = None,
    allowed_providers: Optional[list[str] | tuple[str, ...] | set[str]] = None,
) -> None:
    """Guard cloud-provider calls at both gateway and provider boundaries."""
    provider_id = str(provider).strip().lower()
    if not provider_id:
        raise ValueError("provider must not be empty.")

    assert_external_network_allowed(
        f"{provider_id} cloud provider",
        network_mode=network_mode,
    )

    sensitivity = (
        os.getenv("FINAI_DATA_SENSITIVITY", "standard")
        if data_sensitivity is None
        else data_sensitivity
    )
    sensitivity = str(sensitivity).strip().lower() or "standard"
    if sensitivity not in {"public", "standard", "financial", "restricted"}:
        raise ValueError(
            "FINAI_DATA_SENSITIVITY must be one of: public, standard, financial, restricted."
        )
    if sensitivity == "restricted":
        raise NetworkAccessDisabledError(
            f"Cloud provider '{provider_id}' is not permitted for restricted data."
        )

    env_allowed = {
        item.strip().lower()
        for item in os.getenv("FINAI_ALLOWED_PROVIDERS", "").split(",")
        if item.strip()
    }
    request_allowed = {
        str(item).strip().lower()
        for item in (allowed_providers or ())
        if str(item).strip()
    }
    allowed = request_allowed or env_allowed
    if allowed and provider_id not in allowed:
        raise NetworkAccessDisabledError(
            f"Cloud provider '{provider_id}' is not present in the configured provider allow-list."
        )
