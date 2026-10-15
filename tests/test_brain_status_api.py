"""Safe local-readiness diagnostics for the FinAI Brain endpoint."""

import json

from fastapi.testclient import TestClient

from app import system_api
from app.main import app

client = TestClient(app)


def test_brain_status_reports_missing_assets_without_network_calls(tmp_path, monkeypatch):
    monkeypatch.setattr(system_api, "ROOT", tmp_path)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("MISTRAL_API_KEY", raising=False)
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    monkeypatch.delenv("SARVAM_API_KEY", raising=False)

    response = client.get("/api/v1/system/brain-status")
    assert response.status_code == 200
    payload = response.json()
    layers = {item["id"]: item for item in payload["layers"]}

    assert "market_data" in layers
    assert "structured_knowledge" in layers
    assert layers["market_data"]["provider_reachability_verified"] is False
    assert payload["schema_version"] == "1.0"
    assert payload["status"] == "diagnostic"
    assert payload["live_checks_performed"] is False
    assert layers["retrieval"]["status"] == "assets_missing"
    assert len(layers["retrieval"]["missing_assets"]) == 3
    assert layers["model_generation"]["status"] == "no_cloud_credentials_detected"
    assert layers["model_generation"]["provider_reachability_verified"] is False


def test_brain_status_never_exposes_provider_secrets_and_detects_local_assets(tmp_path, monkeypatch):
    monkeypatch.setattr(system_api, "ROOT", tmp_path)
    for key in (
        "OPENAI_API_KEY", "OPENROUTER_API_KEY", "ANTHROPIC_API_KEY",
        "MISTRAL_API_KEY", "GEMINI_API_KEY", "GOOGLE_API_KEY", "SARVAM_API_KEY",
    ):
        monkeypatch.delenv(key, raising=False)
    secret = "test-provider-secret-never-serialize"
    monkeypatch.setenv("OPENROUTER_API_KEY", secret)

    for relative in system_api.RAG_ASSETS:
        path = tmp_path / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b"test-only-placeholder")

    response = client.get("/api/v1/system/brain-status")
    assert response.status_code == 200
    payload = response.json()
    layers = {item["id"]: item for item in payload["layers"]}

    assert layers["retrieval"]["status"] == "ready_local_assets"
    assert layers["model_generation"]["configured_provider_names"] == ["openrouter"]
    assert layers["model_generation"]["model_inference_verified"] is False
    assert secret not in json.dumps(payload)


def test_brain_status_separates_offline_configuration_from_runtime_verification(tmp_path, monkeypatch):
    monkeypatch.setattr(system_api, "ROOT", tmp_path)
    monkeypatch.setenv("FINAI_NETWORK_MODE", "offline")
    monkeypatch.setenv("FINAI_COLIBRI_BASE_URL", "http://127.0.0.1:8000/v1")

    for relative in ("llm/rllm_finqa_adapter.py", "llm/colibri_adapter.py"):
        path = tmp_path / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("# test placeholder", encoding="utf-8")

    response = client.get("/api/v1/system/brain-status")
    assert response.status_code == 200
    layers = {item["id"]: item for item in response.json()["layers"]}
    offline = layers["offline_inference"]

    assert offline["status"] == "offline_mode_requested"
    assert offline["network_mode"] == "offline"
    assert offline["colibri_configured"] is True
    assert offline["local_runtime_verified"] is False
    assert offline["model_weights_presence_verified"] is False
    assert offline["colibri_server_reachability_verified"] is False


def test_unregistered_key_aliases_do_not_claim_provider_configured(tmp_path, monkeypatch):
    monkeypatch.setattr(system_api, "ROOT", tmp_path)
    for key in (
        "OPENAI_API_KEY", "OPENROUTER_API_KEY", "ANTHROPIC_API_KEY",
        "MISTRAL_API_KEY", "GEMINI_API_KEY", "SARVAM_API_KEY",
    ):
        monkeypatch.delenv(key, raising=False)
    monkeypatch.setenv("GOOGLE_API_KEY", "not-used-by-the-configured-gemini-adapter")
    monkeypatch.setenv("SARVAM_API_KEY", "sarvam-is-not-registered-in-production-gateway")

    response = client.get("/api/v1/system/brain-status")
    assert response.status_code == 200
    layers = {item["id"]: item for item in response.json()["layers"]}
    assert layers["model_generation"]["configured_provider_names"] == []
