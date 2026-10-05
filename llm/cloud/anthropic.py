import os
import time
from typing import Any, Dict

import requests

from .base import CloudLLMProvider


class AnthropicProvider(CloudLLMProvider):
    """Anthropic Messages API provider for FinAI."""

    provider_id = "anthropic"
    endpoint = "https://api.anthropic.com/v1/messages"

    def __init__(
        self,
        api_key: str | None = None,
        model_name: str | None = None,
        timeout_seconds: float = 30.0,
        anthropic_version: str | None = None,
    ):
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY", "").strip()
        self.model_name = (
            model_name
            or os.getenv("ANTHROPIC_MODEL", "claude-sonnet-5.5").strip()
        )
        self.timeout_seconds = float(timeout_seconds)
        self.anthropic_version = (
            anthropic_version
            or os.getenv("ANTHROPIC_VERSION", "2023-06-01").strip()
        )

    @staticmethod
    def _system_instructions(intent: str, source: str, language: str, persona: str) -> str:
        return (
            "You are the reasoning and explanation layer inside FinAI, a financial "
            "intelligence platform. Answer the user's actual question directly. "
            "Never invent prices, rates, regulations, account data, transactions, "
            "or calculations. Treat supplied structured financial data and evidence "
            "as authoritative for the turn. Separate facts from assumptions. "
            "The system, not the model, is the authority for calculations and actions. "
            "Never claim a real-world action occurred unless FinAI executed it.\n\n"
            f"Intent: {intent}\nAuthority source: {source}\n"
            f"Language: {language}\nPersona: {persona}"
        )

    @staticmethod
    def _build_prompt(user_text: str, verified_result: Dict[str, Any]) -> str:
        import json

        return (
            "USER QUESTION:\n"
            f"{user_text}\n\n"
            "STRUCTURED FINAI CONTEXT:\n"
            f"{json.dumps(verified_result, ensure_ascii=False, default=str)}\n\n"
            "Return a useful user-facing answer. Do not alter verified values."
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
            raise RuntimeError("ANTHROPIC_API_KEY is not configured.")

        payload = {
            "model": self.model_name,
            "max_tokens": int(max_new_tokens),
            "system": self._system_instructions(intent, source, language, persona),
            "messages": [
                {
                    "role": "user",
                    "content": self._build_prompt(user_text, verified_result),
                }
            ],
        }
        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": self.anthropic_version,
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
                "Anthropic API request failed "
                f"({response.status_code}): {response.text[:500]}"
            )

        try:
            data = response.json()
        except ValueError as exc:
            raise RuntimeError("Anthropic API returned invalid JSON.") from exc

        try:
            blocks = data["content"]
            text_parts = [
                str(block.get("text", ""))
                for block in blocks
                if isinstance(block, dict) and block.get("type") == "text"
            ]
            text = "".join(text_parts).strip()
        except (KeyError, TypeError) as exc:
            raise RuntimeError("Anthropic API returned no usable text response.") from exc

        if not text:
            raise RuntimeError("Anthropic API returned an empty response.")

        return {
            "status": "GENERATED",
            "provider_id": self.provider_id,
            "model_name": self.model_name,
            "response": text,
            "metrics": {"latency_seconds": round(latency_seconds, 4)},
        }
