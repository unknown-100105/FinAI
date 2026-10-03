"""Advanced research endpoints for FinAI causal-risk extensions."""
from __future__ import annotations

from typing import Any, Dict, List

import numpy as np
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from causal_risk.gfnets import GFlowConfig, GFlowNetTailGenerator
from causal_risk.multimodal_graph import GraphEdge, GraphNode, MultimodalGraph
from causal_risk.microstructure import summarize_order_book
from causal_risk.multimodal_ingestion import (
    build_document_nodes,
    build_event_nodes,
    build_relation_edges,
    build_portfolio_edges,
)
from causal_risk.regime_benchmark import assign_regimes, evaluate_predictions
from causal_risk.risk_calibration import calibrate_risk_target
from causal_risk.research_counterfactual import run_research_counterfactual

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
            "microstructure_features": "implemented",
            "text_graph_alignment": "implemented",
            "research_counterfactual": "explicit-approval-only",
        },
        "production_boundary": (
            "Research components remain isolated from production investment "
            "decision logic unless explicitly validated and approved."
        ),
    }


class ResearchCounterfactualRequest(BaseModel):
    shock: Dict[str, float]
    allocation: Dict[str, float]
    nodes: List[str]
    edges: List[Dict[str, Any]]
    approved: bool = False


@router.post("/research-counterfactual")
def research_counterfactual(request: ResearchCounterfactualRequest):
    try:
        return run_research_counterfactual(
            request.shock,
            request.allocation,
            request.nodes,
            request.edges,
            approved=request.approved,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

 
 
class MicrostructureRequest(BaseModel):
    bids: List[List[float]]
    asks: List[List[float]]


@router.post("/microstructure")
def microstructure(request: MicrostructureRequest):
    try:
        return summarize_order_book({
            "bids": request.bids,
            "asks": request.asks,
        })
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


class MultimodalIngestionRequest(BaseModel):
    documents: List[Dict[str, Any]] = Field(default_factory=list)
    events: List[Dict[str, Any]] = Field(default_factory=list)
    relations: List[Dict[str, Any]] = Field(default_factory=list)
    portfolio_exposures: List[Dict[str, Any]] = Field(default_factory=list)


@router.post("/multimodal/ingest")
def multimodal_ingest(request: MultimodalIngestionRequest):
    try:
        documents = build_document_nodes(request.documents)
        events = build_event_nodes(request.events)
        relation_edges = build_relation_edges(request.relations)
        portfolio_edges = build_portfolio_edges(request.portfolio_exposures)
        return {
            "status": "MULTIMODAL_INGESTION_READY",
            "document_nodes": [node.__dict__ for node in documents],
            "event_nodes": [node.__dict__ for node in events],
            "relation_edges": [edge.__dict__ for edge in relation_edges],
            "portfolio_edges": [edge.__dict__ for edge in portfolio_edges],
            "counts": {
                "documents": len(documents),
                "events": len(events),
                "relations": len(relation_edges),
                "portfolio_exposures": len(portfolio_edges),
            },
        }
    except (TypeError, ValueError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
