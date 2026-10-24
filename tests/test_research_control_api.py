from datetime import datetime, timezone

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def request_body(**overrides):
    body = {
        "experiment_id": "test-exp-1",
        "evidence": [
            {"evidence_id": "source-a", "observed_at": datetime.now(timezone.utc).timestamp(),
             "valid_for_seconds": 3600, "confidence": 0.95},
            {"evidence_id": "source-b", "observed_at": datetime.now(timezone.utc).timestamp(),
             "valid_for_seconds": 1800, "confidence": 0.9},
        ],
        "conflict_pairs": [],
        "uncertainty": 0.05,
        "disagreement": 0.05,
        "operations": ["run_counterfactual", "run_benchmark"],
        "state": {"symbol": "TEST", "window": "2026-Q3", "seed": 42},
        "model_version": "research-model-v1",
        "policy_version": "research-policy-v1",
        "ttl_seconds": 300,
        "metrics": {"samples": 100, "heldout_mae": 0.12},
    }
    body.update(overrides)
    return body


def test_research_control_fresh_evidence_issues_verifiable_proof_without_trade_authority():
    response = client.post("/api/v1/causal-risk/research-control/evaluate", json=request_body())
    assert response.status_code == 200
    result = response.json()
    assert result["status"] == "RESEARCH_CONTROL_EVALUATED"
    assert result["evidence"]["fresh_count"] == 2
    assert result["capability"]["mode"] == "full"
    assert result["lease"]["valid"] is True
    assert result["proof"]["status"] == "RESEARCH_EXPERIMENT_PROOF_READY"
    assert len(result["proof"]["proof_digest"]) == 64
    assert result["decision_boundary"]["trade_authorized"] is False
    assert result["decision_boundary"]["order_submitted"] is False


def test_research_control_stale_evidence_restricts_capability():
    body = request_body(evidence=[
        {"evidence_id": "stale", "observed_at": 1, "valid_for_seconds": 1, "confidence": 0.99},
    ])
    result = client.post("/api/v1/causal-risk/research-control/evaluate", json=body).json()
    assert result["evidence"]["stale_count"] == 1
    assert result["capability"]["mode"] == "restricted"
    assert "stale_evidence" in result["capability"]["reasons"]


def test_research_control_conflicts_restrict_allowed_operations():
    body = request_body(conflict_pairs=[["source-a", "source-b"]])
    result = client.post("/api/v1/causal-risk/research-control/evaluate", json=body).json()
    assert result["evidence"]["conflict_count"] == 1
    assert result["capability"]["mode"] == "safe"
    assert len(result["capability"]["allowed_operations"]) <= 1


def test_research_control_high_uncertainty_quarantines_operations():
    result = client.post("/api/v1/causal-risk/research-control/evaluate",
                         json=request_body(uncertainty=0.9)).json()
    assert result["capability"]["mode"] == "quarantine"
    assert result["capability"]["allowed_operations"] == []


def test_research_control_rejects_duplicate_evidence_ids():
    body = request_body(evidence=[
        {"evidence_id": "dup", "observed_at": 100, "valid_for_seconds": 100, "confidence": 0.9},
        {"evidence_id": "dup", "observed_at": 100, "valid_for_seconds": 100, "confidence": 0.9},
    ])
    response = client.post("/api/v1/causal-risk/research-control/evaluate", json=body)
    assert response.status_code == 422


def test_research_control_rejects_execution_operations():
    response = client.post("/api/v1/causal-risk/research-control/evaluate",
                           json=request_body(operations=["submit_order"]))
    assert response.status_code == 422


def test_research_control_rejects_unknown_conflict_evidence_ids():
    response = client.post("/api/v1/causal-risk/research-control/evaluate",
                           json=request_body(conflict_pairs=[["source-a", "missing"]]))
    assert response.status_code == 422


def test_research_control_status_disclaims_trade_authority():
    result = client.get("/api/v1/causal-risk/research-control/status").json()
    assert result["can_authorize_trades"] is False
    assert result["evidence_is_independently_verified"] is False
