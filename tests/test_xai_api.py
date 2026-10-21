from fastapi.testclient import TestClient

import app.xai_api as xai_api_module
from app.xai_api import app


client = TestClient(app)
TRACE_TOKEN = "test-only-token-with-at-least-32-characters"


def configure_trace_access(monkeypatch):
    monkeypatch.setenv("FINAI_ENV", "development")
    monkeypatch.setenv("FINAI_API_AUTH_MODE", "bearer")
    monkeypatch.setenv("FINAI_API_BEARER_TOKEN", TRACE_TOKEN)
    monkeypatch.setenv("FINAI_ENABLE_XAI_TRACE_API", "true")
    monkeypatch.setenv("FINAI_ENABLE_XAI_TRACE_DETAILS", "true")
    return {"Authorization": f"Bearer {TRACE_TOKEN}"}


def test_health():
    response = client.get("/health")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["service"] == "finai-xai-api"


def test_trace_api_is_disabled_without_explicit_opt_in(monkeypatch):
    monkeypatch.setenv("FINAI_ENV", "development")
    monkeypatch.setenv("FINAI_API_AUTH_MODE", "bearer")
    monkeypatch.setenv("FINAI_API_BEARER_TOKEN", TRACE_TOKEN)
    monkeypatch.delenv("FINAI_ENABLE_XAI_TRACE_API", raising=False)

    response = client.get(
        "/api/v1/xai/traces",
        headers={"Authorization": f"Bearer {TRACE_TOKEN}"},
    )

    assert response.status_code == 404


def test_list_traces_requires_explicit_bearer_opt_in(monkeypatch):
    headers = configure_trace_access(monkeypatch)
    response = client.get("/api/v1/xai/traces", headers=headers)

    assert response.status_code == 200
    data = response.json()
    assert "count" in data
    assert "traces" in data
    assert isinstance(data["count"], int)
    assert isinstance(data["traces"], list)


def test_trace_not_found(monkeypatch):
    headers = configure_trace_access(monkeypatch)
    response = client.get(
        "/api/v1/xai/traces/nonexistent-trace-000",
        headers=headers,
    )
    assert response.status_code == 404


def test_invalid_trace_id(monkeypatch):
    headers = configure_trace_access(monkeypatch)
    response = client.get(
        "/api/v1/xai/traces/invalid_trace_id",
        headers=headers,
    )
    assert response.status_code == 400


def test_trace_api_rejects_missing_bearer(monkeypatch):
    configure_trace_access(monkeypatch)
    response = client.get("/api/v1/xai/traces")
    assert response.status_code == 401


def test_trace_can_be_deleted_with_authorized_opt_in(tmp_path, monkeypatch):
    headers = configure_trace_access(monkeypatch)
    monkeypatch.setattr(xai_api_module, "TRACE_DIR", tmp_path)
    trace_id = "trace-delete123"
    trace_path = tmp_path / f"{trace_id}.json"
    trace_path.write_text('{"trace_id":"trace-delete123"}', encoding="utf-8")

    response = client.delete(
        f"/api/v1/xai/traces/{trace_id}",
        headers=headers,
    )

    assert response.status_code == 200
    assert response.json() == {"status": "DELETED", "trace_id": trace_id}
    assert not trace_path.exists()


def test_full_trace_details_require_separate_opt_in(monkeypatch):
    monkeypatch.setenv("FINAI_ENV", "development")
    monkeypatch.setenv("FINAI_API_AUTH_MODE", "bearer")
    monkeypatch.setenv("FINAI_API_BEARER_TOKEN", TRACE_TOKEN)
    monkeypatch.setenv("FINAI_ENABLE_XAI_TRACE_API", "true")
    monkeypatch.delenv("FINAI_ENABLE_XAI_TRACE_DETAILS", raising=False)

    response = client.get(
        "/api/v1/xai/traces/nonexistent-trace-000",
        headers={"Authorization": f"Bearer {TRACE_TOKEN}"},
    )
    assert response.status_code == 404
