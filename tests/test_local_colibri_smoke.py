import json
import sys
from types import SimpleNamespace

from scripts import smoke_local_colibri


def test_local_colibri_smoke_skips_when_unconfigured(monkeypatch, capsys):
    monkeypatch.delenv("FINAI_COLIBRI_BASE_URL", raising=False)
    monkeypatch.setattr(smoke_local_colibri, "load_dotenv", None)
    monkeypatch.setattr(sys, "argv", ["smoke_local_colibri.py"])

    assert smoke_local_colibri.main() == 0
    report = json.loads(capsys.readouterr().out)
    assert report["status"] == "skipped_unconfigured"
    assert report["network_calls"] == 0


def test_local_colibri_smoke_can_require_configuration(monkeypatch, capsys):
    monkeypatch.delenv("FINAI_COLIBRI_BASE_URL", raising=False)
    monkeypatch.setattr(smoke_local_colibri, "load_dotenv", None)
    monkeypatch.setattr(sys, "argv", ["smoke_local_colibri.py", "--required"])

    assert smoke_local_colibri.main() == 2
    report = json.loads(capsys.readouterr().out)
    assert report["status"] == "skipped_unconfigured"


def test_local_colibri_smoke_uses_adapter_and_never_prints_response(monkeypatch, capsys):
    monkeypatch.setenv("FINAI_COLIBRI_BASE_URL", "http://127.0.0.1:9123/v1")
    monkeypatch.setenv("FINAI_COLIBRI_MODEL", "test-local-model")
    monkeypatch.setattr(smoke_local_colibri, "load_dotenv", None)
    monkeypatch.setattr(sys, "argv", ["smoke_local_colibri.py", "--timeout-seconds", "5"])

    class FakeAdapter:
        def __init__(self):
            assert smoke_local_colibri.os.environ["FINAI_COLIBRI_TIMEOUT_SECONDS"] == "5"

        def generate(self, **kwargs):
            assert kwargs["user_text"] == "Define revenue in one short sentence."
            assert kwargs["max_new_tokens"] == 48
            return {
                "status": "GENERATED",
                "response": "PRIVATE_GENERATED_SENTENCE",
                "provider": "local_colibri",
                "model_name": "test-local-model",
                "usage": {"prompt_tokens": 12, "completion_tokens": 7},
            }

    monkeypatch.setattr("llm.colibri_adapter.ColibriResponseAdapter", FakeAdapter)
    assert smoke_local_colibri.main() == 0
    output = capsys.readouterr().out
    report = json.loads(output)
    assert report["status"] == "passed"
    assert report["cloud_fallback_used"] is False
    assert report["response_text_printed"] is False
    assert "PRIVATE_GENERATED_SENTENCE" not in output
    assert report["response_characters"] == len("PRIVATE_GENERATED_SENTENCE")


def test_local_colibri_smoke_rejects_non_loopback_without_leaking_error(monkeypatch, capsys):
    monkeypatch.setenv("FINAI_COLIBRI_BASE_URL", "https://not-local.example/v1")
    monkeypatch.setattr(smoke_local_colibri, "load_dotenv", None)
    monkeypatch.setattr(sys, "argv", ["smoke_local_colibri.py"])

    assert smoke_local_colibri.main() == 1
    report = json.loads(capsys.readouterr().out)
    assert report["status"] == "failed"
    assert report["error_type"] == "ValueError"
    assert "not-local.example" not in capsys.readouterr().out
