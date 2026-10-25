"""Fail-closed candidate risk evaluation API. Simulation approval only; no broker calls."""
from typing import Literal

from fastapi import APIRouter
from pydantic import BaseModel, Field, field_validator

from swarmtrade.multi_agent import (
    AssetClass,
    OrderSide,
    RiskLimits,
    TradeCandidate,
    evaluate_candidate,
    live_execution_enabled,
)

router = APIRouter(prefix="/api/v1/swarmtrade/safety", tags=["swarmtrade-safety"])


class RiskLimitsRequest(BaseModel):
    max_order_notional: float = Field(default=5000, gt=0, allow_inf_nan=False)
    max_portfolio_notional: float = Field(default=20000, gt=0, allow_inf_nan=False)
    max_daily_loss: float = Field(default=500, gt=0, allow_inf_nan=False)
    max_leverage: float = Field(default=1, gt=0, le=30, allow_inf_nan=False)
    max_spread_bps: float = Field(default=25, gt=0, le=1000, allow_inf_nan=False)
    max_quote_age_seconds: float = Field(default=5, gt=0, le=3600, allow_inf_nan=False)
    allow_derivatives: bool = False


class CandidateRiskRequest(BaseModel):
    instrument_id: str = Field(..., min_length=1, max_length=128)
    asset_class: Literal["equity", "future", "option", "fx", "crypto_spot", "crypto_derivative", "commodity"] = "equity"
    side: Literal["buy", "sell"]
    quantity: float = Field(..., gt=0, allow_inf_nan=False)
    reference_price: float = Field(..., gt=0, allow_inf_nan=False)
    multiplier: float = Field(default=1, gt=0, allow_inf_nan=False)
    estimated_max_loss: float | None = Field(default=None, gt=0, allow_inf_nan=False)
    spread_bps: float | None = Field(default=None, ge=0, allow_inf_nan=False)
    quote_age_seconds: float | None = Field(default=None, ge=0, allow_inf_nan=False)
    portfolio_notional_after: float = Field(default=0, ge=0, allow_inf_nan=False)
    daily_loss_after: float = Field(default=0, ge=0, allow_inf_nan=False)
    leverage_after: float = Field(default=1, gt=0, allow_inf_nan=False)
    has_valid_contract_metadata: bool = False
    has_bounded_max_loss: bool = False
    evidence_count: int = Field(default=0, ge=0, le=10000)
    conflicting_agent_findings: bool = False
    limits: RiskLimitsRequest = Field(default_factory=RiskLimitsRequest)

    @field_validator("instrument_id")
    @classmethod
    def normalize_instrument(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("instrument_id must not be blank")
        return value


@router.get("/status")
def safety_status() -> dict:
    return {
        "service": "FinAI SwarmTrade deterministic safety gate",
        "status": "available",
        "approval_semantics": "simulation_only",
        "live_execution_enabled": live_execution_enabled(),
        "broker_connected": False,
        "order_submission_supported": False,
        "requires_fresh_quote_and_evidence": True,
        "derivatives_default": "disabled",
    }


@router.post("/evaluate")
def evaluate_candidate_risk(request: CandidateRiskRequest) -> dict:
    candidate = TradeCandidate(
        instrument_id=request.instrument_id,
        asset_class=AssetClass(request.asset_class),
        side=OrderSide(request.side),
        quantity=request.quantity,
        reference_price=request.reference_price,
        multiplier=request.multiplier,
        estimated_max_loss=request.estimated_max_loss,
        spread_bps=request.spread_bps,
        quote_age_seconds=request.quote_age_seconds,
        portfolio_notional_after=request.portfolio_notional_after,
        daily_loss_after=request.daily_loss_after,
        leverage_after=request.leverage_after,
        has_valid_contract_metadata=request.has_valid_contract_metadata,
        has_bounded_max_loss=request.has_bounded_max_loss,
        evidence_count=request.evidence_count,
        conflicting_agent_findings=request.conflicting_agent_findings,
    )
    limits = RiskLimits(**request.limits.model_dump())
    decision = evaluate_candidate(candidate, limits)
    return {
        "instrument_id": request.instrument_id,
        "allowed": decision.allowed,
        "state": decision.state.value,
        "reasons": list(decision.reasons),
        "checked_at": decision.checked_at,
        "approval_semantics": "simulation_only",
        "execution": {
            "live_execution_enabled": False,
            "broker_connected": False,
            "order_submitted": False,
            "fill_claimed": False,
        },
    }
