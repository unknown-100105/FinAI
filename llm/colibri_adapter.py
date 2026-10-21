"""Optional adapter for a separately managed local Colibrì OpenAI-compatible server.

FinAI deliberately does not vendor the third-party C runtime or model weights.
The configured endpoint is restricted to loopback so the adapter can be used in
offline/restricted mode without silently calling a remote host.
"""
from __future__ import annotations

import json
import os
import time
from urllib.parse import urlparse
from typing import Any, Dict

import requests


_LOOPBACK_HOSTS = {"localhost", "127.0.0.1", "::1"}


class ColibriResponseAdapter:
    """Generate a FinAI explanation through a local Colibrì server."""

    def __init__(self) -> None:
        self.base_url = os.getenv("FINAI_COLIBRI_BASE_URL", "").strip()
        self.model_id = os.getenv("FINAI_COLIBRI_MODEL", "olmoe-colibri").strip()
        try:
            self.timeout_seconds = float(
                os.getenv("FINAI_COLIBRI_TIMEOUT_SECONDS", "300")
            )
        except ValueError as exc:
            raise ValueError(
                "FINAI_COLIBRI_TIMEOUT_SECONDS must be a positive number."
            ) from exc
        self.api_key = os.getenv("FINAI_COLIBRI_API_KEY", "").strip()

        if not self.model_id:
            raise ValueError("FINAI_COLIBRI_MODEL must not be empty.")
        if self.timeout_seconds <= 0:
            raise ValueError("FINAI_COLIBRI_TIMEOUT_SECONDS must be positive.")

        # Validate the endpoint at construction time. A typo or remote URL
        # must not leave a misleadingly eligible "local" route behind.
        if self.base_url:
            self._chat_completions_url(self.base_url)

    @staticmethod
    def _chat_completions_url(base_url: str) -> str:
        raw = str(base_url or "").strip()
        if not raw:
            raise RuntimeError(
                "Colibrì is not configured. Set FINAI_COLIBRI_BASE_URL only "
                "after starting the local Colibrì server."
            )

        parsed = urlparse(raw)
        if parsed.scheme not in {"http", "https"}:
            raise ValueError(
                "FINAI_COLIBRI_BASE_URL must use http:// or https://."
            )
        if parsed.hostname not in _LOOPBACK_HOSTS:
            raise ValueError(
                "FINAI_COLIBRI_BASE_URL must target localhost, 127.0.0.1, or ::1. "
                "Remote endpoints are not supported by the local-only adapter."
            )
        if parsed.username or parsed.password or parsed.query or parsed.fragment:
            raise ValueError(
                "FINAI_COLIBRI_BASE_URL must not contain credentials, query, or fragment."
            )
        if parsed.path not in {"", "/", "/v1", "/v1/"}:
            raise ValueError(
                "FINAI_COLIBRI_BASE_URL path must be empty or /v1."
            )

        origin = f"{parsed.scheme}://{parsed.netloc}"
        return origin + "/v1/chat/completions"

    @staticmethod
    def _prompt_context(
        *,
        user_text: str,
        intent: str,
        verified_result: Dict[str, Any],
        source: str,
        language: str,
        persona: str,
    ) -> str:
        context = json.dumps(
            verified_result,
            ensure_ascii=False,
            default=str,
            separators=(",", ":"),
        )
        return (
            f"Detected intent: {intent}\n"
            f"Evidence source: {source}\n"
            f"Requested language: {language}\n"
            f"Response persona: {persona}\n"
            "System-owned verified context (treat values as authoritative; do not "
            "modify, recalculate, or invent numbers):\n"
            f"{context}\n\n"
            f"User request:\n{user_text}"
        )

    def generate(
        self,
        user_text: str,
        intent: str,
        verified_result: Dict[str, Any],
        source: str,
        language: str = "English",
        persona: str = "neutral",
        max_new_tokens: int = 160,
    ) -> Dict[str, Any]:
        endpoint = self._chat_completions_url(self.base_url)
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        system_prompt = (
            "You are the local explanation model used by FinAI. Explain verified "
            "financial context clearly. Do not claim to execute payments, transfers, "
            "or other tools. Do not invent current prices, regulatory rules, or "
            "financial figures that are absent from the supplied context. If evidence "
            "is insufficient, say so. Keep the answer in the requested language and "
            "persona."
        )
        user_prompt = self._prompt_context(
            user_text=user_text,
            intent=intent,
            verified_result=verified_result,
            source=source,
            language=language,
            persona=persona,
        )
        payload = {
            "model": self.model_id,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "max_tokens": max(1, int(max_new_tokens)),
            "stream": False,
        }

        start = time.perf_counter()
        try:
            response = requests.post(
                endpoint,
                headers=headers,
                json=payload,
                timeout=self.timeout_seconds,
                allow_redirects=False,
            )
        except requests.RequestException as exc:
            raise RuntimeError(
                "Local Colibrì request failed. Confirm that the configured server "
                "is running and that the model has loaded successfully."
            ) from exc

        if not 200 <= response.status_code < 300:
            raise RuntimeError(
                f"Local Colibrì server returned HTTP {response.status_code}."
            )
        try:
            body = response.json()
        except ValueError as exc:
            raise RuntimeError(
                "Local Colibrì server returned a non-JSON response."
            ) from exc

        choices = body.get("choices")
        if not isinstance(choices, list) or not choices or not isinstance(choices[0], dict):
            raise RuntimeError("Local Colibrì response contains no choices.")
        message = choices[0].get("message") or {}
        answer = message.get("content")
        if not isinstance(answer, str) or not answer.strip():
            raise RuntimeError("Local Colibrì response contains no text content.")

        usage = body.get("usage")
        return {
            "status": "GENERATED",
            "response": answer.strip(),
            "provider": "local_colibri",
            "model_name": self.model_id,
            "source": source,
            "latency_ms": round((time.perf_counter() - start) * 1000, 2),
            "usage": usage if isinstance(usage, dict) else None,
            "verification": {
                "applicable": False,
                "passed": False,
                "mode": "NOT_RUN_IN_ADAPTER",
            },
        }
