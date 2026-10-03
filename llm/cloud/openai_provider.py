import os
from typing import Any, Dict, Optional


class OpenAIProvider:
    """OpenAI Responses API provider for FinAI reasoning and explanation."""

    provider_id = "openai"

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        client: Any = None,
    ):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.model = (
            model
            or os.getenv("OPENAI_MODEL")
            or "gpt-6-luna"
        )
        self.client = client

        if self.client is None:
            if not self.api_key:
                raise RuntimeError(
                    "OPENAI_API_KEY is not configured."
                )

            try:
                from openai import OpenAI
            except ImportError as exc:
                raise RuntimeError(
                    "The OpenAI Python SDK is not installed. "
                    "Install it with 'pip install openai'."
                ) from exc

            self.client = OpenAI(api_key=self.api_key)

    @staticmethod
    def _system_instructions(
        intent: str,
        source: str,
        language: str,
        persona: str,
    ) -> str:
        return (
            "You are the reasoning and explanation layer inside FinAI, "
            "a financial intelligence platform.\n\n"
            "Answer the user's actual question directly and clearly.\n"
            "Do not invent prices, rates, regulations, eligibility, "
            "account data, transactions, or calculations.\n"
            "When structured financial data or retrieved evidence is "
            "provided, treat it as authoritative for that turn.\n"
            "Separate facts from assumptions and projections.\n"
            "For calculations, use the supplied verified values rather "
            "than recomputing them from memory.\n"
            "For current or time-sensitive information, say when the "
            "available source may be stale and identify what should be "
            "checked.\n"
            "Never claim that a trade, payment, transfer, application, "
            "or other real-world action was executed unless FinAI "
            "actually executed an authorized tool operation.\n\n"
            f"Intent: {intent}\n"
            f"Authority source: {source}\n"
            f"Language: {language}\n"
            f"Persona: {persona}\n"
        )

    @staticmethod
    def _build_input(
        user_text: str,
        verified_result: Dict[str, Any],
    ) -> str:
        import json

        return (
            "USER QUESTION:\n"
            f"{user_text}\n\n"
            "STRUCTURED FINAI CONTEXT:\n"
            f"{json.dumps(verified_result, ensure_ascii=False, default=str)}\n\n"
            "Return a useful answer for the user. Prefer concise "
            "headings or bullets when they improve readability."
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
        if not self.client:
            raise RuntimeError("OpenAI client is not initialized.")

        response = self.client.responses.create(
            model=self.model,
            instructions=self._system_instructions(
                intent=intent,
                source=source,
                language=language,
                persona=persona,
            ),
            input=self._build_input(
                user_text=user_text,
                verified_result=verified_result,
            ),
            max_output_tokens=max_new_tokens,
            store=False,
        )

        text = str(
            getattr(response, "output_text", "") or ""
        ).strip()

        if not text:
            raise RuntimeError(
                "OpenAI returned an empty response."
            )

        return {
            "status": "GENERATED",
            "source": source,
            "language": language,
            "persona": persona,
            "response": text,
            "provider": self.provider_id,
            "model_name": self.model,
            "generation_complete": True,
            "truncated": False,
            "finish_reason": "stop",
        }
