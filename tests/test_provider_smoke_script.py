import json
import sys

from scripts import smoke_llm_providers


def test_provider_smoke_defaults_to_no_network_calls(monkeypatch, capsys):
    monkeypatch.setenv("OPENAI_API_KEY", "synthetic-test-key")
    monkeypatch.setattr(
        sys,
        "argv",
        ["smoke_llm_providers.py", "--provider", "openai"],
    )

    assert smoke_llm_providers.main() == 0

    report = json.loads(capsys.readouterr().out)
    assert report["mode"] == "configuration_only"
    assert report["attempted_live_requests"] == 0
    assert report["results"] == [
        {"provider": "openai", "status": "configured_not_called"}
    ]


def test_provider_smoke_respects_offline_mode(monkeypatch, capsys):
    monkeypatch.setenv("OPENAI_API_KEY", "synthetic-test-key")
    monkeypatch.setenv("FINAI_NETWORK_MODE", "offline")
    monkeypatch.setenv("FINAI_DATA_SENSITIVITY", "standard")
    monkeypatch.setattr(
        sys,
        "argv",
        ["smoke_llm_providers.py", "--live", "--provider", "openai"],
    )

    assert smoke_llm_providers.main() == 0

    report = json.loads(capsys.readouterr().out)
    assert report["mode"] == "live"
    assert report["attempted_live_requests"] == 0
    assert report["results"] == [
        {"provider": "openai", "status": "blocked_offline_mode"}
    ]
