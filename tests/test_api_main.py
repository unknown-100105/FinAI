import pytest
from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


@pytest.fixture(autouse=True)
def enable_isolated_demo_auth(monkeypatch):
    monkeypatch.setenv("FINAI_ENV", "development")
    monkeypatch.setenv("FINAI_API_AUTH_MODE", "development")
    monkeypatch.delenv("FINAI_API_BEARER_TOKEN", raising=False)
    monkeypatch.delenv("FINAI_ENABLE_XAI_TRACE_API", raising=False)
    monkeypatch.setenv("FINAI_ENABLE_DEMO_SESSION_AUTH", "true")


def test_health():
    response = client.get("/health")

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "ok"
    assert data["service"] == "finai-api"


def test_api_info():
    response = client.get("/api/v1")

    assert response.status_code == 200

    data = response.json()

    assert data["service"] == "FinAI"
    assert data["endpoints"]["chat"] == "/api/v1/chat"
    assert data["endpoints"]["brain_status"] == "/api/v1/system/brain-status"
    assert data["endpoints"]["xai"] == "/api/v1/xai"


def test_chat_authentication_flow():
    session_id = "api-test-account-balance"

    response = client.post(
        "/api/v1/chat",
        json={
            "session_id": session_id,
            "message": "How much is my account balance?",
        },
    )

    assert response.status_code == 200

    first = response.json()

    assert first["session_id"] == session_id
    assert first["status"] == "AUTH_REQUIRED"
    assert first["trace_id"]
    assert first["session"]["awaiting_authentication"] is True

    response = client.post(
        "/api/v1/chat",
        json={
            "session_id": session_id,
            "message": "authenticated",
        },
    )

    assert response.status_code == 200

    second = response.json()

    assert second["status"] == "TOOL_EXECUTED"
    assert second["session"]["authenticated"] is True
    assert second["trace_id"]
    assert second["tool"]["success"] is True


def test_chat_confirmation_flow():
    session_id = "api-test-card-lost"

    response = client.post(
        "/api/v1/chat",
        json={
            "session_id": session_id,
            "message": "My card is lost",
        },
    )

    assert response.status_code == 200

    first = response.json()

    assert first["status"] == "AUTH_REQUIRED"
    assert first["session"]["awaiting_authentication"] is True

    response = client.post(
        "/api/v1/chat",
        json={
            "session_id": session_id,
            "message": "authenticated",
        },
    )

    assert response.status_code == 200

    second = response.json()

    assert second["status"] == "CONFIRMATION_REQUIRED"
    assert second["session"]["awaiting_confirmation"] is True

    response = client.post(
        "/api/v1/chat",
        json={
            "session_id": session_id,
            "message": "yes",
        },
    )

    assert response.status_code == 200

    third = response.json()

    assert third["status"] == "TOOL_EXECUTED"
    assert third["tool"]["success"] is True
    assert third["session"]["awaiting_confirmation"] is False


def test_chat_rejects_empty_message():
    response = client.post(
        "/api/v1/chat",
        json={
            "message": "   ",
        },
    )

    assert response.status_code == 422

def test_chat_confirmation_cannot_bypass_authentication():
    session_id = "api-security-regression"

    response = client.post(
        "/api/v1/chat",
        json={
            "session_id": session_id,
            "message": "My card is lost",
        },
    )

    assert response.status_code == 200
    first = response.json()

    assert first["status"] == "AUTH_REQUIRED"
    assert first["session"]["authenticated"] is False
    assert first["session"]["awaiting_authentication"] is True

    response = client.post(
        "/api/v1/chat",
        json={
            "session_id": session_id,
            "message": "yes",
        },
    )

    assert response.status_code == 200
    blocked = response.json()

    assert blocked["status"] == "AUTH_REQUIRED"
    assert blocked["session"]["authenticated"] is False
    assert blocked["session"]["awaiting_authentication"] is True
    assert blocked["session"]["awaiting_confirmation"] is False

    response = client.post(
        "/api/v1/chat",
        json={
            "session_id": session_id,
            "message": "authenticated",
        },
    )

    assert response.status_code == 200
    authenticated = response.json()

    assert authenticated["status"] == "CONFIRMATION_REQUIRED"
    assert authenticated["session"]["authenticated"] is True
    assert authenticated["session"]["awaiting_confirmation"] is True

    response = client.post(
        "/api/v1/chat",
        json={
            "session_id": session_id,
            "message": "yes",
        },
    )

    assert response.status_code == 200
    executed = response.json()

    assert executed["status"] == "TOOL_EXECUTED"
    assert executed["tool"]["success"] is True
    assert executed["session"]["awaiting_confirmation"] is False


