from types import SimpleNamespace
from unittest.mock import Mock

from llm.cloud.openai_provider import OpenAIProvider


def test_openai_provider_uses_responses_api():
    client = Mock()
    client.responses.create.return_value = SimpleNamespace(
        output_text="Mutual funds pool investor money into portfolios."
    )

    provider = OpenAIProvider(
        api_key="test-key",
        model="gpt-test",
        client=client,
    )

    result = provider.generate(
        user_text="What are mutual funds?",
        intent="FINANCIAL_PRODUCT_KNOWLEDGE",
        verified_result={"source": "structured_financial_catalog"},
        source="structured_financial_catalog",
    )

    assert result["response"]
    assert result["model_name"] == "gpt-test"
    client.responses.create.assert_called_once()

    call = client.responses.create.call_args.kwargs
    assert call["model"] == "gpt-test"
    assert call["store"] is False
    assert "STRUCTURED FINAI CONTEXT" in call["input"]
    assert "Intent: FINANCIAL_PRODUCT_KNOWLEDGE" in call["instructions"]


def test_openai_provider_rejects_empty_output():
    client = Mock()
    client.responses.create.return_value = SimpleNamespace(output_text="")

    provider = OpenAIProvider(
        api_key="test-key",
        model="gpt-test",
        client=client,
    )

    try:
        provider.generate(
            user_text="Hello",
            intent="FINANCIAL_GUIDANCE",
            verified_result={},
            source="structured_financial_catalog",
        )
    except RuntimeError as exc:
        assert "empty response" in str(exc).lower()
    else:
        raise AssertionError("Expected empty-response failure")
