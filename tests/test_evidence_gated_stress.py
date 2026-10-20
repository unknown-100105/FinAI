from datetime import datetime, timezone

from causal_risk.evidence_gate import evaluate_evidence_gate, required_evidence_claims
from causal_risk.evidence_gated_stress import run_evidence_gated_stress_test


SHOCK = {"rates": 10.0, "usd": 5.0}
ALLOCATION = {"equity": 55.0, "debt": 30.0, "gold": 10.0, "cash": 5.0}
AS_OF = "2026-10-20T00:00:00+00:00"


def evidence_for(shock=SHOCK):
    claims = required_evidence_claims(shock)
    return [
        {
            "evidence_id": f"ev-{index}",
            "source": "test-authoritative-source",
            "observed_at": AS_OF,
            "confidence": 0.95,
            "supports": [claim],
        }
        for index, claim in enumerate(claims)
    ]


def test_evidence_gate_requires_each_intervention_and_relevant_edge():
    claims = required_evidence_claims(SHOCK)
    result = evaluate_evidence_gate(
        SHOCK,
        evidence_for(),
        as_of=AS_OF,
        minimum_confidence=0.6,
        max_age_days=30,
    )
    assert result["passed"] is True
    assert set(result["required_claims"]) == set(claims)
    assert result["missing_claims"] == []


def test_evidence_gate_rejects_missing_and_stale_evidence():
    result = evaluate_evidence_gate(
        SHOCK,
        [{
            "evidence_id": "old",
            "source": "source",
            "observed_at": "2025-01-01T00:00:00+00:00",
            "confidence": 0.99,
            "supports": ["intervention:rates"],
        }],
        as_of=AS_OF,
        max_age_days=30,
    )
    assert result["passed"] is False
    assert result["missing_claims"]
    assert any(item["reason"] == "evidence is stale" for item in result["rejected_records"])


def test_evidence_gate_rejects_future_timestamp_and_low_confidence():
    result = evaluate_evidence_gate(
        SHOCK,
        [
            {
                "evidence_id": "future",
                "source": "source",
                "observed_at": "2027-01-01T00:00:00+00:00",
                "confidence": 0.99,
                "supports": ["intervention:rates"],
            },
            {
                "evidence_id": "weak",
                "source": "source",
                "observed_at": AS_OF,
                "confidence": 0.1,
                "supports": ["intervention:usd"],
            },
        ],
        as_of=AS_OF,
    )
    assert result["passed"] is False
    reasons = {item["reason"] for item in result["rejected_records"]}
    assert "evidence timestamp is in the future" in reasons
    assert "confidence below threshold" in reasons


def test_stress_pipeline_fails_closed_before_simulation_when_gate_fails():
    result = run_evidence_gated_stress_test(
        SHOCK,
        ALLOCATION,
        [],
        as_of=AS_OF,
    )
    assert result["status"] == "EVIDENCE_GATE_REJECTED"
    assert result["feasibility"]["status"] == "NOT_RUN"
    assert result["summary"]["accepted_scenarios"] == 0


def test_stress_pipeline_runs_seeded_feasible_scenarios_when_evidence_passes():
    first = run_evidence_gated_stress_test(
        SHOCK,
        ALLOCATION,
        evidence_for(),
        as_of=AS_OF,
        include_tail_scenarios=True,
        tail_draws=8,
        tail_seed=7,
    )
    second = run_evidence_gated_stress_test(
        SHOCK,
        ALLOCATION,
        evidence_for(),
        as_of=AS_OF,
        include_tail_scenarios=True,
        tail_draws=8,
        tail_seed=7,
    )
    assert first["status"] == "EVIDENCE_GATED_STRESS_TEST_COMPLETE"
    assert first == second
    assert first["evidence_gate"]["passed"] is True
    assert first["summary"]["accepted_scenarios"] >= 1
    assert first["summary"]["realized_tail_coverage"] is None



def test_research_api_exposes_evidence_gated_stress_endpoint():
    from fastapi.testclient import TestClient
    from app.main import app

    client = TestClient(app)
    response = client.post(
        "/api/v1/causal-risk/stress-test/evidence-gated",
        json={
            "shock": SHOCK,
            "allocation": ALLOCATION,
            "evidence": evidence_for(),
            "as_of": AS_OF,
            "include_tail_scenarios": False,
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "EVIDENCE_GATED_STRESS_TEST_COMPLETE"
    assert payload["experimental"] is True
    assert payload["production_validated"] is False
