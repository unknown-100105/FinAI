from unittest.mock import Mock, patch

import pytest

from llm.cloud.openrouter import OpenRouterProvider


VERIFIED = {
    "monthly_emi": 8678.23,
    "total_payment": 2082775.76,
    "total_interest": 1082775.76,
}


def make_response(status_code=200, payload=None):
    response = Mock()
    response.status_code = status_code
    response.text = "error text"

    if payload is None:
        payload = {
            "choices": [
                {
                    "message": {
                        "content": "Your monthly EMI is ?8,678.23."
                    }
                }
            ]
        }

    response.json.return_value = payload
    return response


def test_openrouter_provider_initializes():
    provider = OpenRouterProvider(
        api_key="test-key",
        model_name="openai/gpt-5",
    )

    assert provider.provider_id == "openrouter"
    assert provider.model_name == "openai/gpt-5"
    assert provider.api_key == "test-key"


def test_missing_api_key_fails_before_http_request():
    provider = OpenRouterProvider(
        api_key="",
        model_name="openai/gpt-5",
    )

    with patch("llm.cloud.openrouter.requests.post") as post:
        with pytest.raises(
            RuntimeError,
            match="OPENROUTER_API_KEY",
        ):
            provider.generate(
                user_text="What is KYC?",
                intent="KYC_DOCUMENTS",
                verified_result={},
                source="retrieval_evidence",
            )

        post.assert_not_called()


@patch("llm.cloud.openrouter.requests.post")
def test_generate_parses_success_response(post):
    post.return_value = make_response()

    provider = OpenRouterProvider(
        api_key="test-key",
        model_name="openai/gpt-5",
    )

    result = provider.generate(
        user_text="Calculate my EMI",
        intent="EMI_QUERY",
        verified_result=VERIFIED,
        source="deterministic_finance_engine",
        language="English",
        persona="neutral",
        max_new_tokens=160,
    )

    assert result["status"] == "GENERATED"
    assert result["provider_id"] == "openrouter"
    assert result["model_name"] == "openai/gpt-5"
    assert result["response"] == "Your monthly EMI is ?8,678.23."
    assert "latency_seconds" in result["metrics"]

    post.assert_called_once()


@patch("llm.cloud.openrouter.requests.post")
def test_generate_sends_expected_request(post):
    post.return_value = make_response()

    provider = OpenRouterProvider(
        api_key="test-key",
        model_name="openai/gpt-5",
        http_referer="https://finai.example",
        x_title="FinAI Test",
    )

    provider.generate(
        user_text="Calculate my EMI",
        intent="EMI_QUERY",
        verified_result=VERIFIED,
        source="deterministic_finance_engine",
        language="English",
        persona="neutral",
        max_new_tokens=256,
    )

    args, kwargs = post.call_args

    assert args[0] == (
        "https://openrouter.ai/api/v1/chat/completions"
    )

    headers = kwargs["headers"]
    payload = kwargs["json"]

    assert headers["Authorization"] == "Bearer test-key"
    assert headers["Content-Type"] == "application/json"
    assert headers["HTTP-Referer"] == "https://finai.example"
    assert headers["X-Title"] == "FinAI Test"

    assert payload["model"] == "openai/gpt-5"
    assert payload["max_tokens"] == 256

    prompt = payload["messages"][0]["content"]

    assert "Calculate my EMI" in prompt
    assert "EMI_QUERY" in prompt
    assert "8678.23" in prompt
    assert "2082775.76" in prompt
    assert "1082775.76" in prompt


@patch("llm.cloud.openrouter.requests.post")
def test_http_error_is_reported(post):
    post.return_value = make_response(status_code=429)

    provider = OpenRouterProvider(
        api_key="test-key",
        model_name="openai/gpt-5",
    )

    with pytest.raises(
        RuntimeError,
        match="OpenRouter API request failed",
    ):
        provider.generate(
            user_text="What is KYC?",
            intent="KYC_DOCUMENTS",
            verified_result={},
            source="retrieval_evidence",
        )


@patch("llm.cloud.openrouter.requests.post")
def test_invalid_json_is_rejected(post):
    response = make_response()
    response.json.side_effect = ValueError("bad json")
    post.return_value = response

    provider = OpenRouterProvider(
        api_key="test-key",
        model_name="openai/gpt-5",
    )

    with pytest.raises(
        RuntimeError,
        match="invalid JSON",
    ):
        provider.generate(
            user_text="What is KYC?",
            intent="KYC_DOCUMENTS",
            verified_result={},
            source="retrieval_evidence",
        )


@patch("llm.cloud.openrouter.requests.post")
def test_malformed_response_is_rejected(post):
    post.return_value = make_response(
        payload={"choices": []}
    )

    provider = OpenRouterProvider(
        api_key="test-key",
        model_name="openai/gpt-5",
    )

    with pytest.raises(
        RuntimeError,
        match="no usable text response",
    ):
        provider.generate(
            user_text="What is KYC?",
            intent="KYC_DOCUMENTS",
            verified_result={},
            source="retrieval_evidence",
        )


@patch("llm.cloud.openrouter.requests.post")
def test_empty_text_response_is_rejected(post):
    post.return_value = make_response(
        payload={
            "choices": [
                {
                    "message": {
                        "content": "   "
                    }
                }
            ]
        }
    )

    provider = OpenRouterProvider(
        api_key="test-key",
        model_name="openai/gpt-5",
    )

    with pytest.raises(
        RuntimeError,
        match="empty response",
    ):
        provider.generate(
            user_text="What is KYC?",
            intent="KYC_DOCUMENTS",
            verified_result={},
            source="retrieval_evidence",
        )
