import os
import time
from typing import Any, Dict

import requests

from .base import CloudLLMProvider
from policy.network_mode import assert_cloud_provider_allowed


class MistralProvider(CloudLLMProvider):
    """Mistral Chat Completions provider for FinAI."""

    provider_id = "mistral"
    endpoint = "https://api.mistral.ai/v1/chat/completions"

    def __init__(
        self,
        api_key: str | None = None,
        model_name: str | None = None,
        timeout_seconds: float = 30.0,
    ):
        self.api_key = api_key or os.getenv("MISTRAL_API_KEY", "").strip()
        self.model_name = (
            model_name
            or os.getenv("MISTRAL_MODEL", "mistral-large-latest").strip()
        )
        self.timeout_seconds = float(timeout_seconds)

    @staticmethod
    def _system_prompt(intent: str, source: str, language: str, persona: str) -> str:
        return (
            "You are the reasoning and explanation layer inside FinAI. "
            "Answer directly and clearly. Never invent financial values, regulations, "
            "account data, transactions, or calculations. Treat supplied verified "
            "results and evidence as authoritative. The system, not the LLM, is the "
            "authority for calculations and real-world actions.\n\n"
            f"Intent: {intent}\nAuthority source: {source}\n"
            f"Language: {language}\nPersona: {persona}"
        )

    @staticmethod
    def _user_prompt(user_text: str, verified_result: Dict[str, Any]) -> str:
        import json

        return (
            "USER QUESTION:\n"
            f"{user_text}\n\n"
            "STRUCTURED FINAI CONTEXT:\n"
            f"{json.dumps(verified_result, ensure_ascii=False, default=str)}\n\n"
            "Return only the final user-facing answer."
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
            raise RuntimeError("MISTRAL_API_KEY is not configured.")

        assert_cloud_provider_allowed("mistral")

        payload = {
            "model": self.model_name,
            "messages": [
                {
                    "role": "system",
                    "content": self._system_prompt(intent, source, language, persona),
                },
                {
                    "role": "user",
                    "content": self._user_prompt(user_text, verified_result),
                },
            ],
            "max_tokens": int(max_new_tokens),
        }
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

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
                "Mistral API request failed "
                f"({response.status_code}): {response.text[:500]}"
            )

        try:
            data = response.json()
        except ValueError as exc:
            raise RuntimeError("Mistral API returned invalid JSON.") from exc

        try:
            content = data["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise RuntimeError("Mistral API returned no usable text response.") from exc

        if isinstance(content, list):
            content = "".join(
                str(item.get("text", ""))
                for item in content
                if isinstance(item, dict) and item.get("type") == "text"
            )

        text = str(content).strip()
        if not text:
            raise RuntimeError("Mistral API returned an empty response.")

        return {
            "status": "GENERATED",
            "provider_id": self.provider_id,
            "model_name": self.model_name,
            "response": text,
            "metrics": {"latency_seconds": round(latency_seconds, 4)},
        }
