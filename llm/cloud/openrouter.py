import os
import time
from typing import Any, Dict

import requests

from .base import CloudLLMProvider
from policy.network_mode import assert_cloud_provider_allowed


class OpenRouterProvider(CloudLLMProvider):
    """
    OpenRouter chat-completions provider for FinAI.

    API key:
        OPENROUTER_API_KEY

    Model:
        OPENROUTER_MODEL
        Defaults to openrouter/auto when not configured.
    """

    provider_id = "openrouter"
    endpoint = "https://openrouter.ai/api/v1/chat/completions"

    def __init__(
        self,
        api_key: str | None = None,
        model_name: str | None = None,
        timeout_seconds: float = 30.0,
        http_referer: str | None = None,
        x_title: str | None = None,
    ):
        self.api_key = (
            api_key
            or os.getenv("OPENROUTER_API_KEY", "").strip()
        )

        self.model_name = (
            model_name
            or os.getenv("OPENROUTER_MODEL", "openrouter/auto").strip()
        )

        self.timeout_seconds = float(timeout_seconds)
        self.http_referer = (
            http_referer
            or os.getenv("OPENROUTER_HTTP_REFERER", "").strip()
        )
        self.x_title = (
            x_title
            or os.getenv("OPENROUTER_X_TITLE", "FinAI").strip()
        )

    def _build_prompt(
        self,
        user_text: str,
        intent: str,
        verified_result: Dict[str, Any],
        source: str,
        language: str,
        persona: str,
    ) -> str:
        return (
            "You are FinAI, a financial-domain AI assistant.\n\n"
            "IMPORTANT SYSTEM RULES:\n"
            "1. Follow the supplied verified result exactly.\n"
            "2. Never invent financial values.\n"
            "3. Never change, recalculate, rename, or omit "
            "verified financial values.\n"
            "4. When reference evidence is supplied, answer only "
            "from that evidence.\n"
            "5. The system, not the language model, is the authority "
            "for financial calculations and actions.\n"
            "6. Answer in the requested language.\n"
            "7. Use the requested persona only for communication style.\n\n"
            f"LANGUAGE: {language}\n"
            f"PERSONA: {persona}\n"
            f"INTENT: {intent}\n"
            f"SOURCE: {source}\n\n"
            f"VERIFIED SYSTEM RESULT:\n{verified_result}\n\n"
            f"USER REQUEST:\n{user_text}\n\n"
            "Provide only the final user-facing answer."
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

        if not self.api_key:
            raise RuntimeError(
                "OPENROUTER_API_KEY is not configured."
            )

        assert_cloud_provider_allowed("openrouter")

        prompt = self._build_prompt(
            user_text=user_text,
            intent=intent,
            verified_result=verified_result,
            source=source,
            language=language,
            persona=persona,
        )

        payload = {
            "model": self.model_name,
            "messages": [
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
            "max_tokens": int(max_new_tokens),
        }

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        if self.http_referer:
            headers["HTTP-Referer"] = self.http_referer

        if self.x_title:
            headers["X-Title"] = self.x_title

        start = time.perf_counter()

        response = requests.post(
            self.endpoint,
            headers=headers,
            json=payload,
            timeout=self.timeout_seconds,
        )

        latency_seconds = time.perf_counter() - start

        if response.status_code >= 400:
            raise RuntimeError(
                "OpenRouter API request failed "
                f"({response.status_code}): "
                f"{response.text[:500]}"
            )

        try:
            data = response.json()
        except ValueError as exc:
            raise RuntimeError(
                "OpenRouter API returned invalid JSON."
            ) from exc

        try:
            text = data["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise RuntimeError(
                "OpenRouter API returned no usable text response."
            ) from exc

        text = str(text).strip()

        if not text:
            raise RuntimeError(
                "OpenRouter API returned an empty response."
            )

        return {
            "status": "GENERATED",
            "provider_id": self.provider_id,
            "model_name": self.model_name,
            "response": text,
            "metrics": {
                "latency_seconds": round(latency_seconds, 4),
            },
        }
