"""Advanced research endpoints for FinAI causal-risk extensions."""
from __future__ import annotations

from typing import Any, Dict, List

import numpy as np
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from causal_risk.gfnets import GFlowConfig, GFlowNetTailGenerator
from causal_risk.multimodal_graph import GraphEdge, GraphNode, MultimodalGraph
from causal_risk.regime_benchmark import assign_regimes, evaluate_predictions
from causal_risk.risk_calibration import calibrate_risk_target

router = APIRouter(prefix="/api/v1/causal-risk", tags=["causal-risk-research"])

_gfn_registry: dict[str, GFlowNetTailGenerator] = {}


class RiskCalibrationRequest(BaseModel):
    samples: List[List[float]]
    target: List[float]
    feature_names: List[str]
    alpha: float = Field(default=1.0, gt=0, le=100)


@router.post("/risk-calibration")
def risk_calibration(request: RiskCalibrationRequest):
    try:
        return calibrate_risk_target(
            request.samples,
            request.target,
            request.feature_names,
            alpha=request.alpha,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


class GFlowTrainRequest(BaseModel):
    n_factors: int = Field(ge=1, le=20)
    hidden_dim: int = Field(default=64, ge=8, le=256)
    epochs: int = Field(default=150, ge=1, le=2000)
    learning_rate: float = Field(default=1e-3, gt=0, le=0.1)
    seed: int = Field(default=42, ge=0, le=10_000_000)


@router.post("/gfnets/train")
def gfnets_train(request: GFlowTrainRequest):
    try:
        generator = GFlowNetTailGenerator(
            request.n_factors,
            GFlowConfig(
                hidden_dim=request.hidden_dim,
                learning_rate=request.learning_rate,
                epochs=request.epochs,
                seed=request.seed,
            ),
        )
        result = generator.train()
        key = f"{request.n_factors}:{request.hidden_dim}:{request.seed}"
        _gfn_registry[key] = generator
        return {
            **{k: v for k, v in result.items()},
            "registry_key": key,
            "model_persisted": False,
            "semantics": (
                "In-memory research prototype only. Persisted model artifacts "
                "require explicit versioning and validation before production use."
            ),
        }
    except (RuntimeError, ValueError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


class GFlowGenerateRequest(BaseModel):
    registry_key: str = Field(min_length=3, max_length=128)
    center: Dict[str, float]
    draws: int = Field(default=64, ge=1, le=5000)
    seed: int = Field(default=42, ge=0, le=10_000_000)
    scale: float = Field(default=0.35, gt=0, le=2)


@router.post("/gfnets/generate")
def gfnets_generate(request: GFlowGenerateRequest):
    generator = _gfn_registry.get(request.registry_key)
    if generator is None:
        raise HTTPException(status_code=404, detail="GFlowNet registry key not found")
    try:
        return generator.sample(
            request.center,
            draws=request.draws,
            seed=request.seed,
            scale=request.scale,
        )
    except (RuntimeError, ValueError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


class MultimodalNodeRequest(BaseModel):
    node_id: str
    node_type: str
    modality: str
    features: List[float]
    provenance: str


class MultimodalEdgeRequest(BaseModel):
    source: str
    target: str
    relation: str
    weight: float
    modality: str
    provenance: str


class MultimodalEncodeRequest(BaseModel):
    nodes: List[MultimodalNodeRequest]
    edges: List[MultimodalEdgeRequest]
    target_node: str
    modality_vectors: Dict[str, List[float]]
    output_dim: int = Field(default=16, ge=1, le=256)


@router.post("/multimodal/encode")
def multimodal_encode(request: MultimodalEncodeRequest):
    try:
        graph = MultimodalGraph(
            nodes=[
                GraphNode(
                    item.node_id,
                    item.node_type,
                    item.modality,
                    tuple(item.features),
                    item.provenance,
                )
                for item in request.nodes
            ],
            edges=[
                GraphEdge(
                    item.source,
                    item.target,
                    item.relation,
                    item.weight,
                    item.modality,
                    item.provenance,
                )
                for item in request.edges
            ],
        )
        vector = graph.fuse_node(
            request.target_node,
            request.modality_vectors,
            output_dim=request.output_dim,
        )
        return {
            "status": "MULTIMODAL_FUSION_READY",
            "target_node": request.target_node,
            "embedding": [round(float(value), 8) for value in vector],
            "graph": graph.payload(),
        }
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


class RegimeBenchmarkRequest(BaseModel):
    samples: List[List[float]]
    y_true: List[float]
    y_pred: List[float]
    volatility_window: int = Field(default=20, ge=2, le=250)
    high_vol_quantile: float = Field(default=0.80, gt=0.5, lt=1)


@router.post("/regime-benchmark")
def regime_benchmark(request: RegimeBenchmarkRequest):
    try:
        regimes = assign_regimes(
            request.samples,
            volatility_window=request.volatility_window,
            high_vol_quantile=request.high_vol_quantile,
        )
        if len(regimes) != len(request.y_true):
            raise ValueError("samples and prediction rows must align")
        return {
            **evaluate_predictions(request.y_true, request.y_pred, regimes),
            "regime_counts": {
                str(regime): int(np.sum(regimes == regime))
                for regime in np.unique(regimes)
            },
        }
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.get("/research-status")
def research_status():
    return {
        "status": "FINAI_RESEARCH_STACK",
        "components": {
            "notears": "implemented_research_baseline",
            "temporal_discovery": "implemented_research_baseline",
            "stability_consensus": "implemented_and_gated",
            "empirical_calibration": "implemented",
            "correlation_aware_tail_sampling": "implemented",
            "student_t_copula": "research_implemented",
            "temporal_gnn": "trainable_research_implementation",
            "gflownet": "trajectory_balance_research_prototype",
            "multimodal_graph": "typed_fusion_research_implementation",
            "neuro_symbolic_rules": "deterministic_constraint_engine",
            "regime_benchmark": "implemented",
        },
        "production_boundary": (
            "Research components remain isolated from production investment "
            "decision logic unless explicitly validated and approved."
        ),
    }
