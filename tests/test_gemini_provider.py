from unittest.mock import Mock, patch

import pytest

from llm.cloud.gemini import GeminiProvider


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
            "candidates": [
                {
                    "content": {
                        "parts": [
                            {
                                "text": "Your monthly EMI is ₹8,678.23."
                            }
                        ]
                    }
                }
            ]
        }

    response.json.return_value = payload
    return response


def test_gemini_provider_initializes():
    provider = GeminiProvider(
        api_key="test-key",
        model_name="gemini-3.8-flash",
    )

    assert provider.provider_id == "gemini"
    assert provider.model_name == "gemini-3.8-flash"
    assert provider.api_key == "test-key"


def test_missing_api_key_fails_before_http_request():
    provider = GeminiProvider(
        api_key="",
        model_name="gemini-3.8-flash",
    )

    with patch("llm.cloud.gemini.requests.post") as post:
        with pytest.raises(RuntimeError, match="GEMINI_API_KEY"):
            provider.generate(
                user_text="What is KYC?",
                intent="KYC_DOCUMENTS",
                verified_result={},
                source="retrieval_evidence",
            )

        post.assert_not_called()


@patch("llm.cloud.gemini.requests.post")
def test_generate_parses_success_response(post):
    post.return_value = make_response()

    provider = GeminiProvider(
        api_key="test-key",
        model_name="gemini-3.8-flash",
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
    assert result["provider_id"] == "gemini"
    assert result["model_name"] == "gemini-3.8-flash"
    assert result["response"] == "Your monthly EMI is ₹8,678.23."
    assert "latency_seconds" in result["metrics"]

    post.assert_called_once()


@patch("llm.cloud.gemini.requests.post")
def test_generate_sends_expected_request(post):
    post.return_value = make_response()

    provider = GeminiProvider(
        api_key="test-key",
        model_name="gemini-3.8-flash",
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

    url = args[0]
    headers = kwargs["headers"]
    payload = kwargs["json"]

    assert url == (
        "https://generativelanguage.googleapis.com/v1beta/"
        "models/gemini-3.8-flash:generateContent"
    )

    assert headers["x-goog-api-key"] == "test-key"
    assert headers["Content-Type"] == "application/json"

    assert payload["generationConfig"]["maxOutputTokens"] == 256
    assert (
        payload["generationConfig"]["thinkingConfig"]["thinkingLevel"]
        == "low"
    )

    assert "temperature" not in payload["generationConfig"]
    assert "top_p" not in payload["generationConfig"]
    assert "top_k" not in payload["generationConfig"]

    prompt = payload["contents"][0]["parts"][0]["text"]

    assert "Calculate my EMI" in prompt
    assert "EMI_QUERY" in prompt
    assert "8678.23" in prompt
    assert "2082775.76" in prompt
    assert "1082775.76" in prompt


@patch("llm.cloud.gemini.requests.post")
def test_http_error_is_reported(post):
    post.return_value = make_response(
        status_code=429,
    )

    provider = GeminiProvider(
        api_key="test-key",
        model_name="gemini-3.8-flash",
    )

    with pytest.raises(
        RuntimeError,
        match="Gemini API request failed",
    ):
        provider.generate(
            user_text="What is KYC?",
            intent="KYC_DOCUMENTS",
            verified_result={},
            source="retrieval_evidence",
        )


@patch("llm.cloud.gemini.requests.post")
def test_malformed_response_is_rejected(post):
    post.return_value = make_response(
        payload={
            "candidates": []
        }
    )

    provider = GeminiProvider(
        api_key="test-key",
        model_name="gemini-3.8-flash",
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


@patch("llm.cloud.gemini.requests.post")
def test_empty_text_response_is_rejected(post):
    post.return_value = make_response(
        payload={
            "candidates": [
                {
                    "content": {
                        "parts": [
                            {
                                "text": "   ",
                            }
                        ]
                    }
                }
            ]
        }
    )

    provider = GeminiProvider(
        api_key="test-key",
        model_name="gemini-3.8-flash",
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
