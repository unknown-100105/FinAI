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

    assert payload["schema_version"] == "1.0"
    assert payload["status"] == "diagnostic"
    assert payload["live_checks_performed"] is False
    assert layers["retrieval"]["status"] == "assets_missing"
    assert len(layers["retrieval"]["missing_assets"]) == 3
    assert layers["model_generation"]["status"] == "no_cloud_credentials_detected"
    assert layers["model_generation"]["provider_reachability_verified"] is False


def test_brain_status_never_exposes_provider_secrets_and_detects_local_assets(tmp_path, monkeypatch):
    monkeypatch.setattr(system_api, "ROOT", tmp_path)
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
