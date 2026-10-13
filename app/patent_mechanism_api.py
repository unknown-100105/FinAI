"""Opt-in API for experimental patent-mechanism research tools.

These endpoints are disabled in app.main unless FINAI_ENABLE_RESEARCH_PATENT_ENDPOINTS
is explicitly enabled. They are not production risk or authorization endpoints.
"""
from __future__ import annotations

from typing import Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from finance_engine.epcrp import EvidenceEdge, EvidenceGatedRiskGraph, RiskNode
from finance_engine.counterfactual_screening import (
    BoundedLinearDAG,
    CounterfactualAction,
    Interval,
    LinearNode,
)

router = APIRouter(
    prefix="/api/v1/research/patent-mechanisms",
    tags=["experimental-patent-mechanisms"],
)


class EPCRPNodeInput(BaseModel):
    name: str
    intercept: float = 0.0


class EPCRPEdgeInput(BaseModel):
    source: str
    target: str
    coefficient: float
    evidence_id: str = ""
    support_score: float = 1.0
    regime: str = "all"
    valid_from: Optional[str] = None
    valid_to: Optional[str] = None
    validated: bool = True
    coefficient_std: float = 0.0


class EPCRPEvaluateRequest(BaseModel):
    nodes: List[EPCRPNodeInput] = Field(min_length=1)
    edges: List[EPCRPEdgeInput] = Field(default_factory=list)
    source_values: Dict[str, float] = Field(default_factory=dict)
    interventions: Dict[str, float]
    portfolio_exposures: Dict[str, float]
    as_of: str
    regime: str = "baseline"
    min_support: float = Field(default=0.60, ge=0.0, le=1.0)
    model_version: str = "unspecified"
    uncertainty_samples: int = Field(default=0, ge=0, le=100000)
    seed: int = 17


class IntervalInput(BaseModel):
    low: float
    high: float

    def to_interval(self) -> Interval:
        return Interval(float(self.low), float(self.high))


class ScreeningNodeInput(BaseModel):
    name: str
    domain: IntervalInput
    parents: Dict[str, float] = Field(default_factory=dict)
    intercept: float = 0.0
    noise: IntervalInput = Field(default_factory=lambda: IntervalInput(low=0.0, high=0.0))


class ScreeningActionInput(BaseModel):
    action_id: str
    interventions: Dict[str, IntervalInput]


class ScreeningRequest(BaseModel):
    nodes: List[ScreeningNodeInput] = Field(min_length=1)
    target: str
    target_interval: IntervalInput
    actions: List[ScreeningActionInput] = Field(default_factory=list)


@router.post("/epcrp/evaluate")
def evaluate_epcrp(request: EPCRPEvaluateRequest):
    """Run paired-world analysis on a caller-supplied, evidence-gated static DAG."""
    try:
        graph = EvidenceGatedRiskGraph(
            nodes=[RiskNode(name=node.name, intercept=node.intercept)
                   for node in request.nodes],
            edges=[EvidenceEdge(
                source=edge.source,
                target=edge.target,
                coefficient=edge.coefficient,
                evidence_id=edge.evidence_id,
                support_score=edge.support_score,
                regime=edge.regime,
                valid_from=edge.valid_from,
                valid_to=edge.valid_to,
                validated=edge.validated,
                coefficient_std=edge.coefficient_std,
            ) for edge in request.edges],
            min_support=request.min_support,
            model_version=request.model_version,
        )
        result = graph.run_counterfactual(
            source_values=request.source_values,
            interventions=request.interventions,
            portfolio_exposures=request.portfolio_exposures,
            as_of=request.as_of,
            regime=request.regime,
            uncertainty_samples=request.uncertainty_samples,
            seed=request.seed,
        )
        payload = result.to_dict()
        payload["status"] = "EXPERIMENTAL_EPCRP_RESULT"
        payload["production_validated"] = False
        return payload
    except (TypeError, ValueError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.post("/feasibility-screen")
def screen_counterfactual_feasibility(request: ScreeningRequest):
    """Return conservative interval certificates for bounded linear-DAG actions."""
    try:
        model = BoundedLinearDAG([
            LinearNode(
                name=node.name,
                domain=node.domain.to_interval(),
                parents=node.parents,
                intercept=node.intercept,
                noise=node.noise.to_interval(),
            )
            for node in request.nodes
        ])
        actions = [
            CounterfactualAction(
                action_id=action.action_id,
                interventions={
                    name: interval.to_interval()
                    for name, interval in action.interventions.items()
                },
            )
            for action in request.actions
        ]
        certificates = model.screen_actions(
            target=request.target,
            target_interval=request.target_interval.to_interval(),
            actions=actions,
        )
        return {
            "status": "EXPERIMENTAL_SCREENING_CERTIFICATES_READY",
            "experimental": True,
            "production_validated": False,
            "graph_version": model.graph_version,
            "target": request.target,
            "target_interval": request.target_interval.to_interval().as_list(),
            "certificates": [item.as_dict() for item in certificates],
            "interpretation": (
                "MASK means the supplied bounded model proves the action cannot "
                "reach the target interval. RETAIN means infeasibility was not "
                "proven; it does not certify an action as feasible."
            ),
        }
    except (TypeError, ValueError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
