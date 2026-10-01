from abc import ABC, abstractmethod
from typing import Any, Dict


class CloudLLMProvider(ABC):
    """Common interface implemented by all FinAI cloud LLM providers."""

    provider_id: str = "unknown"
    model_name: str = "unknown"

    @abstractmethod
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
        """Generate a response using the provider."""
        raise NotImplementedError
