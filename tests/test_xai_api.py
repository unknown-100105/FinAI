from fastapi.testclient import TestClient

from app.xai_api import app


client = TestClient(app)


def test_health():
    response = client.get("/health")

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "ok"
    assert data["service"] == "finai-xai-api"


def test_list_traces():
    response = client.get("/api/v1/xai/traces")

    assert response.status_code == 200

    data = response.json()

    assert "count" in data
    assert "traces" in data
    assert isinstance(data["count"], int)
    assert isinstance(data["traces"], list)


def test_trace_not_found():
    response = client.get(
        "/api/v1/xai/traces/nonexistent-trace-000"
    )

    assert response.status_code == 404


def test_invalid_trace_id():
    response = client.get(
        "/api/v1/xai/traces/invalid_trace_id"
    )

    assert response.status_code == 400
