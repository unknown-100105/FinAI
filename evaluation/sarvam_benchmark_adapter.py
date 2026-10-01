from __future__ import annotations

from typing import Any, Dict, Optional

from llm.response_adapter import SarvamResponseAdapter


class SarvamBenchmarkAdapter:

    def __init__(
        self,
        model: Any = None,
        tokenizer: Any = None,
    ):
        self.adapter = SarvamResponseAdapter(
            model=model,
            tokenizer=tokenizer,
        )

        self.model_id = "sarvam-1"

    def generate(
        self,
        user_text: str,
        language: str,
        intent: str,
        reference_response: str,
        *,
        verified_result: Optional[Dict[str, Any]] = None,
        persona: str = "neutral",
        max_new_tokens: int = 256,
    ) -> str:

        result = self.adapter.generate(
            user_text=user_text,
            intent=intent,
            verified_result=verified_result or {},
            source="multilingual_benchmark",
            language=language,
            persona=persona,
            max_new_tokens=max_new_tokens,
        )

        response = result.get(
            "response",
            "",
        )

        if not isinstance(response, str):
            raise TypeError(
                "Sarvam benchmark response must be a string."
            )

        return response