def test_chat_api_does_not_expose_rejected_model_output(monkeypatch):
    class FakeOrchestrator:
        def handle_message(self, **kwargs):
            return {
                "status": "VERIFICATION_FAILED",
                "message": "Safe public message",
                "response_generation": {
                    "status": "VERIFICATION_FAILED",
                    "response": "Safe public message",
                    "original_response": "Private rejected text with account 123456",
                },
                "original_response": "Top-level rejected text",
            }

    monkeypatch.setattr("app.main.get_orchestrator", lambda: FakeOrchestrator())
    response = client.post(
        "/api/v1/chat",
        json={"message": "Explain this finance result"},
    )

    assert response.status_code == 200
    data = response.json()
    assert "original_response" not in data
    assert "original_response" not in data["response_generation"]
    assert data["response_generation"]["response"] == "Safe public message"


def test_existing_chat_session_requires_server_issued_capability(monkeypatch):
    monkeypatch.delenv("FINAI_ENABLE_DEMO_SESSION_AUTH", raising=False)
    monkeypatch.setenv("FINAI_API_AUTH_MODE", "development")

    class FakeOrchestrator:
        def handle_message(self, **kwargs):
            return {"status": "OK", "message": "safe", "session": {"authenticated": False}}

    monkeypatch.setattr("app.main.get_orchestrator", lambda: FakeOrchestrator())
    first = client.post("/api/v1/chat", json={"message": "hello"})
    assert first.status_code == 200
    data = first.json()
    assert data["session_id"].startswith("session-")
    assert len(data["session_token"]) >= 32

    follow_up = client.post(
        "/api/v1/chat",
        json={
            "message": "continue",
            "session_id": data["session_id"],
            "session_token": data["session_token"],
        },
    )
    assert follow_up.status_code == 200
    assert follow_up.json()["session_id"] == data["session_id"]

    hijack = client.post(
        "/api/v1/chat",
        json={"message": "continue", "session_id": data["session_id"]},
    )
    assert hijack.status_code == 401


def test_caller_selected_session_id_cannot_create_an_existing_session_without_capability(monkeypatch):
    monkeypatch.delenv("FINAI_ENABLE_DEMO_SESSION_AUTH", raising=False)
    monkeypatch.setenv("FINAI_API_AUTH_MODE", "development")

    response = client.post(
        "/api/v1/chat",
        json={"message": "hello", "session_id": "attacker-chosen-session"},
    )
    assert response.status_code == 401


def test_mounted_trace_api_is_disabled_by_default(monkeypatch):
    monkeypatch.delenv("FINAI_ENABLE_XAI_TRACE_API", raising=False)
    response = client.get("/api/v1/xai/traces")
    assert response.status_code == 404


def test_mounted_trace_api_requires_bearer_when_enabled(monkeypatch):
    token = "test-only-token-with-at-least-32-characters"
    monkeypatch.setenv("FINAI_API_AUTH_MODE", "bearer")
    monkeypatch.setenv("FINAI_API_BEARER_TOKEN", token)
    monkeypatch.setenv("FINAI_ENABLE_XAI_TRACE_API", "true")

    denied = client.get("/api/v1/xai/traces")
    assert denied.status_code == 401

    allowed = client.get(
        "/api/v1/xai/traces",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert allowed.status_code == 200
