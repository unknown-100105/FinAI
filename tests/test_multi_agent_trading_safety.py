from __future__ import annotations

import math

import pytest

from swarmtrade.multi_agent import (
    AgentFinding,
    AssetClass,
    EvidenceItem,
    OrderState,
    OrderSide,
    RiskLimits,
    SharedEvidenceStore,
    TradeCandidate,
    evaluate_candidate,
    live_execution_enabled,
    validate_order_transition,
)


def evidence(source_id: str = "quote-1") -> EvidenceItem:
    return EvidenceItem(
        source_id=source_id,
        source_uri="https://example.invalid/market-data",
        observed_at="2026-10-25T10:00:00+00:00",
        published_at=None,
        summary="Test fixture only; not live market evidence.",
    )


def limits(**overrides) -> RiskLimits:
    values = {
        "max_order_notional": 5_000,
        "max_portfolio_notional": 20_000,
        "max_daily_loss": 500,
        "max_leverage": 1.0,
        "max_spread_bps": 25,
        "max_quote_age_seconds": 5,
        "allow_derivatives": False,
    }
    values.update(overrides)
    return RiskLimits(**values)


def candidate(**overrides) -> TradeCandidate:
    values = {
        "instrument_id": "TEST",
        "asset_class": AssetClass.EQUITY,
        "side": OrderSide.BUY,
        "quantity": 2,
        "reference_price": 100,
        "multiplier": 1,
        "spread_bps": 5,
        "quote_age_seconds": 1,
        "portfolio_notional_after": 200,
        "daily_loss_after": 0,
        "leverage_after": 1,
        "evidence_count": 1,
    }
    values.update(overrides)
    return TradeCandidate(**values)


def test_evidence_store_shares_findings_and_flags_conflict():
    store = SharedEvidenceStore()
    store.publish(AgentFinding.create(
        agent_id="trend", role="technical", instrument_id="TEST",
        asset_class=AssetClass.EQUITY, timeframe="5m", thesis="bullish trend",
        confidence=0.7, evidence=[evidence()],
    ))
    store.publish(AgentFinding.create(
        agent_id="risk", role="adversarial", instrument_id="TEST",
        asset_class=AssetClass.EQUITY, timeframe="5m", thesis="bearish risk case",
        confidence=0.6, evidence=[evidence("news-2")],
    ))
    assert len(store.findings_for("TEST")) == 2
    assert store.evidence_conflicts("TEST") is True


def test_agent_confidence_must_be_finite_and_bounded():
    with pytest.raises(ValueError):
        AgentFinding.create(
            agent_id="agent", role="research", instrument_id="TEST",
            asset_class=AssetClass.EQUITY, timeframe="1d", thesis="neutral",
            confidence=math.nan, evidence=[evidence()],
        )
    with pytest.raises(ValueError):
        AgentFinding.create(
            agent_id="agent", role="research", instrument_id="TEST",
            asset_class=AssetClass.EQUITY, timeframe="1d", thesis="neutral",
            confidence=1.1, evidence=[evidence()],
        )
    with pytest.raises(ValueError):
        AgentFinding.create(
            agent_id="agent", role="research", instrument_id="TEST",
            asset_class=AssetClass.EQUITY, timeframe="1d", thesis="neutral",
            confidence="not-a-number", evidence=[evidence()],
        )
    with pytest.raises(ValueError):
        AgentFinding.create(
            agent_id="agent", role="research", instrument_id="TEST",
            asset_class=AssetClass.EQUITY, timeframe="1d", thesis="neutral",
            confidence=True, evidence=[evidence()],
        )


def test_candidate_is_approved_for_simulation_when_all_checks_pass():
    result = evaluate_candidate(candidate(), limits())
    assert result.allowed is True
    assert result.state is OrderState.APPROVED_FOR_SIMULATION
    assert result.reasons == ()


@pytest.mark.parametrize(
    ("candidate_overrides", "limits_overrides", "reason"),
    [
        ({"quantity": 100}, {}, "order notional"),
        ({"spread_bps": None}, {}, "spread is missing"),
        ({"quote_age_seconds": 30}, {}, "stale"),
        ({"evidence_count": 0}, {}, "evidence-backed"),
        ({"conflicting_agent_findings": True}, {}, "findings conflict"),
        ({"daily_loss_after": 501}, {}, "daily loss"),
        ({"leverage_after": 2}, {}, "leverage"),
        ({"reference_price": math.inf}, {}, "finite"),
    ],
)
def test_candidate_fails_closed_on_invalid_or_over_limit_inputs(
    candidate_overrides, limits_overrides, reason
):
    result = evaluate_candidate(candidate(**candidate_overrides), limits(**limits_overrides))
    assert result.allowed is False
    assert result.state is OrderState.RISK_REJECTED
    assert any(reason in item for item in result.reasons)


def test_derivatives_require_explicit_policy_and_contract_risk_metadata():
    result = evaluate_candidate(
        candidate(asset_class=AssetClass.OPTION),
        limits(),
    )
    assert result.allowed is False
    assert any("derivatives are disabled" in item for item in result.reasons)
    assert any("contract metadata" in item for item in result.reasons)
    assert any("bounded maximum loss" in item for item in result.reasons)


def test_derivatives_can_only_pass_with_explicitly_enabled_policy_and_metadata():
    result = evaluate_candidate(
        candidate(
            asset_class=AssetClass.FUTURE,
            has_valid_contract_metadata=True,
            has_bounded_max_loss=True,
            estimated_max_loss=100,
        ),
        limits(allow_derivatives=True),
    )
    assert result.allowed is True


def test_invalid_risk_limit_configuration_is_rejected():
    with pytest.raises(ValueError, match="max_order_notional"):
        evaluate_candidate(candidate(), limits(max_order_notional=float("nan")))


def test_unknown_order_state_must_be_reconciled_not_blindly_retried():
    validate_order_transition(OrderState.SUBMITTED, OrderState.UNKNOWN)
    validate_order_transition(OrderState.UNKNOWN, OrderState.FILLED)
    validate_order_transition(OrderState.FILLED, OrderState.RECONCILED)
    with pytest.raises(ValueError, match="invalid order state transition"):
        validate_order_transition(OrderState.SUBMITTED, OrderState.SUBMITTED)


def test_live_execution_is_unconditionally_disabled_in_this_phase():
    assert live_execution_enabled({"FINAI_LIVE_TRADING_ENABLED": "true"}) is False
    assert live_execution_enabled({"FINAI_LIVE_TRADING_ENABLED": "false"}) is False
    assert live_execution_enabled({}) is False
