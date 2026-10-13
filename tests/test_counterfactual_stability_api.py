import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.patent_mechanism_api import router

TOKEN = "test-only-research-api-token-0123456789abcdef"


@pytest.fixture(autouse=True)
def configure_research_token(monkeypatch):
    monkeypatch.setenv("FINAI_RESEARCH_API_TOKEN", TOKEN)


def client():
    app = FastAPI()
    app.include_router(router)
    return TestClient(app)


def payload():
    common = {
        "intervention_key": "rates:+100bp",
        "metric": "portfolio_loss_delta",
        "model_version": "v1",
        "graph_digest": "graph-a",
        "evidence_digest": "evidence-a",
        "regime": "baseline",
        "approved": True,
    }
    return {
        "runs": [
            {**common, "run_id": "r1", "delta_low": 1.0, "delta_high": 2.0},
            {**common, "run_id": "r2", "model_version": "v2",
             "delta_low": 0.5, "delta_high": 1.5},
            {**common, "run_id": "r3", "regime": "stress",
             "delta_low": 2.0, "delta_high": 3.0},
        ]
    }


def test_counterfactual_stability_api_requires_research_token():
    response = client().post("/api/v1/research/patent-mechanisms/counterfactual-stability",
                             json=payload())
    assert response.status_code == 401


def test_counterfactual_stability_api_returns_replayable_experimental_result():
    response = client().post(
        "/api/v1/research/patent-mechanisms/counterfactual-stability",
        headers={"Authorization": f"Bearer {TOKEN}"},
        json=payload(),
    )
    assert response.status_code == 200, response.text
    result = response.json()
    assert result["status"] == "DIRECTION_STABLE"
    assert result["direction"] == "positive"
    assert result["production_validated"] is False
    assert len(result["replay_digest"]) == 64


def test_counterfactual_stability_api_rejects_mismatched_interventions():
    data = payload()
    data["runs"][1]["intervention_key"] = "oil:+10%"
    response = client().post(
        "/api/v1/research/patent-mechanisms/counterfactual-stability",
        headers={"Authorization": f"Bearer {TOKEN}"},
        json=data,
    )
    assert response.status_code == 422
