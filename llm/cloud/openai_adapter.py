from typing import Any, Dict, Optional

from llm.cloud.openai_provider import OpenAIProvider


class OpenAIResponseAdapter:
    """ModelGateway adapter for the OpenAI Responses API provider."""

    def __init__(
        self,
        provider: Optional[OpenAIProvider] = None,
    ):
        self.provider = provider or OpenAIProvider()

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
        return self.provider.generate(
            user_text=user_text,
            intent=intent,
            verified_result=verified_result,
            source=source,
            language=language,
            persona=persona,
            max_new_tokens=max_new_tokens,
        )
