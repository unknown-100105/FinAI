from typing import Any, Dict, List
import numpy as np
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from causal_risk.discovery import notears_linear
from causal_risk.dynamic_discovery import discover_lagged_graph
from causal_risk.engine import graph_snapshot, run_counterfactual
from causal_risk.tail_scenarios import generate_tail_scenarios
from causal_risk.temporal_gnn import architecture_metadata

router=APIRouter(prefix="/api/v1/causal-risk",tags=["causal-risk"])


class CounterfactualRequest(BaseModel):
    shock: Dict[str,float]=Field(default_factory=dict)
    allocation: Dict[str,float]=Field(default_factory=lambda:{"equity":55,"debt":30,"gold":10,"cash":5})
    include_tail_scenarios: bool = False


class DiscoveryRequest(BaseModel):
    samples: List[List[float]]
    lambda1: float = Field(default=0.02, ge=0, le=2)
    threshold: float = Field(default=0.10, ge=0, le=2)


class DynamicDiscoveryRequest(BaseModel):
    samples: List[List[float]]
    lags: int = Field(default=1, ge=1, le=8)
    alpha: float = Field(default=1.0, gt=0, le=100)
    threshold: float = Field(default=0.08, ge=0, le=2)


class TailScenarioRequest(BaseModel):
    shock: Dict[str,float]
    draws: int = Field(default=256, ge=8, le=5000)
    seed: int = Field(default=42, ge=0, le=10_000_000)


@router.get("/graph")
def graph():
    return graph_snapshot()


@router.get("/architecture")
def architecture():
    return architecture_metadata()


@router.post("/counterfactual")
def counterfactual(request:CounterfactualRequest):
    try:
        return run_counterfactual(
            request.shock,
            request.allocation,
            include_tail_scenarios=request.include_tail_scenarios,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.post("/discover/notears")
def discover_notears(request: DiscoveryRequest):
    try:
        x = np.asarray(request.samples, dtype=float)
        return notears_linear(x, lambda1=request.lambda1, threshold=request.threshold)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.post("/discover/dynamic")
def discover_dynamic(request: DynamicDiscoveryRequest):
    try:
        return discover_lagged_graph(
            request.samples,
            lags=request.lags,
            alpha=request.alpha,
            threshold=request.threshold,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.post("/tail-scenarios")
def tail_scenarios(request: TailScenarioRequest):
    try:
        return generate_tail_scenarios(
            request.shock,
            draws=request.draws,
            seed=request.seed,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
