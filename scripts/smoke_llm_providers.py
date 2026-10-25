"""Opt-in live connectivity smoke test for configured FinAI cloud LLM providers.

This script sends a synthetic, non-personal prompt to configured providers and may
incur API charges. No network request is made unless --live is supplied. Output
never includes API keys or generated response text.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import sys
import time
from typing import Any, Callable

# When executed as `python scripts/smoke_llm_providers.py`, Python puts the
# scripts directory (not the repository root) on sys.path. Add the root so
# repository packages such as `llm` and `policy` can be imported reliably.
_REPOSITORY_ROOT = str(Path(__file__).resolve().parents[1])
if _REPOSITORY_ROOT not in sys.path:
    sys.path.insert(0, _REPOSITORY_ROOT)


def load_project_env(root: Path = Path(_REPOSITORY_ROOT)) -> bool:
    """Load local .env values for CLI runs without overriding shell/CI secrets."""
    try:
        from dotenv import load_dotenv
    except ImportError:
        return False
    return bool(load_dotenv(dotenv_path=Path(root) / ".env", override=False))


PROVIDER_ENV = {
    "openai": "OPENAI_API_KEY",
    "gemini": "GEMINI_API_KEY",
    "openrouter": "OPENROUTER_API_KEY",
    "anthropic": "ANTHROPIC_API_KEY",
    "mistral": "MISTRAL_API_KEY",
}


def _provider_factories() -> dict[str, tuple[str, Callable[[], Any]]]:
    # Import provider classes without constructing clients or requiring keys.
    from llm.cloud.anthropic import AnthropicProvider
    from llm.cloud.gemini import GeminiProvider
    from llm.cloud.mistral import MistralProvider
    from llm.cloud.openai_provider import OpenAIProvider
    from llm.cloud.openrouter import OpenRouterProvider

    return {
        "openai": ("OPENAI_API_KEY", OpenAIProvider),
        "gemini": ("GEMINI_API_KEY", GeminiProvider),
        "openrouter": ("OPENROUTER_API_KEY", OpenRouterProvider),
        "anthropic": ("ANTHROPIC_API_KEY", AnthropicProvider),
        "mistral": ("MISTRAL_API_KEY", MistralProvider),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--live",
        action="store_true",
        help="Actually call configured providers; requests may incur charges.",
    )
    parser.add_argument(
        "--provider",
        choices=("all", *PROVIDER_ENV.keys()),
        default="all",
        help="Provider to inspect or smoke-test (default: all).",
    )
    args = parser.parse_args()
    # Local developer convenience: never override explicit shell/CI environment values.
    load_project_env()

    network_mode = os.getenv("FINAI_NETWORK_MODE", "online").strip().lower()
    sensitivity = os.getenv("FINAI_DATA_SENSITIVITY", "standard").strip().lower()
    allowlist = {
        item.strip().lower()
        for item in os.getenv("FINAI_ALLOWED_PROVIDERS", "").split(",")
        if item.strip()
    }

    factories = _provider_factories()
    names = list(factories) if args.provider == "all" else [args.provider]
    results: list[dict[str, Any]] = []
    failures = 0
    attempted = 0

    for name in names:
        env_name, factory = factories[name]
        if not os.getenv(env_name, "").strip():
            results.append({"provider": name, "status": "skipped_no_credentials"})
            continue
        if not args.live:
            results.append({"provider": name, "status": "configured_not_called"})
            continue
        if network_mode == "offline":
            results.append({"provider": name, "status": "blocked_offline_mode"})
            continue
        if sensitivity == "restricted":
            results.append({"provider": name, "status": "blocked_restricted_data_mode"})
            continue
        if allowlist and name not in allowlist:
            results.append({"provider": name, "status": "blocked_provider_allowlist"})
            continue

        attempted += 1
        started = time.perf_counter()
        provider = None
        try:
            provider = factory()
            result = provider.generate(
                user_text=(
                    "Connectivity check only. Reply with a short acknowledgement; "
                    "do not provide financial advice."
                ),
                intent="GENERAL_FINANCE",
                verified_result={"smoke_test": True, "synthetic": True},
                source="synthetic_provider_smoke_test",
                language="English",
                persona="neutral",
                max_new_tokens=48,
            )
            response_text = str(result.get("response", "")).strip()
            if result.get("status") != "GENERATED" or not response_text:
                raise RuntimeError("Provider returned no completed text.")
            results.append(
                {
                    "provider": name,
                    "status": "passed",
                    "model": str(result.get("model_name", "unknown")),
                    "latency_ms": round((time.perf_counter() - started) * 1000, 1),
                    "response_characters": len(response_text),
                }
            )
        except Exception as exc:  # Report only safe metadata, not provider body or secrets.
            failures += 1
            status_code = getattr(exc, "status_code", None)
            response = getattr(exc, "response", None)
            if status_code is None and response is not None:
                status_code = getattr(response, "status_code", None)
            configured_model = (
                getattr(provider, "model_name", None)
                or getattr(provider, "model", None)
            )
            results.append(
                {
                    "provider": name,
                    "status": "failed",
                    "model": str(configured_model) if configured_model else "unknown",
                    "error_type": type(exc).__name__,
                    "error_status_code": status_code,
                    "latency_ms": round((time.perf_counter() - started) * 1000, 1),
                }
            )

    print(json.dumps({
        "mode": "live" if args.live else "configuration_only",
        "network_mode": network_mode,
        "data_sensitivity": sensitivity,
        "attempted_live_requests": attempted,
        "results": results,
        "note": (
            "Live requests use a synthetic prompt and may incur charges. "
            "Response text and credential values are never printed."
        ),
    }, indent=2))
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
