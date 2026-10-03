"""Advanced research endpoints for FinAI causal-risk extensions."""
from __future__ import annotations

from typing import Any, Dict, List

import numpy as np
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from causal_risk.gfnets import GFlowConfig, GFlowNetTailGenerator
from causal_risk.constrained_gfnets import CausalConstrainedTailGenerator
from causal_risk.feasibility_pruning import AdaptivePruningController, evaluate_prefix_feasibility
from causal_risk.stress_objectives import CausalStressReward
from causal_risk.multimodal_graph import GraphEdge, GraphNode, MultimodalGraph
from causal_risk.multimodal_encoder import MultimodalEncoderConfig, train_multimodal_encoder
from causal_risk.microstructure import summarize_order_book
from causal_risk.multimodal_ingestion import (
    build_document_nodes,
    build_event_nodes,
    build_relation_edges,
    build_portfolio_edges,
)
from causal_risk.regime_benchmark import assign_regimes, evaluate_predictions
from causal_risk.risk_calibration import calibrate_risk_target
from causal_risk.channel_calibration import fit_channel_calibration
from causal_risk.research_evaluation import (
    ablation_summary,
    perturb_features,
    scenario_quality_metrics,
    tail_backtest_metrics,
)
from causal_risk.pipeline import run_causal_research_pipeline
from causal_risk.research_counterfactual import run_research_counterfactual
from causal_risk.temporal_gnn import (
    TemporalSnapshot,
    build_temporal_edges,
    train_temporal_sequence_model,
)

router = APIRouter(prefix="/api/v1/causal-risk", tags=["causal-risk-research"])

_gfn_registry: dict[str, GFlowNetTailGenerator] = {}


class RiskCalibrationRequest(BaseModel):
    samples: List[List[float]] = Field(min_length=60, max_length=5000)
    target: List[float] = Field(min_length=60, max_length=5000)
    feature_names: List[str] = Field(min_length=2, max_length=100)
    alpha: float = Field(default=1.0, gt=0, le=100)


@router.post("/risk-calibration")
def risk_calibration(request: RiskCalibrationRequest):
    try:
        if request.samples and len(request.samples) * len(request.samples[0]) > 250_000:
            raise ValueError("calibration input exceeds the maximum of 250000 cells")
        if len(request.target) != len(request.samples):
            raise ValueError("target must align with samples")
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
    device: str = Field(default="auto", pattern="^(auto|cpu|cuda)$")
    reward_mode: str = Field(default="synthetic_tail", pattern="^(synthetic_tail|causal_empirical)$")
    empirical_center: List[float] | None = Field(default=None, min_length=1, max_length=20)
    empirical_scale: List[float] | None = Field(default=None, min_length=1, max_length=20)
    correlation_inverse: List[List[float]] | None = Field(default=None, max_length=20)
    edge_matrix: List[List[float]] | None = Field(default=None, max_length=20)
    portfolio_weights: List[float] | None = Field(default=None, max_length=20)


class ChannelCalibrationRequest(BaseModel):
    scm_samples: List[Dict[str, float]] = Field(min_length=80, max_length=5000)
    observed_channels: Dict[str, List[float]]
    alpha: float = Field(default=1.0, gt=0, le=100)


