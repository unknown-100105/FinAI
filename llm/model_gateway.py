from typing import Any, Dict, Optional


class ModelGateway:

    def __init__(
        self,
        default_model: str = "sarvam-1",
    ):
        self.default_model = default_model
        self._adapters: Dict[str, Any] = {}
        self._capabilities: Dict[str, list] = {}

    def register(
        self,
        model_id: str,
        adapter: Any,
        capabilities: Optional[list] = None,
    ) -> None:

        model_id = str(model_id).strip().lower()

        if not model_id:
            raise ValueError("model_id cannot be empty.")

        if adapter is None:
            raise ValueError(
                f"Adapter for '{model_id}' cannot be None."
            )

        if not hasattr(adapter, "generate"):
            raise TypeError(
                f"Adapter '{model_id}' must provide a "
                "'generate(...)' method."
            )

        self._adapters[model_id] = adapter
        self._capabilities[model_id] = list(
            capabilities or []
        )

    def unregister(self, model_id: str) -> None:

        model_id = str(model_id).strip().lower()

        self._adapters.pop(model_id, None)
        self._capabilities.pop(model_id, None)

    def available_models(self) -> list:

        return sorted(self._adapters.keys())

    def get_adapter(
        self,
        model_id: Optional[str] = None,
    ) -> Any:

        selected = (
            str(model_id).strip().lower()
            if model_id is not None
            else self.default_model
        )

        if selected not in self._adapters:

            available = ", ".join(
                self.available_models()
            )

            raise ValueError(
                f"Model '{selected}' is not registered. "
                f"Available models: {available or 'none'}"
            )

        return self._adapters[selected]

    def capabilities(
        self,
        model_id: str,
    ) -> list:

        model_id = str(model_id).strip().lower()

        if model_id not in self._adapters:
            raise ValueError(
                f"Model '{model_id}' is not registered."
            )

        return list(
            self._capabilities.get(model_id, [])
        )

    def set_default(
        self,
        model_id: str,
    ) -> None:

        model_id = str(model_id).strip().lower()

        if model_id not in self._adapters:
            raise ValueError(
                f"Cannot set default model '{model_id}'. "
                "Register it first."
            )

        self.default_model = model_id

    def generate(
        self,
        user_text: str,
        intent: str,
        verified_result: Dict[str, Any],
        source: str,
        language: str = "English",
        persona: str = "neutral",
        model_id: Optional[str] = None,
        max_new_tokens: int = 160,
    ) -> Dict[str, Any]:

        selected_model = (
            str(model_id).strip().lower()
            if model_id is not None
            else self.default_model
        )

        adapter = self.get_adapter(
            selected_model
        )

        result = adapter.generate(
            user_text=user_text,
            intent=intent,
            verified_result=verified_result,
            source=source,
            language=language,
            persona=persona,
            max_new_tokens=max_new_tokens,
        )

        if not isinstance(result, dict):
            raise TypeError(
                f"Adapter '{selected_model}' returned "
                f"{type(result).__name__}; expected dict."
            )

        # Gateway-owned metadata.
        result["model_id"] = selected_model

        return result


if __name__ == "__main__":

    from .response_adapter import SarvamResponseAdapter
    from .rllm_finqa_adapter import RLLMFinQAModelAdapter

    gateway = ModelGateway()

    gateway.register(
        model_id="sarvam-1",
        adapter=SarvamResponseAdapter(),
        capabilities=[
            "response_generation",
            "financial_explanation",
            "persona_control",
        ],
    )

    gateway.register(
        model_id="rllm-finqa-4b",
        adapter=RLLMFinQAModelAdapter(),
        capabilities=[
            "financial_qa",
            "financial_reasoning",
            "financial_explanation",
        ],
    )

    verified = {
        "principal": 1_000_000,
        "annual_rate": 8.5,
        "tenure_months": 240,
        "monthly_emi": 8678.23,
        "total_payment": 2082775.76,
        "total_interest": 1082775.76,
    }

    result = gateway.generate(
        user_text=(
            "Calculate EMI for ₹10 lakh at "
            "8.5% for 20 years"
        ),
        intent="EMI_QUERY",
        verified_result=verified,
        source="deterministic_finance_engine",
        language="English",
        persona="neutral",
    )

    print("=" * 80)
    print("FINAI MODEL GATEWAY TEST")
    print("=" * 80)
    print("AVAILABLE MODELS:", gateway.available_models())
    print("DEFAULT MODEL:", gateway.default_model)
    print("MODEL USED:", result["model_id"])
    print("STATUS:", result["status"])
    print("VERIFICATION:", result["verification"])
    print("RESPONSE:", result["response"])
