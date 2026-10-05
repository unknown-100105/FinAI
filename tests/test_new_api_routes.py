from fastapi.testclient import TestClient

from app.main import app


def test_route_registry_has_new_modules():
    paths = set(app.openapi()["paths"])
    expected = {
        "/api/v1/compliance/catalog",
        "/api/v1/resources",
        "/api/v1/models",
        "/api/v1/market/analyst",
        "/api/v1/market/analyst/explain",
        "/api/v1/crypto/ohlcv",
        "/api/v1/crypto/arbitrage/scan-all",
        "/api/v1/crypto/mining/btc",
        "/api/v1/knowledge/investment-routes",
        "/api/v1/system/status",
        "/api/v1/causal-risk/graph",
        "/api/v1/causal-risk/architecture",
    }
    assert expected <= paths


def test_system_status_is_reachable():
    client = TestClient(app)
    response = client.get("/api/v1/system/status")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert "/api/v1/resources" in body["api_prefixes"]


def test_resource_catalog_is_reachable():
    client = TestClient(app)
    response = client.get("/api/v1/resources")
    assert response.status_code == 200
    assert response.json()["count"] > 0


def test_compliance_catalog_is_reachable():
    client = TestClient(app)
    response = client.get("/api/v1/compliance/catalog")
    assert response.status_code == 200
    assert response.json()["items"]


def test_model_registry_endpoint_is_reachable():
    client = TestClient(app)
    response = client.get("/api/v1/models?capability=financial_qa")
    assert response.status_code == 200
    assert "models" in response.json()


def test_causal_risk_counterfactual_is_reachable():
    client = TestClient(app)
    response = client.post("/api/v1/causal-risk/counterfactual", json={"shock": {"rates": 75, "supply": 60}})
    assert response.status_code == 200
    body = response.json()
    assert 0 <= body["systemic_stress"] <= 100


def test_causal_architecture_is_reachable():
    client = TestClient(app)
    response = client.get("/api/v1/causal-risk/architecture")
    assert response.status_code == 200
    assert response.json()["status"] == "architecture_implemented"


def test_causal_counterfactual_can_generate_tail_scenarios():
    client = TestClient(app)
    response = client.post(
        "/api/v1/causal-risk/counterfactual",
        json={"shock": {"rates": 75, "supply": 60}, "include_tail_scenarios": True},
    )
    assert response.status_code == 200
    assert response.json()["tail_scenarios"]["scenario_count"] > 0
