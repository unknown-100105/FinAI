from __future__ import annotations

from scripts.smoke_llm_providers import load_project_env


def test_provider_smoke_loads_project_env_without_overriding_shell_values(tmp_path, monkeypatch):
    (tmp_path / ".env").write_text(
        "OPENAI_API_KEY=local-test-key\nGEMINI_API_KEY=local-gemini-key\n",
        encoding="utf-8",
    )
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.setenv("GEMINI_API_KEY", "shell-gemini-key")

    assert load_project_env(tmp_path) is True

    assert __import__("os").environ["OPENAI_API_KEY"] == "local-test-key"
    assert __import__("os").environ["GEMINI_API_KEY"] == "shell-gemini-key"
