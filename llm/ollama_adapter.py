"""Ollama local chat adapter for FinAI's ModelGateway.

The adapter intentionally uses the Ollama HTTP API via requests so Ollama remains
an optional external runtime rather than a mandatory Python dependency.
"""
from __future__ import annotations

import os
import time
from typing import Any, Dict

import requests


class OllamaResponseAdapter:
    provider_id = "ollama"

    def __init__(
        self,
        model_name: str | None = None,
        base_url: str | None = None,
        timeout_seconds: float = 90.0,
    ) -> None:
        self.model_name = (
            model_name or os.getenv("OLLAMA_MODEL", "qwen3:4b")
        ).strip()
        self.base_url = (
            base_url or os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434")
        ).strip().rstrip("/")
        self.timeout_seconds = float(timeout_seconds)
        if not self.base_url.startswith(("http://", "https://")):
            raise ValueError("OLLAMA_BASE_URL must be an http(s) URL")
        if self.timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be positive")

    @staticmethod
    def _build_system_prompt(
        intent: str,
        verified_result: Dict[str, Any],
        source: str,
        language: str,
        persona: str,
    ) -> str:
        return (
            "You are FinAI, a financial-domain assistant.\n"
            "Follow the supplied verified result exactly. Never invent, "
            "recalculate, alter, or omit verified financial values. "
            "The system, not the language model, is authoritative for "
            "calculations and actions. Use supplied reference evidence as the "
            "source of factual claims. Answer in the requested language; "
            "persona affects style only.\n\n"
            f"LANGUAGE: {language}\nPERSONA: {persona}\n"
            f"INTENT: {intent}\nSOURCE: {source}\n"
            f"VERIFIED SYSTEM RESULT:\n{verified_result}"
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
        if not self.model_name:
            raise RuntimeError("OLLAMA_MODEL is not configured.")

        payload = {
            "model": self.model_name,
            "stream": False,
            "messages": [
                {
                    "role": "system",
                    "content": self._build_system_prompt(
                        intent, verified_result, source, language, persona
                    ),
                },
                {"role": "user", "content": str(user_text)},
            ],
            "options": {"num_predict": int(max_new_tokens)},
        }
        start = time.perf_counter()
        try:
            response = requests.post(
                f"{self.base_url}/api/chat",
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=self.timeout_seconds,
            )
        except requests.RequestException as exc:
            raise RuntimeError(f"Ollama request failed: {exc}") from exc
        latency_seconds = time.perf_counter() - start

        if response.status_code >= 400:
            detail = str(getattr(response, "text", ""))[:500]
            raise RuntimeError(
                f"Ollama API request failed ({response.status_code}): {detail}"
            )
        try:
            data = response.json()
            text = data["message"]["content"]
        except (ValueError, KeyError, IndexError, TypeError) as exc:
            raise RuntimeError("Ollama API returned no usable text response.") from exc

        text = str(text).strip()
        if not text:
            raise RuntimeError("Ollama API returned an empty response.")

        return {
            "status": "GENERATED",
            "provider_id": self.provider_id,
            "model_name": self.model_name,
            "response": text,
            "metrics": {"latency_seconds": round(latency_seconds, 4)},
        }
