"""Tests for explicit, loopback-only local model readiness probes."""
from unittest.mock import Mock

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_local_model_status_does_not_make_network_call_by_default(monkeypatch):
    monkeypatch.setenv("FINAI_COLIBRI_BASE_URL", "http://127.0.0.1:8000/v1")
    monkeypatch.setenv("FINAI_COLIBRI_MODEL", "local-finai")
    get = Mock(side_effect=AssertionError("default status must not probe"))
    monkeypatch.setattr("app.local_model_api.requests.get", get)

    response = client.get("/api/v1/system/local-model-status")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "configured_not_probed"
    assert body["configured"] is True
    assert body["probe_requested"] is False
    assert body["reachable"] is False
    get.assert_not_called()


def test_local_model_status_reports_unconfigured_without_network(monkeypatch):
    monkeypatch.delenv("FINAI_COLIBRI_BASE_URL", raising=False)
    get = Mock(side_effect=AssertionError("unconfigured status must not probe"))
    monkeypatch.setattr("app.local_model_api.requests.get", get)

    response = client.get("/api/v1/system/local-model-status?probe=true")

    assert response.status_code == 200
    assert response.json()["status"] == "unconfigured"
    get.assert_not_called()


def test_local_model_probe_matches_configured_model_id(monkeypatch):
    monkeypatch.setenv("FINAI_COLIBRI_BASE_URL", "http://127.0.0.1:8123/v1")
    monkeypatch.setenv("FINAI_COLIBRI_MODEL", "local-finai")
    monkeypatch.setenv("FINAI_COLIBRI_API_KEY", "test-only-secret")
    response = Mock(status_code=200)
    response.json.return_value = {"data": [{"id": "local-finai"}]}
    get = Mock(return_value=response)
    monkeypatch.setattr("app.local_model_api.requests.get", get)

    result = client.get("/api/v1/system/local-model-status?probe=true").json()

    assert result["status"] == "ready_for_inference"
    assert result["reachable"] is True
    assert result["model_available"] is True
    _, kwargs = get.call_args
    assert get.call_args.args[0] == "http://127.0.0.1:8123/v1/models"
    assert kwargs["headers"]["Authorization"] == "Bearer test-only-secret"
    assert kwargs["timeout"] <= 3
    assert kwargs["allow_redirects"] is False


def test_local_model_probe_does_not_claim_wrong_model_is_ready(monkeypatch):
    monkeypatch.setenv("FINAI_COLIBRI_BASE_URL", "http://127.0.0.1:8123/v1")
    monkeypatch.setenv("FINAI_COLIBRI_MODEL", "expected-model")
    response = Mock(status_code=200)
    response.json.return_value = {"data": [{"id": "different-model"}]}
    monkeypatch.setattr("app.local_model_api.requests.get", Mock(return_value=response))

    result = client.get("/api/v1/system/local-model-status?probe=true").json()

    assert result["status"] == "model_not_found"
    assert result["reachable"] is True
    assert result["model_available"] is False


def test_local_model_probe_rejects_remote_endpoint(monkeypatch):
    monkeypatch.setenv("FINAI_COLIBRI_BASE_URL", "https://remote.example/v1")
    get = Mock(side_effect=AssertionError("invalid endpoint must not be contacted"))
    monkeypatch.setattr("app.local_model_api.requests.get", get)

    result = client.get("/api/v1/system/local-model-status?probe=true").json()

    assert result["status"] == "invalid_configuration"
    assert result["configured"] is False
    get.assert_not_called()


def test_local_model_probe_handles_unreachable_server(monkeypatch):
    import requests

    monkeypatch.setenv("FINAI_COLIBRI_BASE_URL", "http://127.0.0.1:8123/v1")
    monkeypatch.setattr(
        "app.local_model_api.requests.get",
        Mock(side_effect=requests.ConnectionError("internal detail")),
    )

    result = client.get("/api/v1/system/local-model-status?probe=true").json()

    assert result["status"] == "unreachable"
    assert "internal detail" not in str(result)
