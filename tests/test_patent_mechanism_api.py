from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.patent_mechanism_api import router


def build_client():
    app = FastAPI()
    app.include_router(router)
    return TestClient(app)


def test_epcrp_endpoint_returns_paired_world_delta_and_manifest():
    client = build_client()
    response = client.post("/api/v1/research/patent-mechanisms/epcrp/evaluate", json={
        "nodes": [{"name": "A"}, {"name": "B"}],
        "edges": [{
            "source": "A", "target": "B", "coefficient": 2.0,
            "evidence_id": "EDGE-AB", "support_score": 0.95
        }],
        "source_values": {"A": 2.0},
        "interventions": {"A": 3.0},
        "portfolio_exposures": {"B": 1.0},
        "as_of": "2026-10-13T00:00:00Z",
        "regime": "baseline",
        "model_version": "api-test-v1"
    })
    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["status"] == "EXPERIMENTAL_EPCRP_RESULT"
    assert payload["production_validated"] is False
    assert payload["portfolio_delta"] == 2.0
    assert payload["evidence_by_output"]["B"] == ["EDGE-AB"]
    assert payload["manifest"]["model_version"] == "api-test-v1"


def test_epcrp_endpoint_returns_422_for_unknown_node():
    response = build_client().post(
        "/api/v1/research/patent-mechanisms/epcrp/evaluate",
        json={
            "nodes": [{"name": "A"}],
            "source_values": {},
            "interventions": {"UNKNOWN": 2.0},
            "portfolio_exposures": {"A": 1.0},
            "as_of": "2026-10-13T00:00:00Z"
        },
    )
    assert response.status_code == 422


def test_feasibility_screen_endpoint_labels_retain_as_uncertain():
    response = build_client().post(
        "/api/v1/research/patent-mechanisms/feasibility-screen",
        json={
            "nodes": [
                {"name": "A", "domain": {"low": 0, "high": 10}},
                {"name": "B", "domain": {"low": 0, "high": 10},
                 "parents": {"A": 1.0}}
            ],
            "target": "B",
            "target_interval": {"low": 5, "high": 7},
            "actions": [{
                "action_id": "reach-six",
                "interventions": {"A": {"low": 6, "high": 6}}
            }]
        },
    )
    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["production_validated"] is False
    certificate = payload["certificates"][0]
    assert certificate["status"] == "RETAIN"
    assert "does not certify" in payload["interpretation"]


def test_feasibility_screen_endpoint_masks_out_of_domain_intervention():
    response = build_client().post(
        "/api/v1/research/patent-mechanisms/feasibility-screen",
        json={
            "nodes": [
                {"name": "A", "domain": {"low": 0, "high": 10}},
                {"name": "B", "domain": {"low": 0, "high": 10},
                 "parents": {"A": 1.0}}
            ],
            "target": "B",
            "target_interval": {"low": 5, "high": 7},
            "actions": [{
                "action_id": "outside",
                "interventions": {"A": {"low": 11, "high": 12}}
            }]
        },
    )
    assert response.status_code == 200, response.text
    assert response.json()["certificates"][0]["status"] == "MASK"
