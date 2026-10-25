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


def test_demo_session_authentication_is_disabled_in_production(monkeypatch):
    monkeypatch.setenv("FINAI_ENV", "production")
    monkeypatch.setenv("FINAI_API_AUTH_MODE", "bearer")
    monkeypatch.setenv("FINAI_API_BEARER_TOKEN", VALID_TOKEN)
    headers = {"Authorization": f"Bearer {VALID_TOKEN}"}

    authenticate = client.post(
        "/api/v1/session/authenticate",
        json={"session_id": "demo-session"},
        headers=headers,
    )
    assert authenticate.status_code == 503
    assert "real identity provider" in authenticate.json()["detail"]

    logout = client.post(
        "/api/v1/session/logout",
        json={"session_id": "demo-session"},
        headers=headers,
    )
    assert logout.status_code == 503


def test_invalid_auth_mode_fails_closed(monkeypatch):
    monkeypatch.setenv("FINAI_ENV", "development")
    monkeypatch.setenv("FINAI_API_AUTH_MODE", "sometimes")
    monkeypatch.setenv("FINAI_API_BEARER_TOKEN", VALID_TOKEN)

    response = client.get("/api/v1")
    assert response.status_code == 503


def test_cors_development_defaults_are_local_only():
    from app.main import _cors_allowed_origins

    assert _cors_allowed_origins("development", "") == [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
    ]


def test_cors_production_defaults_to_no_browser_origins():
    from app.main import _cors_allowed_origins

    assert _cors_allowed_origins("production", "") == []


def test_cors_production_uses_explicit_allowlist():
    from app.main import _cors_allowed_origins

    assert _cors_allowed_origins(
        "production", "https://finai.example.com, https://admin.example.com/"
    ) == ["https://finai.example.com", "https://admin.example.com"]


def test_cors_rejects_wildcard_with_credentials():
    import pytest
    from app.main import _cors_allowed_origins

    with pytest.raises(ValueError, match="must not contain"):
        _cors_allowed_origins("production", "*")
