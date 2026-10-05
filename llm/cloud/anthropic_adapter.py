from typing import Any, Dict

from llm.cloud.anthropic import AnthropicProvider


class AnthropicResponseAdapter:
    """ModelGateway adapter for Anthropic."""

    def __init__(self, provider: AnthropicProvider | None = None):
        self.provider = provider or AnthropicProvider()

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
