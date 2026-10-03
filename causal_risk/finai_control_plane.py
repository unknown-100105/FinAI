"""Research control-plane mechanisms for FinAI's financial execution safety.

This module implements concrete, testable research mechanisms around:
- risk-capability envelopes;
- stateful risk budgets;
- state-bound decision leases;
- evidence freshness/conflict assessment;
- deterministic safe-mode degradation;
- machine-verifiable decision proofs.

The module is intentionally isolated from production investment/payment logic.
It uses only the Python standard library so the research mechanism can be
exercised without adding runtime dependencies.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import IntEnum
import hashlib
import hmac
import json
import threading
from typing import Any, Mapping, Sequence


def _utc_timestamp(value: datetime | None = None) -> float:
    stamp = value or datetime.now(timezone.utc)
    if stamp.tzinfo is None:
        stamp = stamp.replace(tzinfo=timezone.utc)
    return float(stamp.timestamp())


def _canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _digest(value: Any) -> str:
    return hashlib.sha256(_canonical_json(value).encode("utf-8")).hexdigest()


class CapabilityLevel(IntEnum):
    """Ordered financial-execution capability state."""

    QUARANTINE = 0
    SAFE = 1
    RESTRICTED = 2
    FULL = 3


@dataclass(frozen=True)
class EvidenceRecord:
    """Point-in-time evidence item with explicit freshness semantics."""

    evidence_id: str
    source: str
    observed_at: float
    valid_for_seconds: float
    confidence: float = 1.0
    integrity_hash: str = ""

    def __post_init__(self) -> None:
        if not self.evidence_id:
            raise ValueError("evidence_id must be non-empty")
        if not self.source:
            raise ValueError("source must be non-empty")
        if self.valid_for_seconds <= 0:
            raise ValueError("valid_for_seconds must be positive")
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence must be between 0 and 1")
        if not self.integrity_hash:
            object.__setattr__(
                self,
                "integrity_hash",
                _digest(
                    {
                        "evidence_id": self.evidence_id,
                        "source": self.source,
                        "observed_at": self.observed_at,
                        "valid_for_seconds": self.valid_for_seconds,
                    }
                ),
            )

    def is_fresh(self, now: float | None = None) -> bool:
        current = _utc_timestamp() if now is None else float(now)
        return current <= self.observed_at + self.valid_for_seconds

    def as_dict(self) -> dict[str, Any]:
        return {
            "evidence_id": self.evidence_id,
            "source": self.source,
            "observed_at": self.observed_at,
            "valid_for_seconds": self.valid_for_seconds,
            "confidence": self.confidence,
            "integrity_hash": self.integrity_hash,
        }


@dataclass(frozen=True)
class EvidenceAssessment:
    fresh_count: int
    stale_count: int
    conflict_count: int
    minimum_confidence: float
    digest: str
    reasons: tuple[str, ...] = ()

    @property
    def all_fresh(self) -> bool:
        return self.stale_count == 0

    @property
    def has_conflict(self) -> bool:
        return self.conflict_count > 0

    def as_dict(self) -> dict[str, Any]:
        return {
            "fresh_count": self.fresh_count,
            "stale_count": self.stale_count,
            "conflict_count": self.conflict_count,
            "minimum_confidence": self.minimum_confidence,
            "digest": self.digest,
            "all_fresh": self.all_fresh,
            "has_conflict": self.has_conflict,
            "reasons": list(self.reasons),
        }


def assess_evidence(
    records: Sequence[EvidenceRecord],
    *,
    now: float | None = None,
    conflict_pairs: Sequence[tuple[str, str]] = (),
) -> EvidenceAssessment:
    if not records:
        raise ValueError("at least one evidence record is required")
    by_id = {record.evidence_id: record for record in records}
    unknown_pairs = [
        pair for pair in conflict_pairs
        if pair[0] not in by_id or pair[1] not in by_id
    ]
    if unknown_pairs:
        raise ValueError(f"conflict_pairs reference unknown evidence: {unknown_pairs}")

    fresh = sum(record.is_fresh(now) for record in records)
    stale = len(records) - fresh
    minimum_confidence = min(record.confidence for record in records)
    reasons: list[str] = []
    if stale:
        reasons.append(f"{stale} evidence item(s) are stale")
    if conflict_pairs:
        reasons.append(f"{len(conflict_pairs)} evidence conflict(s) declared")

    digest = _digest({
        "records": [record.as_dict() for record in sorted(records, key=lambda item: item.evidence_id)],
        "conflict_pairs": sorted(tuple(pair) for pair in conflict_pairs),
    })
    return EvidenceAssessment(
        fresh_count=fresh,
        stale_count=stale,
        conflict_count=len(conflict_pairs),
        minimum_confidence=minimum_confidence,
        digest=digest,
        reasons=tuple(reasons),
    )


@dataclass(frozen=True)
class RiskCapabilityEnvelope:
    """Machine-readable execution envelope derived from risk state."""

    level: CapabilityLevel
    maximum_amount: float
    allowed_rails: tuple[str, ...]
    allowed_operations: tuple[str, ...]
    verification_required: bool
    model_uncertainty: float
    model_disagreement: float
    evidence_digest: str
    reasons: tuple[str, ...] = ()

    def permits(
        self,
        *,
        amount: float,
        rail: str,
        operation: str,
        verified: bool = False,
    ) -> bool:
        if amount < 0:
            return False
        if amount > self.maximum_amount:
            return False
        if rail not in self.allowed_rails or operation not in self.allowed_operations:
            return False
        if self.verification_required and not verified:
            return False
        return self.level > CapabilityLevel.QUARANTINE

    def as_dict(self) -> dict[str, Any]:
        return {
            "level": self.level.name.lower(),
            "maximum_amount": self.maximum_amount,
            "allowed_rails": list(self.allowed_rails),
            "allowed_operations": list(self.allowed_operations),
            "verification_required": self.verification_required,
            "model_uncertainty": self.model_uncertainty,
            "model_disagreement": self.model_disagreement,
            "evidence_digest": self.evidence_digest,
            "reasons": list(self.reasons),
        }


def build_risk_capability_envelope(
    *,
    base_amount_limit: float,
    permitted_rails: Sequence[str],
    permitted_operations: Sequence[str],
    model_uncertainty: float,
    model_disagreement: float,
    evidence: EvidenceAssessment,
    minimum_confidence: float = 0.70,
) -> RiskCapabilityEnvelope:
    """Convert uncertainty/evidence state into a bounded capability set.

    This is deliberately a control-state mechanism rather than a scalar
    approve/deny score. Thresholds are research defaults and must be calibrated
    against domain-specific validation data before authoritative use.
    """
    if base_amount_limit < 0:
        raise ValueError("base_amount_limit must be non-negative")
    if not 0.0 <= model_uncertainty <= 1.0:
        raise ValueError("model_uncertainty must be between 0 and 1")
    if not 0.0 <= model_disagreement <= 1.0:
        raise ValueError("model_disagreement must be between 0 and 1")
    if not 0.0 < minimum_confidence <= 1.0:
        raise ValueError("minimum_confidence must be between 0 and 1")

    rails = tuple(dict.fromkeys(str(value) for value in permitted_rails))
    operations = tuple(dict.fromkeys(str(value) for value in permitted_operations))
    if not rails or not operations:
        raise ValueError("permitted_rails and permitted_operations must be non-empty")

    reasons: list[str] = []
    stress = max(model_uncertainty, model_disagreement)

    if evidence.has_conflict:
        level = CapabilityLevel.SAFE
        reasons.append("evidence conflict requires constrained capability")
    elif not evidence.all_fresh:
        level = min(CapabilityLevel.RESTRICTED, CapabilityLevel.SAFE)
        reasons.append("stale evidence constrains capability")
    elif evidence.minimum_confidence < minimum_confidence:
        level = CapabilityLevel.RESTRICTED
        reasons.append("minimum evidence confidence is below threshold")
    elif stress > 0.60:
        level = CapabilityLevel.QUARANTINE
        reasons.append("high model uncertainty/disagreement")
    elif stress > 0.35:
        level = CapabilityLevel.SAFE
        reasons.append("moderate model uncertainty/disagreement")
    elif stress > 0.15:
        level = CapabilityLevel.RESTRICTED
        reasons.append("elevated model uncertainty/disagreement")
    else:
        level = CapabilityLevel.FULL

    if level == CapabilityLevel.FULL:
        amount = base_amount_limit
        selected_rails = rails
        selected_operations = operations
        verification_required = False
    elif level == CapabilityLevel.RESTRICTED:
        amount = base_amount_limit * 0.50
        selected_rails = rails
        selected_operations = operations
        verification_required = True
    elif level == CapabilityLevel.SAFE:
        amount = base_amount_limit * 0.10
        selected_rails = (rails[0],)
        selected_operations = (operations[0],)
        verification_required = True
    else:
        amount = 0.0
        selected_rails = ()
        selected_operations = ()
        verification_required = True

    return RiskCapabilityEnvelope(
        level=level,
        maximum_amount=round(amount, 8),
        allowed_rails=selected_rails,
        allowed_operations=selected_operations,
        verification_required=verification_required,
        model_uncertainty=model_uncertainty,
        model_disagreement=model_disagreement,
        evidence_digest=evidence.digest,
        reasons=tuple(reasons),
    )


@dataclass
class RiskBudgetLedger:
    """Thread-safe, stateful exposure budget with idempotent debits."""

    initial_budget: float
    _balances: dict[str, float] = field(default_factory=dict, init=False)
    _transactions: dict[str, tuple[str, float]] = field(default_factory=dict, init=False)
    _lock: threading.Lock = field(default_factory=threading.Lock, init=False, repr=False)

    def __post_init__(self) -> None:
        if self.initial_budget < 0:
            raise ValueError("initial_budget must be non-negative")

    def balance(self, subject: str) -> float:
        if not subject:
            raise ValueError("subject must be non-empty")
        with self._lock:
            return self._balances.get(subject, self.initial_budget)

    def debit(self, subject: str, transaction_id: str, cost: float) -> dict[str, Any]:
        if not subject or not transaction_id:
            raise ValueError("subject and transaction_id must be non-empty")
        if cost < 0:
            raise ValueError("cost must be non-negative")
        with self._lock:
            existing = self._transactions.get(transaction_id)
            if existing is not None:
                existing_subject, existing_cost = existing
                if existing_subject != subject or existing_cost != cost:
                    raise ValueError("transaction_id already exists with different subject/cost")
                return {
                    "status": "IDEMPOTENT_REPLAY",
                    "subject": subject,
                    "transaction_id": transaction_id,
                    "cost": cost,
                    "balance": self._balances.get(subject, self.initial_budget),
                }

            current = self._balances.get(subject, self.initial_budget)
            if cost > current:
                return {
                    "status": "REJECTED_INSUFFICIENT_RISK_BUDGET",
                    "subject": subject,
                    "transaction_id": transaction_id,
                    "cost": cost,
                    "balance": current,
                }

            remaining = round(current - cost, 8)
            self._balances[subject] = remaining
            self._transactions[transaction_id] = (subject, cost)
            return {
                "status": "RISK_BUDGET_DEBITED",
                "subject": subject,
                "transaction_id": transaction_id,
                "cost": cost,
                "balance": remaining,
            }

    def replenish(self, subject: str, amount: float, *, reason: str = "validated_settlement") -> dict[str, Any]:
        if not subject:
            raise ValueError("subject must be non-empty")
        if amount < 0:
            raise ValueError("amount must be non-negative")
        with self._lock:
            current = self._balances.get(subject, self.initial_budget)
            updated = round(current + amount, 8)
            self._balances[subject] = updated
            return {
                "status": "RISK_BUDGET_REPLENISHED",
                "subject": subject,
                "amount": amount,
                "balance": updated,
                "reason": reason,
            }


@dataclass(frozen=True)
class DecisionLease:
    """Time- and state-bound authorization artifact."""

    transaction_id: str
    transaction_digest: str
    model_version: str
    policy_version: str
    evidence_digest: str
    capability_digest: str
    issued_at: float
    expires_at: float
    integrity_digest: str
    signature: str = ""

    @classmethod
    def issue(
        cls,
        *,
        transaction_id: str,
        transaction_state: Mapping[str, Any],
        model_version: str,
        policy_version: str,
        evidence_digest: str,
        capability: RiskCapabilityEnvelope,
        ttl_seconds: float = 60.0,
        signing_key: bytes | None = None,
        issued_at: float | None = None,
    ) -> "DecisionLease":
        if not transaction_id or not model_version or not policy_version:
            raise ValueError("transaction_id, model_version and policy_version are required")
        if ttl_seconds <= 0:
            raise ValueError("ttl_seconds must be positive")
        issued = _utc_timestamp() if issued_at is None else float(issued_at)
        transaction_digest = _digest(transaction_state)
        capability_digest = _digest(capability.as_dict())
        payload = {
            "transaction_id": transaction_id,
            "transaction_digest": transaction_digest,
            "model_version": model_version,
            "policy_version": policy_version,
            "evidence_digest": evidence_digest,
            "capability_digest": capability_digest,
            "issued_at": issued,
            "expires_at": issued + ttl_seconds,
        }
        integrity_digest = _digest(payload)
        signature = (
            hmac.new(signing_key, integrity_digest.encode("ascii"), hashlib.sha256).hexdigest()
            if signing_key
            else ""
        )
        return cls(
            transaction_id=transaction_id,
            transaction_digest=transaction_digest,
            model_version=model_version,
            policy_version=policy_version,
            evidence_digest=evidence_digest,
            capability_digest=capability_digest,
            issued_at=issued,
            expires_at=issued + ttl_seconds,
            integrity_digest=integrity_digest,
            signature=signature,
        )

    def validate(
        self,
        *,
        transaction_state: Mapping[str, Any],
        model_version: str,
        policy_version: str,
        evidence_digest: str,
        capability: RiskCapabilityEnvelope,
        now: float | None = None,
        signing_key: bytes | None = None,
    ) -> dict[str, Any]:
        current = _utc_timestamp() if now is None else float(now)
        reasons: list[str] = []
        if current > self.expires_at:
            reasons.append("decision lease expired")
        if self.transaction_digest != _digest(transaction_state):
            reasons.append("transaction state changed")
        if self.model_version != model_version:
            reasons.append("model version changed")
        if self.policy_version != policy_version:
            reasons.append("policy version changed")
        if self.evidence_digest != evidence_digest:
            reasons.append("evidence state changed")
        if self.capability_digest != _digest(capability.as_dict()):
            reasons.append("capability envelope changed")
        if signing_key:
            expected = hmac.new(
                signing_key,
                self.integrity_digest.encode("ascii"),
                hashlib.sha256,
            ).hexdigest()
            if not hmac.compare_digest(expected, self.signature):
                reasons.append("decision lease signature invalid")
        return {
            "valid": not reasons,
            "reasons": reasons,
            "transaction_id": self.transaction_id,
            "expires_at": self.expires_at,
        }

    def as_dict(self) -> dict[str, Any]:
        return {
            "transaction_id": self.transaction_id,
            "transaction_digest": self.transaction_digest,
            "model_version": self.model_version,
            "policy_version": self.policy_version,
            "evidence_digest": self.evidence_digest,
            "capability_digest": self.capability_digest,
            "issued_at": self.issued_at,
            "expires_at": self.expires_at,
            "integrity_digest": self.integrity_digest,
            "signature": self.signature,
        }


@dataclass(frozen=True)
class SafeModeState:
    level: CapabilityLevel
    reason_codes: tuple[str, ...]
    preserved_operations: tuple[str, ...]
    blocked_operations: tuple[str, ...]

    def as_dict(self) -> dict[str, Any]:
        return {
            "level": self.level.name.lower(),
            "reason_codes": list(self.reason_codes),
            "preserved_operations": list(self.preserved_operations),
            "blocked_operations": list(self.blocked_operations),
        }


def derive_safe_mode(
    *,
    model_available: bool,
    evidence_available: bool,
    network_available: bool,
    integrity_valid: bool,
    default_operations: Sequence[str],
) -> SafeModeState:
    """Deterministically degrade capabilities under partial failures."""
    operations = tuple(dict.fromkeys(str(value) for value in default_operations))
    reasons: list[str] = []
    if not model_available:
        reasons.append("MODEL_UNAVAILABLE")
    if not evidence_available:
        reasons.append("EVIDENCE_UNAVAILABLE")
    if not network_available:
        reasons.append("NETWORK_DEGRADED")
    if not integrity_valid:
        reasons.append("INTEGRITY_FAILURE")

    if not integrity_valid:
        level = CapabilityLevel.QUARANTINE
        preserved: tuple[str, ...] = ()
    elif not model_available or not evidence_available:
        level = CapabilityLevel.SAFE
        preserved = tuple(operations[:1])
    elif not network_available:
        level = CapabilityLevel.RESTRICTED
        preserved = tuple(operations)
    else:
        level = CapabilityLevel.FULL
        preserved = tuple(operations)

    blocked = tuple(value for value in operations if value not in preserved)
    return SafeModeState(
        level=level,
        reason_codes=tuple(reasons),
        preserved_operations=preserved,
        blocked_operations=blocked,
    )


def build_decision_proof(
    *,
    transaction_state: Mapping[str, Any],
    model_version: str,
    policy_version: str,
    evidence: EvidenceAssessment,
    capability: RiskCapabilityEnvelope,
    lease: DecisionLease,
    outcome: str,
) -> dict[str, Any]:
    """Build a reproducible proof artifact for a FinAI authorization decision."""
    payload = {
        "transaction_state": dict(transaction_state),
        "model_version": model_version,
        "policy_version": policy_version,
        "evidence": evidence.as_dict(),
        "capability": capability.as_dict(),
        "lease": lease.as_dict(),
        "outcome": outcome,
    }
    proof_digest = _digest(payload)
    return {
        "status": "DECISION_PROOF_READY",
        "proof_digest": proof_digest,
        "payload": payload,
    }
