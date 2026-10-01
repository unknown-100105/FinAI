from unittest.mock import Mock

from llm.cloud.gemini_adapter import GeminiResponseAdapter


def test_gemini_adapter_delegates_to_provider():
    provider = Mock()
    provider.generate.return_value = {
        "status": "GENERATED",
        "provider_id": "gemini",
        "model_name": "gemini-3.8-flash",
        "response": "Test response",
    }

    adapter = GeminiResponseAdapter(provider=provider)

    result = adapter.generate(
        user_text="What is an EMI?",
        intent="EMI_QUERY",
        verified_result={"monthly_emi": 1000},
        source="deterministic_finance_engine",
    )

    provider.generate.assert_called_once()
    assert result["response"] == "Test response"
    assert result["provider_id"] == "gemini"
