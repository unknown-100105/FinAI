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


def test_provider_smoke_script_runs_from_outside_repository(monkeypatch, tmp_path):
    import os
    import subprocess

    repository_root = __import__("pathlib").Path(__file__).resolve().parents[1]
    env = os.environ.copy()
    env.pop("OPENAI_API_KEY", None)
    env.pop("GEMINI_API_KEY", None)
    env.pop("OPENROUTER_API_KEY", None)
    env.pop("ANTHROPIC_API_KEY", None)
    env.pop("MISTRAL_API_KEY", None)

    result = subprocess.run(
        [
            sys.executable,
            str(repository_root / "scripts" / "smoke_llm_providers.py"),
            "--provider",
            "openai",
        ],
        cwd=tmp_path,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    report = json.loads(result.stdout)
    assert report["results"] == [
        {"provider": "openai", "status": "skipped_no_credentials"}
    ]
