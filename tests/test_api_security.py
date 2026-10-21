from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)
VALID_TOKEN = "test-only-token-with-at-least-32-characters"


def test_development_mode_keeps_local_api_usable(monkeypatch):
    monkeypatch.setenv("FINAI_ENV", "development")
    monkeypatch.setenv("FINAI_API_AUTH_MODE", "development")
    monkeypatch.delenv("FINAI_API_BEARER_TOKEN", raising=False)

    response = client.get("/api/v1")
    assert response.status_code == 200


def test_bearer_mode_rejects_missing_and_invalid_tokens(monkeypatch):
    monkeypatch.setenv("FINAI_ENV", "development")
    monkeypatch.setenv("FINAI_API_AUTH_MODE", "bearer")
    monkeypatch.setenv("FINAI_API_BEARER_TOKEN", VALID_TOKEN)

    assert client.get("/api/v1").status_code == 401
    response = client.get("/api/v1", headers={"Authorization": "Bearer wrong"})
    assert response.status_code == 401
    assert response.headers["www-authenticate"] == "Bearer"


def test_bearer_mode_accepts_configured_token(monkeypatch):
    monkeypatch.setenv("FINAI_ENV", "development")
    monkeypatch.setenv("FINAI_API_AUTH_MODE", "bearer")
    monkeypatch.setenv("FINAI_API_BEARER_TOKEN", VALID_TOKEN)

    response = client.get(
        "/api/v1",
        headers={"Authorization": f"Bearer {VALID_TOKEN}"},
    )
    assert response.status_code == 200


def test_health_probe_stays_public_in_bearer_mode(monkeypatch):
    monkeypatch.setenv("FINAI_ENV", "production")
    monkeypatch.setenv("FINAI_API_AUTH_MODE", "bearer")
    monkeypatch.setenv("FINAI_API_BEARER_TOKEN", VALID_TOKEN)

    response = client.get("/health")
    assert response.status_code == 200


def test_production_fails_closed_without_strong_token(monkeypatch):
    monkeypatch.setenv("FINAI_ENV", "production")
    monkeypatch.setenv("FINAI_API_AUTH_MODE", "development")
    monkeypatch.setenv("FINAI_API_BEARER_TOKEN", "short")

    response = client.get("/api/v1")
    assert response.status_code == 503
    assert "FINAI_API_BEARER_TOKEN" in response.json()["detail"]


def test_invalid_auth_mode_fails_closed(monkeypatch):
    monkeypatch.setenv("FINAI_ENV", "development")
    monkeypatch.setenv("FINAI_API_AUTH_MODE", "sometimes")
    monkeypatch.setenv("FINAI_API_BEARER_TOKEN", VALID_TOKEN)

    response = client.get("/api/v1")
    assert response.status_code == 503
