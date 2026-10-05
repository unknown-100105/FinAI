"""Research-only control mechanisms for FinAI patent experiments.

This module deliberately does not authorize, execute, route, or approve live
financial transactions. It provides experiment-state controls that can be
benchmarked alongside the causal-feasibility research stack.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import IntEnum
import hashlib
import json
from typing import Any, Mapping, Sequence


def _now() -> float:
    return datetime.now(timezone.utc).timestamp()


def _canonical(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def digest(value: Any) -> str:
    return hashlib.sha256(_canonical(value).encode("utf-8")).hexdigest()


class ResearchMode(IntEnum):
    QUARANTINE = 0
    SAFE = 1
    RESTRICTED = 2
    FULL = 3


@dataclass(frozen=True)
class EvidenceItem:
    evidence_id: str
    observed_at: float
    valid_for_seconds: float
    confidence: float = 1.0

    def __post_init__(self) -> None:
        if not self.evidence_id:
            raise ValueError("evidence_id must be non-empty")
        if self.valid_for_seconds <= 0:
            raise ValueError("valid_for_seconds must be positive")
        if not 0 <= self.confidence <= 1:
            raise ValueError("confidence must be between 0 and 1")

    def fresh(self, now: float | None = None) -> bool:
        current = _now() if now is None else float(now)
        return current <= self.observed_at + self.valid_for_seconds


@dataclass(frozen=True)
class EvidenceState:
    fresh_count: int
    stale_count: int
    conflict_count: int
    minimum_confidence: float
    evidence_digest: str

    @property
    def is_fresh(self) -> bool:
        return self.stale_count == 0

    @property
    def is_conflicted(self) -> bool:
        return self.conflict_count > 0


def evaluate_evidence(
    items: Sequence[EvidenceItem],
    *,
    now: float | None = None,
    conflict_pairs: Sequence[tuple[str, str]] = (),
) -> EvidenceState:
    if not items:
        raise ValueError("at least one evidence item is required")
    ids = {item.evidence_id for item in items}
    unknown = [pair for pair in conflict_pairs if pair[0] not in ids or pair[1] not in ids]
    if unknown:
        raise ValueError(f"unknown evidence in conflict pairs: {unknown}")

    fresh_count = sum(item.fresh(now) for item in items)
    payload = {
        "items": [
            {
                "id": item.evidence_id,
                "observed_at": item.observed_at,
                "valid_for_seconds": item.valid_for_seconds,
                "confidence": item.confidence,
            }
            for item in sorted(items, key=lambda x: x.evidence_id)
        ],
        "conflicts": sorted(tuple(pair) for pair in conflict_pairs),
    }
    return EvidenceState(
        fresh_count=fresh_count,
        stale_count=len(items) - fresh_count,
        conflict_count=len(conflict_pairs),
        minimum_confidence=min(item.confidence for item in items),
        evidence_digest=digest(payload),
    )


@dataclass(frozen=True)
class ResearchCapabilityEnvelope:
    """Experimental capability state; never connect this directly to execution."""

    mode: ResearchMode
    uncertainty: float
    disagreement: float
    evidence_digest: str
    allowed_operations: tuple[str, ...]
    reasons: tuple[str, ...] = ()

    def as_dict(self) -> dict[str, Any]:
        return {
            "mode": self.mode.name.lower(),
            "uncertainty": self.uncertainty,
            "disagreement": self.disagreement,
            "evidence_digest": self.evidence_digest,
            "allowed_operations": list(self.allowed_operations),
            "reasons": list(self.reasons),
        }


def derive_research_capability(
    *,
    uncertainty: float,
    disagreement: float,
    evidence: EvidenceState,
    operations: Sequence[str],
) -> ResearchCapabilityEnvelope:
    if not 0 <= uncertainty <= 1 or not 0 <= disagreement <= 1:
        raise ValueError("uncertainty and disagreement must be between 0 and 1")

    ops = tuple(dict.fromkeys(str(x) for x in operations))
    reasons: list[str] = []
    stress = max(uncertainty, disagreement)

    if evidence.is_conflicted:
        mode = ResearchMode.SAFE
        reasons.append("evidence_conflict")
        ops = ops[:1]
    elif not evidence.is_fresh:
        mode = ResearchMode.RESTRICTED
        reasons.append("stale_evidence")
    elif evidence.minimum_confidence < 0.70:
        mode = ResearchMode.RESTRICTED
        reasons.append("low_evidence_confidence")
    elif stress > 0.60:
        mode = ResearchMode.QUARANTINE
        reasons.append("high_uncertainty_or_model_disagreement")
        ops = ()
    elif stress > 0.35:
        mode = ResearchMode.SAFE
        reasons.append("moderate_uncertainty_or_model_disagreement")
        ops = ops[:1]
    elif stress > 0.15:
        mode = ResearchMode.RESTRICTED
        reasons.append("elevated_uncertainty_or_model_disagreement")
    else:
        mode = ResearchMode.FULL

    return ResearchCapabilityEnvelope(
        mode=mode,
        uncertainty=uncertainty,
        disagreement=disagreement,
        evidence_digest=evidence.evidence_digest,
        allowed_operations=ops,
        reasons=tuple(reasons),
    )


@dataclass(frozen=True)
class EvaluationLease:
    """Time/state lease for a research evaluation artifact."""

    experiment_id: str
    state_digest: str
    model_version: str
    policy_version: str
    evidence_digest: str
    issued_at: float
    expires_at: float
    lease_digest: str

    @classmethod
    def issue(
        cls,
        *,
        experiment_id: str,
        state: Mapping[str, Any],
        model_version: str,
        policy_version: str,
        evidence_digest: str,
        ttl_seconds: float = 300.0,
        issued_at: float | None = None,
    ) -> "EvaluationLease":
        if not experiment_id or not model_version or not policy_version:
            raise ValueError("experiment_id, model_version and policy_version are required")
        if ttl_seconds <= 0:
            raise ValueError("ttl_seconds must be positive")
        issued = _now() if issued_at is None else float(issued_at)
        payload = {
            "experiment_id": experiment_id,
            "state_digest": digest(state),
            "model_version": model_version,
            "policy_version": policy_version,
            "evidence_digest": evidence_digest,
            "issued_at": issued,
            "expires_at": issued + ttl_seconds,
        }
        return cls(**payload, lease_digest=digest(payload))

    def validate(
        self,
        *,
        state: Mapping[str, Any],
        model_version: str,
        policy_version: str,
        evidence_digest: str,
        now: float | None = None,
    ) -> dict[str, Any]:
        current = _now() if now is None else float(now)
        reasons: list[str] = []
        if current > self.expires_at:
            reasons.append("lease_expired")
        if digest(state) != self.state_digest:
            reasons.append("state_changed")
        if model_version != self.model_version:
            reasons.append("model_version_changed")
        if policy_version != self.policy_version:
            reasons.append("policy_version_changed")
        if evidence_digest != self.evidence_digest:
            reasons.append("evidence_changed")
        payload = {
            "experiment_id": self.experiment_id,
            "state_digest": self.state_digest,
            "model_version": self.model_version,
            "policy_version": self.policy_version,
            "evidence_digest": self.evidence_digest,
            "issued_at": self.issued_at,
            "expires_at": self.expires_at,
        }
        if digest(payload) != self.lease_digest:
            reasons.append("lease_integrity_failure")
        return {
            "valid": not reasons,
            "experiment_id": self.experiment_id,
            "reasons": reasons,
        }


def derive_safe_mode(
    *,
    model_available: bool,
    evidence_available: bool,
    graph_valid: bool,
    operations: Sequence[str],
) -> ResearchMode:
    if not graph_valid:
        return ResearchMode.QUARANTINE
    if not model_available or not evidence_available:
        return ResearchMode.SAFE
    if not operations:
        return ResearchMode.RESTRICTED
    return ResearchMode.FULL


def build_experiment_proof(
    *,
    experiment_id: str,
    input_digest: str,
    evidence: EvidenceState,
    capability: ResearchCapabilityEnvelope,
    lease: EvaluationLease,
    metrics: Mapping[str, Any],
) -> dict[str, Any]:
    payload = {
        "experiment_id": experiment_id,
        "input_digest": input_digest,
        "evidence": {
            "fresh_count": evidence.fresh_count,
            "stale_count": evidence.stale_count,
            "conflict_count": evidence.conflict_count,
            "minimum_confidence": evidence.minimum_confidence,
            "evidence_digest": evidence.evidence_digest,
        },
        "capability": capability.as_dict(),
        "lease": {
            "experiment_id": lease.experiment_id,
            "state_digest": lease.state_digest,
            "model_version": lease.model_version,
            "policy_version": lease.policy_version,
            "evidence_digest": lease.evidence_digest,
            "issued_at": lease.issued_at,
            "expires_at": lease.expires_at,
            "lease_digest": lease.lease_digest,
        },
        "metrics": dict(metrics),
    }
    return {
        "status": "RESEARCH_EXPERIMENT_PROOF_READY",
        "proof_digest": digest(payload),
        "payload": payload,
    }
