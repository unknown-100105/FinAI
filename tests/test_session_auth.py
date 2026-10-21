from fastapi.testclient import TestClient

from app.main import app


def test_demo_authentication_is_disabled_by_default(monkeypatch):
    monkeypatch.setenv("FINAI_ENV", "development")
    monkeypatch.delenv("FINAI_ENABLE_DEMO_SESSION_AUTH", raising=False)
    client = TestClient(app)

    response = client.post(
        "/api/v1/session/authenticate",
        json={"session_id": "test-auth-session"},
    )

    assert response.status_code == 404


def test_demo_authentication_requires_explicit_nonproduction_opt_in(monkeypatch):
    monkeypatch.setenv("FINAI_ENV", "development")
    monkeypatch.setenv("FINAI_ENABLE_DEMO_SESSION_AUTH", "true")
    client = TestClient(app)

    response = client.post(
        "/api/v1/session/authenticate",
        json={"session_id": "test-auth-session"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "AUTHENTICATED"
    assert data["session"]["authenticated"] is True
    assert "demo only" in data["message"].lower()


def test_demo_authentication_is_disabled_in_production(monkeypatch):
    monkeypatch.setenv("FINAI_ENV", "production")
    monkeypatch.setenv("FINAI_ENABLE_DEMO_SESSION_AUTH", "true")
    monkeypatch.setenv("FINAI_API_AUTH_MODE", "bearer")
    monkeypatch.setenv("FINAI_API_BEARER_TOKEN", "test-only-token-with-at-least-32-characters")
    client = TestClient(app)

    response = client.post(
        "/api/v1/session/authenticate",
        json={"session_id": "test-auth-session-prod"},
        headers={"Authorization": "Bearer test-only-token-with-at-least-32-characters"},
    )

    assert response.status_code == 404


def test_logout_clears_demo_session_authentication(monkeypatch):
    monkeypatch.setenv("FINAI_ENV", "development")
    monkeypatch.setenv("FINAI_ENABLE_DEMO_SESSION_AUTH", "true")
    client = TestClient(app)

    client.post(
        "/api/v1/session/authenticate",
        json={"session_id": "test-auth-session-logout"},
    )

    response = client.post(
        "/api/v1/session/logout",
        json={"session_id": "test-auth-session-logout"},
    )

    assert response.status_code == 200
    assert response.json()["session"]["authenticated"] is False


def test_session_id_rejects_path_separators(monkeypatch):
    monkeypatch.setenv("FINAI_ENV", "development")
    monkeypatch.setenv("FINAI_ENABLE_DEMO_SESSION_AUTH", "true")
    client = TestClient(app)

    response = client.post(
        "/api/v1/session/authenticate",
        json={"session_id": "../outside"},
    )

    assert response.status_code == 422
