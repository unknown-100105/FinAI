import requests
import pytest

from llm.ollama_adapter import OllamaResponseAdapter


class FakeResponse:
    def __init__(self, status_code=200, payload=None, text=""):
        self.status_code = status_code
        self._payload = payload
        self.text = text

    def json(self):
        if isinstance(self._payload, Exception):
            raise self._payload
        return self._payload


def _generate(adapter):
    return adapter.generate(
        user_text="Explain this verified result",
        intent="FINANCIAL_GUIDANCE",
        verified_result={"status": "verified", "value": 12},
        source="test",
        language="English",
        persona="neutral",
    )


def test_ollama_adapter_sends_chat_request_and_normalizes_response(monkeypatch):
    calls = {}

    def fake_post(url, **kwargs):
        calls["url"] = url
        calls["kwargs"] = kwargs
        return FakeResponse(payload={"message": {"content": "Verified explanation."}})

    monkeypatch.setattr("llm.ollama_adapter.requests.post", fake_post)
    result = _generate(OllamaResponseAdapter(model_name="qwen3:4b"))

    assert calls["url"] == "http://127.0.0.1:11434/api/chat"
    assert calls["kwargs"]["json"]["model"] == "qwen3:4b"
    assert calls["kwargs"]["json"]["stream"] is False
    assert result["provider_id"] == "ollama"
    assert result["response"] == "Verified explanation."


def test_ollama_adapter_translates_connection_errors(monkeypatch):
    def fake_post(*args, **kwargs):
        raise requests.ConnectionError("offline")

    monkeypatch.setattr("llm.ollama_adapter.requests.post", fake_post)
    with pytest.raises(RuntimeError, match="Ollama request failed"):
        _generate(OllamaResponseAdapter())


def test_ollama_adapter_rejects_http_errors(monkeypatch):
    monkeypatch.setattr(
        "llm.ollama_adapter.requests.post",
        lambda *args, **kwargs: FakeResponse(503, text="service unavailable"),
    )
    with pytest.raises(RuntimeError, match="503"):
        _generate(OllamaResponseAdapter())


def test_ollama_adapter_rejects_empty_payload(monkeypatch):
    monkeypatch.setattr(
        "llm.ollama_adapter.requests.post",
        lambda *args, **kwargs: FakeResponse(payload={"message": {"content": " "}}),
    )
    with pytest.raises(RuntimeError, match="empty response"):
        _generate(OllamaResponseAdapter())


def test_ollama_adapter_validates_url():
    with pytest.raises(ValueError, match="http"):
        OllamaResponseAdapter(base_url="localhost:11434")
