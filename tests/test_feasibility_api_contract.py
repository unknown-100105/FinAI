from fastapi.testclient import TestClient

from app.main import app
from app.advanced_causal_api import ConstrainedGFlowNetGenerateRequest


client = TestClient(app)


def test_research_pruning_rejects_malformed_node_bounds():
    response = client.post(
        "/api/v1/causal-risk/research-pruning/screen",
        json={
            "nodes": ["rates", "portfolio"],
            "edges": [{"source": "rates", "target": "portfolio", "weight": 0.8}],
            "candidate_actions": {"rates": [1.0]},
            "node_bounds": {"rates": [-100.0, 100.0, 200.0], "portfolio": [-100.0, 100.0]},
            "target_node": "portfolio",
            "target_interval": [0.0, 10.0],
        },
    )
    assert response.status_code == 422


def test_constrained_gfnets_contract_exposes_bidirectional_toggle():
    request = ConstrainedGFlowNetGenerateRequest(
        factor_ids=["rates"],
        center={"rates": 10.0},
        nodes=["rates", "portfolio"],
        edges=[{"source": "rates", "target": "portfolio", "weight": 0.8}],
        node_bounds={"rates": [-100.0, 100.0], "portfolio": [-100.0, 100.0]},
        target_node="portfolio",
        target_interval=[0.0, 10.0],
    )
    assert request.use_bidirectional_feasibility is True