@router.post("/risk-calibration/fit-channels")
def fit_channel_risk_calibration(request: ChannelCalibrationRequest):
    try:
        lengths = {len(values) for values in request.observed_channels.values()}
        if lengths != {len(request.scm_samples)}:
            raise ValueError("all observed channel arrays must align with scm_samples")
        if len(request.scm_samples) * max(len(request.scm_samples[0]), 1) > 250_000:
            raise ValueError("calibration input exceeds the maximum of 250000 cells")
        return fit_channel_calibration(
            request.scm_samples,
            request.observed_channels,
            alpha=request.alpha,
        )
    except (TypeError, ValueError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


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
                device=request.device,
            ),
        )
        reward_fn = None
        objective_name = "synthetic_tail_reward"
        if request.reward_mode == "causal_empirical":
            if request.empirical_center is None or request.empirical_scale is None:
                raise ValueError("causal_empirical reward requires empirical_center and empirical_scale")
            if len(request.empirical_center) != request.n_factors:
                raise ValueError("empirical_center must match n_factors")
            if len(request.empirical_scale) != request.n_factors:
                raise ValueError("empirical_scale must match n_factors")
            if request.correlation_inverse is not None:
                inverse_shape = np.asarray(request.correlation_inverse, dtype=float).shape
                if inverse_shape != (request.n_factors, request.n_factors):
                    raise ValueError("correlation_inverse must match n_factors")
            if request.edge_matrix is not None:
                edge_shape = np.asarray(request.edge_matrix, dtype=float).shape
                if edge_shape != (request.n_factors, request.n_factors):
                    raise ValueError("edge_matrix must match n_factors")
            reward_fn = CausalStressReward(
                tuple(request.empirical_center),
                tuple(request.empirical_scale),
                tuple(tuple(row) for row in request.correlation_inverse)
                if request.correlation_inverse is not None else None,
                tuple(tuple(row) for row in request.edge_matrix)
                if request.edge_matrix is not None else None,
                tuple(request.portfolio_weights)
                if request.portfolio_weights is not None else None,
            )
            objective_name = "causal_empirical_tail_reward"
        result = generator.train(
            reward_fn=reward_fn,
            objective_name=objective_name,
        )
        key = f"{request.n_factors}:{request.hidden_dim}:{request.seed}:{request.reward_mode}"
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
    center: Dict[str, float] = Field(min_length=1, max_length=20)
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


class MultimodalTrainRequest(BaseModel):
    inputs: Dict[str, List[List[float]]]
    hidden_dim: int = Field(default=64, ge=8, le=256)
    layers: int = Field(default=2, ge=1, le=6)
    heads: int = Field(default=4, ge=1, le=16)
    epochs: int = Field(default=100, ge=1, le=1000)
    learning_rate: float = Field(default=1e-3, gt=0, le=0.1)
    mask_probability: float = Field(default=0.25, ge=0, lt=1)
    seed: int = Field(default=42, ge=0, le=10_000_000)


