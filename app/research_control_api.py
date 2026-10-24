"""Research-only evidence gate, evaluation lease, and proof API.

Caller-provided evidence metadata is not independently verified by this service.
The outputs are experimental diagnostics, not investment recommendations or
authorization to place orders.
"""
from __future__ import annotations

from typing import Any, Dict, List, Tuple

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field, field_validator

from causal_risk.research_control_plane import (
    EvidenceItem,
    EvaluationLease,
    build_experiment_proof,
    derive_research_capability,
    digest,
    evaluate_evidence,
)

router = APIRouter(prefix="/api/v1/causal-risk/research-control", tags=["causal-risk-research-control"])
MAX_EVIDENCE_ITEMS = 32
MAX_OPERATIONS = 20
ALLOWED_RESEARCH_OPERATIONS = {
    "run_counterfactual", "run_benchmark", "inspect_retrieval",
    "generate_report", "evaluate_model", "compare_models",
    "calibrate_research_model", "inspect_causal_graph",
}


class EvidenceInput(BaseModel):
    evidence_id: str = Field(..., min_length=1, max_length=160)
    observed_at: float = Field(..., ge=0, allow_inf_nan=False)
    valid_for_seconds: float = Field(..., gt=0, le=31_536_000, allow_inf_nan=False)
    confidence: float = Field(default=1.0, ge=0, le=1, allow_inf_nan=False)

    @field_validator("evidence_id")
    @classmethod
    def strip_evidence_id(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("evidence_id must not be blank")
        return value


class ResearchControlRequest(BaseModel):
    experiment_id: str = Field(..., min_length=1, max_length=160)
    evidence: List[EvidenceInput] = Field(..., min_length=1, max_length=MAX_EVIDENCE_ITEMS)
    conflict_pairs: List[Tuple[str, str]] = Field(default_factory=list, max_length=100)
    uncertainty: float = Field(default=0.0, ge=0, le=1, allow_inf_nan=False)
    disagreement: float = Field(default=0.0, ge=0, le=1, allow_inf_nan=False)
    operations: List[str] = Field(default_factory=lambda: ["run_counterfactual"], max_length=MAX_OPERATIONS)
    state: Dict[str, Any] = Field(default_factory=dict)
    model_version: str = Field(..., min_length=1, max_length=128)
    policy_version: str = Field(..., min_length=1, max_length=128)
    ttl_seconds: float = Field(default=300.0, gt=0, le=3600, allow_inf_nan=False)
    metrics: Dict[str, Any] = Field(default_factory=dict)

    @field_validator("experiment_id", "model_version", "policy_version")
    @classmethod
    def strip_required_labels(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("identifier/version must not be blank")
        return value

    @field_validator("operations")
    @classmethod
    def restrict_research_operations(cls, value: List[str]) -> List[str]:
        normalized = list(dict.fromkeys(item.strip() for item in value if item.strip()))
        unknown = set(normalized) - ALLOWED_RESEARCH_OPERATIONS
        if unknown:
            raise ValueError(f"unsupported research operation(s): {', '.join(sorted(unknown))}")
        return normalized


@router.get("/status")
def research_control_status() -> dict:
    return {
        "status": "available",
        "mode": "research_diagnostics_only",
        "max_evidence_items": MAX_EVIDENCE_ITEMS,
        "max_operations": MAX_OPERATIONS,
        "allowed_operations": sorted(ALLOWED_RESEARCH_OPERATIONS),
        "can_authorize_trades": False,
        "can_submit_orders": False,
        "evidence_is_independently_verified": False,
    }


@router.post("/evaluate")
def evaluate_research_control(request: ResearchControlRequest) -> dict:
    try:
        evidence_ids = [item.evidence_id for item in request.evidence]
        if len(set(evidence_ids)) != len(evidence_ids):
            raise ValueError("evidence_id values must be unique")

        evidence_items = [
            EvidenceItem(
                evidence_id=item.evidence_id,
                observed_at=item.observed_at,
                valid_for_seconds=item.valid_for_seconds,
                confidence=item.confidence,
            )
            for item in request.evidence
        ]
        evidence = evaluate_evidence(
            evidence_items,
            conflict_pairs=[tuple(pair) for pair in request.conflict_pairs],
        )
        capability = derive_research_capability(
            uncertainty=request.uncertainty,
            disagreement=request.disagreement,
            evidence=evidence,
            operations=request.operations,
        )
        lease = EvaluationLease.issue(
            experiment_id=request.experiment_id,
            state=request.state,
            model_version=request.model_version,
            policy_version=request.policy_version,
            evidence_digest=evidence.evidence_digest,
            ttl_seconds=request.ttl_seconds,
        )
        lease_check = lease.validate(
            state=request.state,
            model_version=request.model_version,
            policy_version=request.policy_version,
            evidence_digest=evidence.evidence_digest,
        )
        proof = build_experiment_proof(
            experiment_id=request.experiment_id,
            input_digest=digest(request.state),
            evidence=evidence,
            capability=capability,
            lease=lease,
            metrics=request.metrics,
        )
        return {
            "status": "RESEARCH_CONTROL_EVALUATED",
            "experiment_id": request.experiment_id,
            "evidence": {
                "fresh_count": evidence.fresh_count,
                "stale_count": evidence.stale_count,
                "conflict_count": evidence.conflict_count,
                "minimum_confidence": evidence.minimum_confidence,
                "evidence_digest": evidence.evidence_digest,
                "provenance_boundary": "caller_supplied_metadata_not_independently_verified",
            },
            "capability": capability.as_dict(),
            "lease": {
                "valid": lease_check["valid"],
                "experiment_id": lease.experiment_id,
                "issued_at": lease.issued_at,
                "expires_at": lease.expires_at,
                "lease_digest": lease.lease_digest,
                "validation_reasons": lease_check["reasons"],
            },
            "proof": proof,
            "decision_boundary": {
                "research_mode_only": True,
                "trade_authorized": False,
                "order_submitted": False,
                "fill_claimed": False,
            },
        }
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
