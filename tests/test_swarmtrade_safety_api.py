from __future__ import annotations

from app.swarmtrade_safety_api import (
    CandidateRiskRequest,
    evaluate_candidate_risk,
    safety_status,
)


def base_request(**overrides):
    payload = {
        "instrument_id": "TEST-EQ",
        "asset_class": "equity",
        "side": "buy",
        "quantity": 2,
        "reference_price": 100,
        "spread_bps": 5,
        "quote_age_seconds": 1,
        "portfolio_notional_after": 200,
        "daily_loss_after": 0,
        "leverage_after": 1,
        "evidence_count": 1,
    }
    payload.update(overrides)
    return CandidateRiskRequest(**payload)


def test_safety_status_is_research_and_simulation_only():
    result = safety_status()
    assert result["approval_semantics"] == "simulation_only"
    assert result["live_execution_enabled"] is False
    assert result["broker_connected"] is False
    assert result["order_submission_supported"] is False


def test_risk_endpoint_approves_only_for_simulation():
    result = evaluate_candidate_risk(base_request())
    assert result["allowed"] is True
    assert result["state"] == "approved_for_simulation"
    assert result["execution"] == {
        "live_execution_enabled": False,
        "broker_connected": False,
        "order_submitted": False,
        "fill_claimed": False,
    }


def test_risk_endpoint_rejects_missing_quote_and_evidence():
    result = evaluate_candidate_risk(base_request(spread_bps=None, evidence_count=0))
    assert result["allowed"] is False
    assert result["state"] == "risk_rejected"
    assert any("spread is missing" in reason for reason in result["reasons"])
    assert any("evidence-backed" in reason for reason in result["reasons"])


def test_derivative_risk_is_disabled_by_default():
    result = evaluate_candidate_risk(base_request(
        asset_class="option",
        estimated_max_loss=100,
        has_bounded_max_loss=True,
        has_valid_contract_metadata=True,
    ))
    assert result["allowed"] is False
    assert any("derivatives are disabled" in reason for reason in result["reasons"])
