from fastapi.testclient import TestClient

from app.main import app


def test_demo_authentication_endpoint_is_explicit():
    client = TestClient(app)

    response = client.post(
        "/api/v1/session/authenticate",
        json={"session_id": "test-auth-session"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "AUTHENTICATED"
    assert data["session"]["authenticated"] is True
    assert "demo" in data["message"].lower()


def test_logout_clears_session_authentication():
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
