from unittest.mock import Mock, patch

import pytest

from llm.cloud.anthropic import AnthropicProvider


def _response(status_code=200, payload=None):
    response = Mock()
    response.status_code = status_code
    response.text = "error"
    response.json.return_value = payload or {
        "content": [{"type": "text", "text": "Anthropic response"}]
    }
    return response


def test_missing_key_fails_before_http():
    provider = AnthropicProvider(api_key="")
    with patch("llm.cloud.anthropic.requests.post") as post:
        with pytest.raises(RuntimeError, match="ANTHROPIC_API_KEY"):
            provider.generate("Explain SIP", "FINANCIAL_PRODUCT_KNOWLEDGE", {}, "catalog")
        post.assert_not_called()


@patch("llm.cloud.anthropic.requests.post")
def test_success_parses_message_content(post):
    post.return_value = _response()
    provider = AnthropicProvider(api_key="test-key", model_name="claude-sonnet-5-5")

    result = provider.generate(
        "Explain SIP",
        "FINANCIAL_PRODUCT_KNOWLEDGE",
        {"topic": "SIP"},
        "catalog",
    )

    assert result["provider_id"] == "anthropic"
    assert result["model_name"] == "claude-sonnet-5-5"
    assert result["response"] == "Anthropic response"
    assert "latency_seconds" in result["metrics"]


@patch("llm.cloud.anthropic.requests.post")
def test_request_headers_and_payload(post):
    post.return_value = _response()
    provider = AnthropicProvider(api_key="secret", model_name="claude-test")

    provider.generate("Explain SIP", "FINANCIAL_PRODUCT_KNOWLEDGE", {}, "catalog")

    args, kwargs = post.call_args
    assert args[0] == "https://api.anthropic.com/v1/messages"
    assert kwargs["headers"]["x-api-key"] == "secret"
    assert kwargs["headers"]["anthropic-version"] == "2023-06-01"
    assert kwargs["json"]["model"] == "claude-test"
    assert kwargs["json"]["messages"][0]["role"] == "user"


@patch("llm.cloud.anthropic.requests.post")
def test_http_error_is_reported(post):
    post.return_value = _response(status_code=429)
    provider = AnthropicProvider(api_key="test-key")

    with pytest.raises(RuntimeError, match="Anthropic API request failed"):
        provider.generate("Explain SIP", "FINANCIAL_PRODUCT_KNOWLEDGE", {}, "catalog")