@router.post("/multimodal/train")
def multimodal_train(request: MultimodalTrainRequest):
    try:
        if not request.inputs:
            raise ValueError("at least one modality matrix is required")
        if len(request.inputs) > 7:
            raise ValueError("a maximum of 7 modalities is supported")
        total_cells = sum(
            len(values) * (len(values[0]) if values else 0)
            for values in request.inputs.values()
        )
        if total_cells > 250_000:
            raise ValueError("multimodal training input exceeds 250000 cells")
        return train_multimodal_encoder(
            request.inputs,
            config=MultimodalEncoderConfig(
                hidden_dim=request.hidden_dim,
                layers=request.layers,
                heads=request.heads,
            ),
            epochs=request.epochs,
            learning_rate=request.learning_rate,
            mask_probability=request.mask_probability,
            seed=request.seed,
        )
    except (TypeError, ValueError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


class MultimodalNodeRequest(BaseModel):
    node_id: str = Field(min_length=1, max_length=128)
    node_type: str = Field(min_length=1, max_length=64)
    modality: str = Field(min_length=1, max_length=32)
    features: List[float] = Field(max_length=256)
    provenance: str = Field(min_length=1, max_length=512)


class MultimodalEdgeRequest(BaseModel):
    source: str = Field(min_length=1, max_length=128)
    target: str = Field(min_length=1, max_length=128)
    relation: str = Field(min_length=1, max_length=128)
    weight: float
    modality: str = Field(min_length=1, max_length=32)
    provenance: str = Field(min_length=1, max_length=512)


class MultimodalEncodeRequest(BaseModel):
    nodes: List[MultimodalNodeRequest] = Field(min_length=1, max_length=500)
    edges: List[MultimodalEdgeRequest] = Field(max_length=2000)
    target_node: str = Field(min_length=1, max_length=128)
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


class TemporalSnapshotRequest(BaseModel):
    node_features: List[List[float]] = Field(min_length=2, max_length=100)
    target: List[float] = Field(min_length=2, max_length=100)
    edge_sources: List[int] = Field(max_length=1000)
    edge_targets: List[int] = Field(max_length=1000)
    time_deltas: List[float] = Field(max_length=1000)


class TemporalTrainRequest(BaseModel):
    snapshots: List[TemporalSnapshotRequest] = Field(min_length=5, max_length=120)
    hidden_features: int = Field(default=32, ge=4, le=128)
    heads: int = Field(default=4, ge=1, le=16)
    epochs: int = Field(default=100, ge=1, le=1000)
    learning_rate: float = Field(default=1e-3, gt=0, le=0.1)
    train_fraction: float = Field(default=0.8, ge=0.6, lt=1.0)
    seed: int = Field(default=42, ge=0, le=10_000_000)
    device: str = Field(default="auto", pattern="^(auto|cpu|cuda)$")


@router.post("/temporal-gnn/train")
def temporal_gnn_train(request: TemporalTrainRequest):
    try:
        snapshots = []
        total_cells = 0
        for index, item in enumerate(request.snapshots):
            if len(item.node_features) != len(item.target):
                raise ValueError(f"snapshot {index} target length must match node count")
            if not (
                len(item.edge_sources)
                == len(item.edge_targets)
                == len(item.time_deltas)
            ):
                raise ValueError(f"snapshot {index} edge arrays must have equal lengths")
            if item.node_features:
                total_cells += len(item.node_features) * len(item.node_features[0])
            snapshots.append(
                TemporalSnapshot(
                    node_features=np.asarray(item.node_features, dtype=np.float32),
                    target=np.asarray(item.target, dtype=np.float32),
                    edges=build_temporal_edges(
                        item.edge_sources,
                        item.edge_targets,
                        item.time_deltas,
                    ),
                )
            )
        if total_cells > 250_000:
            raise ValueError("temporal training input exceeds the maximum of 250000 cells")
        result = train_temporal_sequence_model(
            snapshots,
            hidden_features=request.hidden_features,
            heads=request.heads,
            epochs=request.epochs,
            learning_rate=request.learning_rate,
            train_fraction=request.train_fraction,
            seed=request.seed,
            device=request.device,
        )
        result.pop("model", None)
        return result
    except (TypeError, ValueError, RuntimeError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


class RegimeBenchmarkRequest(BaseModel):
    samples: List[List[float]] = Field(min_length=22, max_length=5000)
    y_true: List[float] = Field(min_length=22, max_length=5000)
    y_pred: List[float] = Field(min_length=22, max_length=5000)
    volatility_window: int = Field(default=20, ge=2, le=250)
    high_vol_quantile: float = Field(default=0.80, gt=0.5, lt=1)


@router.post("/regime-benchmark")
def regime_benchmark(request: RegimeBenchmarkRequest):
    try:
        if request.samples and len(request.samples) * len(request.samples[0]) > 250_000:
            raise ValueError("regime benchmark input exceeds the maximum of 250000 cells")
        if len(request.y_true) != len(request.samples) or len(request.y_pred) != len(request.samples):
            raise ValueError("prediction arrays must align with samples")
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
            "temporal_gnn_evaluation": "chronological_holdout_training_available",
            "gflownet": "trajectory_balance_research_prototype",
            "gflownet_training": "causal_empirical_reward_training_available",
            "multimodal_graph": "typed_fusion_research_implementation",
            "multimodal_encoder": "masked_modality_training_available",
            "neuro_symbolic_rules": "deterministic_constraint_engine",
            "regime_benchmark": "implemented",
            "microstructure_features": "implemented",
            "text_graph_alignment": "implemented",
            "research_counterfactual": "explicit-approval-only",
            "causal_feasibility_pruning": "conservative_prefix_certificate",
            "constrained_gflownet": "action_masked_research_prototype",
            "incremental_feasibility_cache": "descendant_cone_recomputation",
            "patent_mechanism_benchmark": "exact_small_state_comparison_available",
        },
        "production_boundary": (
            "Research components remain isolated from production investment "
            "decision logic unless explicitly validated and approved."
        ),
    }


