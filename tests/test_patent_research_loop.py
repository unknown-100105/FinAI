from fastapi.testclient import TestClient

from app.main import app


def test_feasibility_screen_api_is_registered():
    paths = set(app.openapi()["paths"])
    assert "/api/v1/causal-risk/research-pruning/screen" in paths
    assert "/api/v1/causal-risk/research-pruning/constrained-gfnets" in paths


def test_feasibility_screen_api_returns_certificate():
    client = TestClient(app)
    response = client.post(
        "/api/v1/causal-risk/research-pruning/screen",
        json={
            "nodes": ["rates", "credit", "portfolio"],
            "edges": [
                {"source": "rates", "target": "credit", "weight": 0.8},
                {"source": "credit", "target": "portfolio", "weight": 0.9},
            ],
            "prefix": {},
            "candidate_actions": {"rates": [-100, 0, 100]},
            "node_bounds": {
                "rates": [-100, 100],
                "credit": [-100, 100],
                "portfolio": [-100, 100],
            },
            "target_node": "portfolio",
            "target_interval": [50, 100],
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "CAUSAL_FEASIBILITY_SCREENING_READY"
    assert body["candidates"][0]["certificate"]["certificate_type"].startswith(
        "conservative_linear_dag"
    )
    assert body["hard_pruned_candidates"] >= 1
