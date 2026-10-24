"""Tests for the local smoke script's end-to-end decision gates."""
from unittest.mock import Mock

from scripts import smoke_local_model


class FakeResponse:
    def __init__(self, body, status_code=200):
        self._body = body
        self.status_code = status_code

    def raise_for_status(self):
        if self.status_code >= 400:
            raise RuntimeError("HTTP error in fake response")

    def json(self):
        return self._body


def test_main_requires_offline_backend_before_model_probe_or_chat(monkeypatch, capsys):
    monkeypatch.setattr("sys.argv", ["smoke_local_model.py"])
    monkeypatch.setattr(
        "scripts.smoke_local_model.requests.get",
        Mock(side_effect=[
            FakeResponse({"status": "ok"}),
            FakeResponse({"layers": [
                {"id": "offline_inference", "network_mode": "online"}
            ]}),
        ]),
    )
    post = Mock(side_effect=AssertionError("chat must not run outside offline mode"))
    monkeypatch.setattr("scripts.smoke_local_model.requests.post", post)

    assert smoke_local_model.main() == 1
    assert "not configured with FINAI_NETWORK_MODE=offline" in capsys.readouterr().err
    post.assert_not_called()


def test_main_success_requires_local_provider_and_generated_response(monkeypatch, capsys):
    monkeypatch.setattr("sys.argv", ["smoke_local_model.py"])
    monkeypatch.delenv("FINAI_API_BEARER_TOKEN", raising=False)
    get = Mock(side_effect=[
        FakeResponse({"status": "ok"}),
        FakeResponse({"layers": [
            {"id": "offline_inference", "network_mode": "offline"}
        ]}),
        FakeResponse({"status": "model_listed_not_inference_verified"}),
    ])
    post = Mock(return_value=FakeResponse({
        "response_generation": {
            "status": "GENERATED",
            "model_id": "colibri-local",
            "provider": "local_colibri",
            "response": "Compound interest earns interest on accumulated interest.",
        }
    }))
    monkeypatch.setattr("scripts.smoke_local_model.requests.get", get)
    monkeypatch.setattr("scripts.smoke_local_model.requests.post", post)

    assert smoke_local_model.main() == 0
    output = capsys.readouterr().out
    assert "PASS: Brain diagnostics report offline mode." in output
    assert "PASS: FinAI generated a response" in output
    assert post.call_args.args[0] == "http://127.0.0.1:8000/api/v1/chat"
    assert post.call_args.kwargs["json"]["model_id"] == "colibri-local"


def test_main_rejects_fallback_or_missing_local_model_metadata(monkeypatch, capsys):
    monkeypatch.setattr("sys.argv", ["smoke_local_model.py"])
    monkeypatch.delenv("FINAI_API_BEARER_TOKEN", raising=False)
    monkeypatch.setattr(
        "scripts.smoke_local_model.requests.get",
        Mock(side_effect=[
            FakeResponse({"status": "ok"}),
            FakeResponse({"layers": [
                {"id": "offline_inference", "network_mode": "offline"}
            ]}),
            FakeResponse({"status": "model_listed_not_inference_verified"}),
        ]),
    )
    monkeypatch.setattr(
        "scripts.smoke_local_model.requests.post",
        Mock(return_value=FakeResponse({
            "response_generation": {
                "status": "GENERATED",
                "model_id": "gemini-cloud",
                "provider": "gemini",
                "response": "A response.",
            }
        })),
    )

    assert smoke_local_model.main() == 1
    assert "does not confirm the explicit local Colibri adapter" in capsys.readouterr().err