class TailBacktestRequest(BaseModel):
    realized_loss: List[float] = Field(min_length=20, max_length=5000)
    forecast_var: List[float] = Field(min_length=20, max_length=5000)
    level: float = Field(default=0.95, gt=0.5, lt=1.0)


@router.post("/tail-backtest")
def tail_backtest(request: TailBacktestRequest):
    try:
        return tail_backtest_metrics(
            request.realized_loss,
            request.forecast_var,
            level=request.level,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


class ScenarioQualityRequest(BaseModel):
    scenarios: List[List[float]] = Field(min_length=2, max_length=5000)
    empirical_samples: List[List[float]] | None = Field(default=None, max_length=5000)
    causal_edge_matrix: List[List[float]] | None = Field(default=None, max_length=100)


@router.post("/scenario-quality")
def scenario_quality(request: ScenarioQualityRequest):
    try:
        total_cells = len(request.scenarios) * len(request.scenarios[0])
        if request.empirical_samples:
            total_cells += len(request.empirical_samples) * len(request.empirical_samples[0])
        if total_cells > 250_000:
            raise ValueError("scenario-quality input exceeds the maximum of 250000 cells")
        return scenario_quality_metrics(
            request.scenarios,
            request.empirical_samples,
            causal_edge_matrix=request.causal_edge_matrix,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


class AblationSummaryRequest(BaseModel):
    results: Dict[str, Dict[str, float]]
    primary_metric: str = Field(min_length=1, max_length=64)


@router.post("/ablation-summary")
def ablation(request: AblationSummaryRequest):
    try:
        if len(request.results) < 2 or len(request.results) > 50:
            raise ValueError("ablation results must contain between 2 and 50 models")
        return ablation_summary(request.results, primary_metric=request.primary_metric)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


class RobustnessPerturbationRequest(BaseModel):
    samples: List[List[float]] = Field(min_length=2, max_length=5000)
    scale: float = Field(default=1.0, gt=0, le=10)
    missing_columns: List[int] = Field(default_factory=list, max_length=100)
    noise_std: float = Field(default=0.0, ge=0, le=10)
    seed: int = Field(default=42, ge=0, le=10_000_000)


@router.post("/robustness/perturb")
def robustness_perturb(request: RobustnessPerturbationRequest):
    try:
        if request.samples and len(request.samples) * len(request.samples[0]) > 250_000:
            raise ValueError("robustness input exceeds the maximum of 250000 cells")
        result = perturb_features(
            request.samples,
            scale=request.scale,
            missing_columns=request.missing_columns,
            noise_std=request.noise_std,
            seed=request.seed,
        )
        return {
            "status": "ROBUSTNESS_PERTURBATION_READY",
            "shape": list(result.shape),
            "samples": result.tolist(),
            "perturbation": {
                "scale": request.scale,
                "missing_columns": request.missing_columns,
                "noise_std": request.noise_std,
                "seed": request.seed,
            },
        }
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


class ResearchCounterfactualRequest(BaseModel):
    shock: Dict[str, float] = Field(min_length=1, max_length=100)
    allocation: Dict[str, float] = Field(min_length=1, max_length=100)
    nodes: List[str] = Field(min_length=1, max_length=100)
    edges: List[Dict[str, Any]] = Field(max_length=1000)
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
    bids: List[List[float]] = Field(min_length=1, max_length=1000)
    asks: List[List[float]] = Field(min_length=1, max_length=1000)


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
    documents: List[Dict[str, Any]] = Field(default_factory=list, max_length=1000)
    events: List[Dict[str, Any]] = Field(default_factory=list, max_length=1000)
    relations: List[Dict[str, Any]] = Field(default_factory=list, max_length=2000)
    portfolio_exposures: List[Dict[str, Any]] = Field(default_factory=list, max_length=2000)


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


class CausalResearchPipelineRequest(BaseModel):
    samples: List[List[float]] = Field(min_length=60, max_length=5000)
    node_ids: List[str] = Field(min_length=2, max_length=100)
    lambda1: float = Field(default=0.02, ge=0, le=2)
    threshold: float = Field(default=0.08, ge=0, le=2)
    lags: int = Field(default=2, ge=1, le=8)
    alpha: float = Field(default=1.0, gt=0, le=100)
    windows: int = Field(default=4, ge=2, le=6)
    window_fraction: float = Field(default=0.60, gt=0, le=0.90)
    stable_frequency: float = Field(default=0.75, ge=0.5, le=1.0)
    bootstrap_draws: int = Field(default=100, ge=20, le=1000)
    block_size: int = Field(default=10, ge=1, le=365)
    ridge_alpha: float = Field(default=1.0, gt=0, le=100)
    seed: int = Field(default=42, ge=0, le=10_000_000)


@router.post("/research-pipeline")
def causal_research_pipeline(request: CausalResearchPipelineRequest):
    try:
        return run_causal_research_pipeline(
            request.samples,
            request.node_ids,
            lambda1=request.lambda1,
            threshold=request.threshold,
            lags=request.lags,
            alpha=request.alpha,
            windows=request.windows,
            window_fraction=request.window_fraction,
            stable_frequency=request.stable_frequency,
            bootstrap_draws=request.bootstrap_draws,
            block_size=request.block_size,
            ridge_alpha=request.ridge_alpha,
            seed=request.seed,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


class FeasibilityScreenRequest(BaseModel):
    nodes: List[str] = Field(min_length=2, max_length=100)
    edges: List[Dict[str, Any]] = Field(max_length=1000)
    prefix: Dict[str, float] = Field(default_factory=dict, max_length=100)
    candidate_actions: Dict[str, List[float]]
    node_bounds: Dict[str, List[float]]
    target_node: str = Field(min_length=1, max_length=100)
    target_interval: List[float] = Field(min_length=2, max_length=2)
    empirical_center: Dict[str, float] | None = Field(default=None, max_length=100)
    empirical_scale: Dict[str, float] | None = Field(default=None, max_length=100)
    target_full_eval_fraction: float = Field(default=0.25, gt=0, le=1)
    adaptive_margin: float = Field(default=0.0, ge=-1, le=1)


@router.post("/research-pruning/screen")
def feasibility_screen(request: FeasibilityScreenRequest):
    try:
        if len(request.edges) > 1000:
            raise ValueError("at most 1000 edges are supported")
        if len(request.candidate_actions) > 100:
            raise ValueError("at most 100 candidate action groups are supported")
        total_candidates = sum(len(values) for values in request.candidate_actions.values())
        if total_candidates < 1 or total_candidates > 5000:
            raise ValueError("candidate action count must be between 1 and 5000")
        controller = AdaptivePruningController(
            target_full_eval_fraction=request.target_full_eval_fraction,
            current_margin=request.adaptive_margin,
        )
        from causal_risk.feasibility_pruning import screen_candidate_actions
        return screen_candidate_actions(
            request.nodes,
            request.edges,
            request.prefix,
            request.candidate_actions,
            request.node_bounds,
            target_node=request.target_node,
            target_interval=request.target_interval,
            empirical_center=request.empirical_center,
            empirical_scale=request.empirical_scale,
            controller=controller,
        )
    except (TypeError, ValueError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


class ConstrainedGFlowNetTrainRequest(BaseModel):
    factor_ids: List[str] = Field(min_length=1, max_length=20)
    hidden_dim: int = Field(default=64, ge=8, le=256)
    epochs: int = Field(default=150, ge=1, le=2000)
    learning_rate: float = Field(default=1e-3, gt=0, le=0.1)
    seed: int = Field(default=42, ge=0, le=10_000_000)
    device: str = Field(default="auto", pattern="^(auto|cpu|cuda)$")
    empirical_center: List[float] | None = Field(default=None, min_length=1, max_length=20)
    empirical_scale: List[float] | None = Field(default=None, min_length=1, max_length=20)
    correlation_inverse: List[List[float]] | None = Field(default=None, max_length=20)
    edge_matrix: List[List[float]] | None = Field(default=None, max_length=20)
    portfolio_weights: List[float] | None = Field(default=None, max_length=20)


class ConstrainedGFlowNetGenerateRequest(BaseModel):
    factor_ids: List[str] = Field(min_length=1, max_length=20)
    center: Dict[str, float] = Field(min_length=1, max_length=20)
    nodes: List[str] = Field(min_length=2, max_length=100)
    edges: List[Dict[str, Any]] = Field(max_length=1000)
    node_bounds: Dict[str, List[float]]
    target_node: str = Field(min_length=1, max_length=100)
    target_interval: List[float] = Field(min_length=2, max_length=2)
    draws: int = Field(default=64, ge=1, le=5000)
    scale: float = Field(default=0.35, gt=0, le=2)
    seed: int = Field(default=42, ge=0, le=10_000_000)
    hidden_dim: int = Field(default=64, ge=8, le=256)
    epochs: int = Field(default=150, ge=1, le=2000)
    device: str = Field(default="auto", pattern="^(auto|cpu|cuda)$")
    adaptive_margin: float = Field(default=0.0, ge=-1, le=1)
    target_full_eval_fraction: float = Field(default=0.25, gt=0, le=1)
    empirical_center: Dict[str, float] | None = Field(default=None, max_length=100)
    empirical_scale: Dict[str, float] | None = Field(default=None, max_length=100)


@router.post("/research-pruning/constrained-gfnets")
def constrained_gfnets(request: ConstrainedGFlowNetGenerateRequest):
    try:
        if len(request.factor_ids) != len(request.center):
            raise ValueError("factor_ids and center must have matching dimensions")
        config = GFlowConfig(
            hidden_dim=request.hidden_dim,
            epochs=request.epochs,
            seed=request.seed,
            device=request.device,
        )
        generator = CausalConstrainedTailGenerator(request.factor_ids, config)
        reward = None
        objective = "synthetic_tail_reward"
        if request.empirical_center is not None or request.empirical_scale is not None:
            if request.empirical_center is None or request.empirical_scale is None:
                raise ValueError("empirical_center and empirical_scale must be supplied together")
            if len(request.empirical_center) != len(request.factor_ids) or len(request.empirical_scale) != len(request.factor_ids):
                raise ValueError("empirical center/scale must match factor_ids")
            missing_center = [k for k in request.factor_ids if k not in request.empirical_center]
            missing_scale = [k for k in request.factor_ids if k not in request.empirical_scale]
            if missing_center or missing_scale:
                raise ValueError(
                    f"empirical center/scale missing factor ids: {sorted(set(missing_center + missing_scale))}"
                )
            factor_index = {factor: index for index, factor in enumerate(request.factor_ids)}
            edge_matrix = np.zeros((len(request.factor_ids), len(request.factor_ids)), dtype=float)
            for edge in request.edges:
                source = str(edge.get("source", ""))
                target = str(edge.get("target", ""))
                if source in factor_index and target in factor_index and int(edge.get("lag", 0)) == 0:
                    edge_matrix[factor_index[source], factor_index[target]] = float(edge.get("weight", 0.0))
            reward = CausalStressReward(
                tuple(request.empirical_center[k] for k in request.factor_ids),
                tuple(request.empirical_scale[k] for k in request.factor_ids),
                edge_matrix=tuple(tuple(float(v) for v in row) for row in edge_matrix),
            )
            objective = "causal_empirical_tail_reward"
        train_result = generator.train(
            reward_fn=reward,
            objective_name=objective,
            device=request.device,
        )
        controller = AdaptivePruningController(
            target_full_eval_fraction=request.target_full_eval_fraction,
            current_margin=request.adaptive_margin,
        )
        sample_result = generator.sample(
            request.center,
            nodes=request.nodes,
            edges=request.edges,
            node_bounds=request.node_bounds,
            target_node=request.target_node,
            target_interval=request.target_interval,
            scale=request.scale,
            draws=request.draws,
            seed=request.seed,
            controller=controller,
            empirical_center=request.empirical_center,
            empirical_scale=request.empirical_scale,
        )
        return {
            "status": "CAUSAL_CONSTRAINED_GFNet_RESEARCH_READY",
            "training": train_result,
            "generation": sample_result,
        }
    except (RuntimeError, TypeError, ValueError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
