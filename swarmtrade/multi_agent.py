"""Fail-closed multi-agent research coordination and execution safety primitives.

This module does not connect to a broker or submit orders. Research agents exchange
structured, provenance-bearing evidence; a deterministic gate validates candidate
intents before they can be handed to a future execution adapter.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
import math
from typing import Any, Iterable, Mapping
from uuid import uuid4


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class AssetClass(str, Enum):
    EQUITY = "equity"
    FUTURE = "future"
    OPTION = "option"
    FX = "fx"
    CRYPTO_SPOT = "crypto_spot"
    CRYPTO_DERIVATIVE = "crypto_derivative"
    COMMODITY = "commodity"


class OrderSide(str, Enum):
    BUY = "buy"
    SELL = "sell"


class OrderState(str, Enum):
    CANDIDATE = "candidate"
    RISK_REJECTED = "risk_rejected"
    APPROVED_FOR_SIMULATION = "approved_for_simulation"
    SUBMITTED = "submitted"
    ACKNOWLEDGED = "acknowledged"
    PARTIALLY_FILLED = "partially_filled"
    FILLED = "filled"
    REJECTED = "rejected"
    CANCELLED = "cancelled"
    UNKNOWN = "unknown"
    RECONCILED = "reconciled"


@dataclass(frozen=True)
class EvidenceItem:
    source_id: str
    source_uri: str
    observed_at: str
    published_at: str | None
    summary: str
    data_fingerprint: str | None = None


@dataclass(frozen=True)
class AgentFinding:
    run_id: str
    agent_id: str
    role: str
    instrument_id: str
    asset_class: AssetClass
    timeframe: str
    created_at: str
    thesis: str
    confidence: float
    evidence: tuple[EvidenceItem, ...] = ()
    risks: tuple[str, ...] = ()
    invalidation_conditions: tuple[str, ...] = ()
    abstain_reason: str | None = None

    @classmethod
    def create(
        cls,
        *,
        agent_id: str,
        role: str,
        instrument_id: str,
        asset_class: AssetClass,
        timeframe: str,
        thesis: str,
        confidence: float,
        evidence: Iterable[EvidenceItem] = (),
        risks: Iterable[str] = (),
        invalidation_conditions: Iterable[str] = (),
        abstain_reason: str | None = None,
    ) -> "AgentFinding":
        if not agent_id.strip() or not role.strip() or not instrument_id.strip():
            raise ValueError("agent_id, role, and instrument_id are required")
        if not math.isfinite(confidence) or not 0.0 <= confidence <= 1.0:
            raise ValueError("confidence must be finite and between 0 and 1")
        return cls(
            run_id=str(uuid4()),
            agent_id=agent_id.strip(),
            role=role.strip(),
            instrument_id=instrument_id.strip(),
            asset_class=AssetClass(asset_class),
            timeframe=timeframe.strip(),
            created_at=utc_now_iso(),
            thesis=thesis.strip(),
            confidence=confidence,
            evidence=tuple(evidence),
            risks=tuple(risks),
            invalidation_conditions=tuple(invalidation_conditions),
            abstain_reason=abstain_reason,
        )


class SharedEvidenceStore:
    """In-memory, per-run evidence exchange; persistence can be added behind this API."""

    def __init__(self) -> None:
        self._findings: dict[str, list[AgentFinding]] = {}

    def publish(self, finding: AgentFinding) -> None:
        if not finding.evidence and not finding.abstain_reason:
            raise ValueError("finding must include evidence or an explicit abstain_reason")
        self._findings.setdefault(finding.instrument_id, []).append(finding)

    def findings_for(self, instrument_id: str) -> tuple[AgentFinding, ...]:
        return tuple(self._findings.get(instrument_id, ()))

    def evidence_conflicts(self, instrument_id: str) -> bool:
        """Flag disagreement in signed directional theses; never resolve by majority alone."""
        directional = {
            "bullish" if "bullish" in f.thesis.casefold() or "buy" in f.thesis.casefold()
            else "bearish" if "bearish" in f.thesis.casefold() or "sell" in f.thesis.casefold()
            else "neutral"
            for f in self.findings_for(instrument_id)
            if f.abstain_reason is None
        }
        return "bullish" in directional and "bearish" in directional

    def export(self, instrument_id: str) -> list[dict[str, Any]]:
        return [asdict(item) for item in self.findings_for(instrument_id)]


@dataclass(frozen=True)
class RiskLimits:
    max_order_notional: float
    max_portfolio_notional: float
    max_daily_loss: float
    max_leverage: float = 1.0
    max_spread_bps: float = 50.0
    max_quote_age_seconds: float = 5.0
    allow_derivatives: bool = False

    def validate(self) -> None:
        for name in ("max_order_notional", "max_portfolio_notional", "max_daily_loss",
                     "max_leverage", "max_spread_bps", "max_quote_age_seconds"):
            value = getattr(self, name)
            if not math.isfinite(value) or value <= 0:
                raise ValueError(f"{name} must be finite and positive")


@dataclass(frozen=True)
class TradeCandidate:
    instrument_id: str
    asset_class: AssetClass
    side: OrderSide
    quantity: float
    reference_price: float
    multiplier: float = 1.0
    estimated_max_loss: float | None = None
    spread_bps: float | None = None
    quote_age_seconds: float | None = None
    portfolio_notional_after: float = 0.0
    daily_loss_after: float = 0.0
    leverage_after: float = 1.0
    has_valid_contract_metadata: bool = False
    has_bounded_max_loss: bool = False
    evidence_count: int = 0
    conflicting_agent_findings: bool = False


@dataclass(frozen=True)
class RiskDecision:
    allowed: bool
    state: OrderState
    reasons: tuple[str, ...]
    checked_at: str = field(default_factory=utc_now_iso)


def evaluate_candidate(candidate: TradeCandidate, limits: RiskLimits) -> RiskDecision:
    """Fail-closed deterministic checks; passing means simulation approval only."""
    limits.validate()
    reasons: list[str] = []

    numeric = {
        "quantity": candidate.quantity,
        "reference_price": candidate.reference_price,
        "multiplier": candidate.multiplier,
        "portfolio_notional_after": candidate.portfolio_notional_after,
        "daily_loss_after": candidate.daily_loss_after,
        "leverage_after": candidate.leverage_after,
    }
    for name, value in numeric.items():
        if not math.isfinite(value):
            reasons.append(f"{name} must be finite")
    if any(value <= 0 for key, value in numeric.items() if key in {
        "quantity", "reference_price", "multiplier", "leverage_after"
    }):
        reasons.append("quantity, reference_price, multiplier and leverage must be positive")

    notional = candidate.quantity * candidate.reference_price * candidate.multiplier
    if not math.isfinite(notional) or notional <= 0:
        reasons.append("computed order notional is invalid")
    elif notional > limits.max_order_notional:
        reasons.append("order notional exceeds configured limit")

    if candidate.portfolio_notional_after < 0 or candidate.portfolio_notional_after > limits.max_portfolio_notional:
        reasons.append("portfolio notional is outside configured limit")
    if candidate.daily_loss_after < 0 or candidate.daily_loss_after > limits.max_daily_loss:
        reasons.append("daily loss is outside configured limit")
    if candidate.leverage_after > limits.max_leverage:
        reasons.append("leverage exceeds configured limit")

    if candidate.spread_bps is None or not math.isfinite(candidate.spread_bps):
        reasons.append("spread is missing or invalid")
    elif candidate.spread_bps < 0 or candidate.spread_bps > limits.max_spread_bps:
        reasons.append("spread exceeds configured limit")

    if candidate.quote_age_seconds is None or not math.isfinite(candidate.quote_age_seconds):
        reasons.append("quote age is missing or invalid")
    elif candidate.quote_age_seconds < 0 or candidate.quote_age_seconds > limits.max_quote_age_seconds:
        reasons.append("quote is stale or timestamp is invalid")

    if candidate.evidence_count < 1:
        reasons.append("no evidence-backed agent finding")
    if candidate.conflicting_agent_findings:
        reasons.append("agent findings conflict; supervisor review required")

    if candidate.asset_class in {
        AssetClass.FUTURE, AssetClass.OPTION, AssetClass.CRYPTO_DERIVATIVE
    }:
        if not limits.allow_derivatives:
            reasons.append("derivatives are disabled by risk policy")
        if not candidate.has_valid_contract_metadata:
            reasons.append("validated contract metadata is required")
        if not candidate.has_bounded_max_loss or candidate.estimated_max_loss is None:
            reasons.append("bounded maximum loss is required for derivatives")
        elif not math.isfinite(candidate.estimated_max_loss) or candidate.estimated_max_loss <= 0:
            reasons.append("estimated maximum loss must be finite and positive")

    if reasons:
        return RiskDecision(False, OrderState.RISK_REJECTED, tuple(dict.fromkeys(reasons)))
    return RiskDecision(True, OrderState.APPROVED_FOR_SIMULATION, ())


@dataclass(frozen=True)
class OrderUpdate:
    order_id: str
    state: OrderState
    filled_quantity: float = 0.0
    average_fill_price: float | None = None
    broker_status: str | None = None


_ALLOWED_TRANSITIONS: Mapping[OrderState, set[OrderState]] = {
    OrderState.CANDIDATE: {OrderState.RISK_REJECTED, OrderState.APPROVED_FOR_SIMULATION},
    OrderState.APPROVED_FOR_SIMULATION: {OrderState.SUBMITTED, OrderState.CANCELLED},
    OrderState.SUBMITTED: {OrderState.ACKNOWLEDGED, OrderState.REJECTED, OrderState.UNKNOWN},
    OrderState.ACKNOWLEDGED: {OrderState.PARTIALLY_FILLED, OrderState.FILLED, OrderState.CANCELLED, OrderState.REJECTED, OrderState.UNKNOWN},
    OrderState.PARTIALLY_FILLED: {OrderState.PARTIALLY_FILLED, OrderState.FILLED, OrderState.CANCELLED, OrderState.UNKNOWN},
    OrderState.UNKNOWN: {OrderState.ACKNOWLEDGED, OrderState.PARTIALLY_FILLED, OrderState.FILLED, OrderState.REJECTED, OrderState.CANCELLED, OrderState.RECONCILED},
    OrderState.FILLED: {OrderState.RECONCILED},
    OrderState.REJECTED: {OrderState.RECONCILED},
    OrderState.CANCELLED: {OrderState.RECONCILED},
    OrderState.RISK_REJECTED: set(),
    OrderState.RECONCILED: set(),
}


def validate_order_transition(previous: OrderState, next_state: OrderState) -> None:
    """Reject impossible state transitions; UNKNOWN must be queried, never blindly retried."""
    if next_state not in _ALLOWED_TRANSITIONS.get(previous, set()):
        raise ValueError(f"invalid order state transition: {previous.value} -> {next_state.value}")


def live_execution_enabled(environment: Mapping[str, str] | None = None) -> bool:
    """Always fail closed in this phase; no live broker adapter is implemented here."""
    values = environment or {}
    return values.get("FINAI_LIVE_TRADING_ENABLED", "").strip().casefold() == "true" and False
