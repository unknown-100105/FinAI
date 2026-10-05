from unittest.mock import Mock, patch

import pytest

from llm.cloud.mistral import MistralProvider


def _response(status_code=200, payload=None):
    response = Mock()
    response.status_code = status_code
    response.text = "error"
    response.json.return_value = payload or {
        "choices": [{"message": {"content": "Mistral response"}}]
    }
    return response


def test_missing_key_fails_before_http():
    provider = MistralProvider(api_key="")
    with patch("llm.cloud.mistral.requests.post") as post:
        with pytest.raises(RuntimeError, match="MISTRAL_API_KEY"):
            provider.generate("Explain SIP", "FINANCIAL_PRODUCT_KNOWLEDGE", {}, "catalog")
        post.assert_not_called()


@patch("llm.cloud.mistral.requests.post")
def test_success_parses_message_content(post):
    post.return_value = _response()
    provider = MistralProvider(api_key="test-key", model_name="mistral-large-latest")

    result = provider.generate(
        "Explain SIP",
        "FINANCIAL_PRODUCT_KNOWLEDGE",
        {"topic": "SIP"},
        "catalog",
    )

    assert result["provider_id"] == "mistral"
    assert result["model_name"] == "mistral-large-latest"
    assert result["response"] == "Mistral response"
    assert "latency_seconds" in result["metrics"]


@patch("llm.cloud.mistral.requests.post")
def test_request_headers_and_payload(post):
    post.return_value = _response()
    provider = MistralProvider(api_key="secret", model_name="mistral-test")

    provider.generate("Explain SIP", "FINANCIAL_PRODUCT_KNOWLEDGE", {}, "catalog")

    args, kwargs = post.call_args
    assert args[0] == "https://api.mistral.ai/v1/chat/completions"
    assert kwargs["headers"]["Authorization"] == "Bearer secret"
    assert kwargs["json"]["model"] == "mistral-test"
    assert kwargs["json"]["messages"][0]["role"] == "system"


@patch("llm.cloud.mistral.requests.post")
def test_http_error_is_reported(post):
    post.return_value = _response(status_code=429)
    provider = MistralProvider(api_key="test-key")

    with pytest.raises(RuntimeError, match="Mistral API request failed"):
        provider.generate("Explain SIP", "FINANCIAL_PRODUCT_KNOWLEDGE", {}, "catalog")
