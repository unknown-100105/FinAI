from typing import Any, Dict, List
import numpy as np
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from causal_risk.discovery import notears_linear
from causal_risk.dynamic_discovery import discover_lagged_graph
from causal_risk.engine import graph_snapshot, run_counterfactual
from causal_risk.tail_scenarios import generate_tail_scenarios
from causal_risk.temporal_gnn import architecture_metadata
from causal_risk.stability import assess_discovery_stability
from causal_risk.consensus import build_consensus_graph
from causal_risk.research_graph import validate_research_graph
from causal_risk.calibration import calibrate_consensus_edges
from causal_risk.market_dataset import DEFAULT_CAUSAL_PROXIES, build_market_return_dataset
from app.market_api import _get_service
from market_data.resolver import InstrumentResolver

router=APIRouter(prefix="/api/v1/causal-risk",tags=["causal-risk"])

MAX_DISCOVERY_ROWS = 5_000
MAX_DISCOVERY_VARIABLES = 100
MAX_DISCOVERY_CELLS = 250_000


def _validate_discovery_samples(samples: List[List[float]]) -> None:
    """Reject oversized or ragged discovery inputs before NumPy allocation."""
    rows = len(samples)
    if rows == 0:
        raise ValueError("samples must contain at least one row")
    if rows > MAX_DISCOVERY_ROWS:
        raise ValueError(f"samples exceed the maximum of {MAX_DISCOVERY_ROWS} rows")

    widths = {len(row) for row in samples}
    if len(widths) != 1:
        raise ValueError("samples must be a rectangular matrix")
    columns = next(iter(widths), 0)
    if columns < 2:
        raise ValueError("samples must contain at least 2 variables")
    if columns > MAX_DISCOVERY_VARIABLES:
        raise ValueError(
            f"samples exceed the maximum of {MAX_DISCOVERY_VARIABLES} variables"
        )
    if rows * columns > MAX_DISCOVERY_CELLS:
        raise ValueError(
            f"samples exceed the maximum of {MAX_DISCOVERY_CELLS} cells"
        )



class CounterfactualRequest(BaseModel):
    shock: Dict[str,float]=Field(default_factory=dict)
    allocation: Dict[str,float]=Field(default_factory=lambda:{"equity":55,"debt":30,"gold":10,"cash":5})
    include_tail_scenarios: bool = False
    use_empirical_tail_dependence: bool = False
    tail_distribution: str = Field(default="gaussian", pattern="^(gaussian|student_t_copula)$")
    tail_degrees_of_freedom: float = Field(default=5.0, gt=2.0, le=30.0)


class DiscoveryRequest(BaseModel):
    samples: List[List[float]] = Field(min_length=8, max_length=MAX_DISCOVERY_ROWS)
    lambda1: float = Field(default=0.02, ge=0, le=2)
    threshold: float = Field(default=0.10, ge=0, le=2)


class DynamicDiscoveryRequest(BaseModel):
    samples: List[List[float]] = Field(min_length=8, max_length=MAX_DISCOVERY_ROWS)
    lags: int = Field(default=1, ge=1, le=8)
    alpha: float = Field(default=1.0, gt=0, le=100)
    threshold: float = Field(default=0.08, ge=0, le=2)


class TailScenarioRequest(BaseModel):
    shock: Dict[str,float] = Field(min_length=1, max_length=MAX_DISCOVERY_VARIABLES)
    draws: int = Field(default=256, ge=8, le=5000)
    seed: int = Field(default=42, ge=0, le=10_000_000)
    use_empirical_market_dependence: bool = False
    distribution: str = Field(default="gaussian", pattern="^(gaussian|student_t_copula)$")
    degrees_of_freedom: float = Field(default=5.0, gt=2.0, le=30.0)


def _empirical_correlation_for_shock(shock: Dict[str, float]) -> list[list[float]] | None:
    proxy_items = [(key, DEFAULT_CAUSAL_PROXIES[key]) for key in sorted(shock) if key in DEFAULT_CAUSAL_PROXIES]
    if len(proxy_items) < 2:
        raise ValueError("at least two shock factors need known market proxies for empirical dependence")
    dataset = build_market_return_dataset(
        _get_service(),
        InstrumentResolver(),
        dict(proxy_items),
        days=730,
    )
    correlation = np.asarray(dataset.get("empirical_correlation"), dtype=float)
    if correlation.shape != (len(proxy_items), len(proxy_items)):
        raise ValueError("empirical market correlation is unavailable for the requested factors")
    return correlation.tolist()


@router.get("/graph")
def graph():
    return graph_snapshot()


@router.get("/architecture")
def architecture():
    return architecture_metadata()


@router.post("/counterfactual")
def counterfactual(request:CounterfactualRequest):
    try:
        tail_correlation = (
            _empirical_correlation_for_shock(request.shock)
            if request.use_empirical_tail_dependence
            else None
        )
        return run_counterfactual(
            request.shock,
            request.allocation,
            include_tail_scenarios=request.include_tail_scenarios,
            tail_correlation=tail_correlation,
            tail_distribution=request.tail_distribution,
            tail_degrees_of_freedom=request.tail_degrees_of_freedom,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.post("/discover/notears")
def discover_notears(request: DiscoveryRequest):
    try:
        _validate_discovery_samples(request.samples)
        x = np.asarray(request.samples, dtype=float)
        return notears_linear(x, lambda1=request.lambda1, threshold=request.threshold)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.post("/discover/dynamic")
def discover_dynamic(request: DynamicDiscoveryRequest):
    try:
        _validate_discovery_samples(request.samples)
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
        correlation = (
            _empirical_correlation_for_shock(request.shock)
            if request.use_empirical_market_dependence
            else None
        )
        return generate_tail_scenarios(
            request.shock,
            draws=request.draws,
            seed=request.seed,
            correlation=correlation,
            distribution=request.distribution,
            degrees_of_freedom=request.degrees_of_freedom,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


class DiscoveryGraphRequest(BaseModel):
    samples: List[List[float]] = Field(min_length=8, max_length=MAX_DISCOVERY_ROWS)
    node_ids: List[str] | None = Field(default=None, max_length=MAX_DISCOVERY_VARIABLES)
    lambda1: float = Field(default=0.02, ge=0, le=2)
    threshold: float = Field(default=0.10, ge=0, le=2)
    lags: int = Field(default=1, ge=1, le=8)
    alpha: float = Field(default=1.0, gt=0, le=100)


@router.post("/discover/graph")
def discover_graph(request: DiscoveryGraphRequest):
    try:
        _validate_discovery_samples(request.samples)
        x = np.asarray(request.samples, dtype=float)
        if request.node_ids is not None:
            if len(request.node_ids) != x.shape[1]:
                raise ValueError("node_ids length must match the sample variable count")
            if len(set(request.node_ids)) != len(request.node_ids):
                raise ValueError("node_ids must be unique")
            node_ids = [str(node_id).strip() for node_id in request.node_ids]
            if any(not node_id for node_id in node_ids):
                raise ValueError("node_ids must not be empty")
        else:
            node_ids = [f"var_{index}" for index in range(x.shape[1])]

        note = notears_linear(
            x,
            lambda1=request.lambda1,
            threshold=request.threshold,
        )
        dynamic = discover_lagged_graph(
            x,
            lags=request.lags,
            alpha=request.alpha,
            threshold=request.threshold,
        )

        contemporaneous_edges = []
        for src, row in enumerate(note["adjacency"]):
            for dst, weight in enumerate(row):
                numeric_weight = float(weight)
                if numeric_weight:
                    contemporaneous_edges.append({
                        "source": node_ids[src],
                        "target": node_ids[dst],
                        "weight": round(numeric_weight, 6),
                        "lag": 0,
                        "modality": "NOTEARS-linear",
                    })

        lagged_edges = [
            {
                **edge,
                "source": node_ids[edge["source"]],
                "target": node_ids[edge["target"]],
                "modality": "DYNOTEARS-style-temporal-ridge",
            }
            for edge in dynamic["edges"]
        ]

        return {
            "status": "research_graph_ready",
            "n_samples": int(x.shape[0]),
            "n_variables": int(x.shape[1]),
            "node_ids": node_ids,
            "contemporaneous": {
                "method": note["method"],
                "status": note["status"],
                "acyclicity": note["acyclicity"],
                "edges": contemporaneous_edges,
            },
            "temporal": {
                "method": dynamic["method"],
                "status": dynamic["status"],
                "lags": dynamic["lags"],
                "edges": lagged_edges,
            },
            "semantics": "Research discovery outputs combine a contemporaneous NOTEARS baseline with lagged temporal screening; they are not validated causal identification.",
        }
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


class MarketDiscoveryRequest(BaseModel):
    proxies: Dict[str, str] = Field(default_factory=lambda: dict(DEFAULT_CAUSAL_PROXIES))
    days: int = Field(default=730, ge=90, le=3650)
    lags: int = Field(default=1, ge=1, le=8)
    alpha: float = Field(default=1.0, gt=0, le=100)
    threshold: float = Field(default=0.08, ge=0, le=2)
    lambda1: float = Field(default=0.02, ge=0, le=2)


@router.post("/discover/market-graph")
def discover_market_graph(request: MarketDiscoveryRequest):
    try:
        dataset = build_market_return_dataset(
            _get_service(),
            InstrumentResolver(),
            request.proxies,
            days=request.days,
        )
        x = np.asarray(dataset["returns"], dtype=float)
        if x.shape[1] < 2:
            raise ValueError("market dataset must contain at least two usable variables")

        note = notears_linear(
            x,
            lambda1=request.lambda1,
            threshold=request.threshold,
        )
        dynamic = discover_lagged_graph(
            x,
            lags=request.lags,
            alpha=request.alpha,
            threshold=request.threshold,
        )
        node_ids = dataset["node_ids"]

        contemporaneous_edges = []
        for src, row in enumerate(note["adjacency"]):
            for dst, weight in enumerate(row):
                if float(weight):
                    contemporaneous_edges.append({
                        "source": node_ids[src],
                        "target": node_ids[dst],
                        "weight": round(float(weight), 6),
                        "lag": 0,
                        "modality": "NOTEARS-linear",
                    })

        temporal_edges = [
            {
                **edge,
                "source": node_ids[edge["source"]],
                "target": node_ids[edge["target"]],
                "modality": "DYNOTEARS-style-temporal-ridge",
            }
            for edge in dynamic["edges"]
        ]

        return {
            "status": "market_research_graph_ready",
            "dataset": {
                key: value for key, value in dataset.items()
                if key != "returns"
            },
            "discovery": {
                "contemporaneous": {
                    "method": note["method"],
                    "status": note["status"],
                    "acyclicity": note["acyclicity"],
                    "edges": contemporaneous_edges,
                },
                "temporal": {
                    "method": dynamic["method"],
                    "status": dynamic["status"],
                    "lags": dynamic["lags"],
                    "edges": temporal_edges,
                },
            },
            "semantics": "Market-return proxy discovery for research. Proxy selection, stationarity, confounding, identification and structural interpretation require empirical validation.",
        }
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Market causal discovery failed: {exc}") from exc


class MarketStabilityRequest(BaseModel):
    proxies: Dict[str, str] = Field(default_factory=lambda: dict(DEFAULT_CAUSAL_PROXIES))
    days: int = Field(default=730, ge=90, le=3650)
    windows: int = Field(default=4, ge=2, le=6)
    window_fraction: float = Field(default=0.60, gt=0, le=0.90)
    lags: int = Field(default=1, ge=1, le=8)
    alpha: float = Field(default=1.0, gt=0, le=100)
    threshold: float = Field(default=0.08, ge=0, le=2)
    lambda1: float = Field(default=0.02, ge=0, le=2)
    stable_frequency: float = Field(default=0.75, ge=0.5, le=1.0)


@router.post("/discover/market-graph/stability")
def market_graph_stability(request: MarketStabilityRequest):
    try:
        dataset = build_market_return_dataset(
            _get_service(),
            InstrumentResolver(),
            request.proxies,
            days=request.days,
        )
        x = np.asarray(dataset["returns"], dtype=float)
        result = assess_discovery_stability(
            x,
            dataset["node_ids"],
            windows=request.windows,
            window_fraction=request.window_fraction,
            lambda1=request.lambda1,
            threshold=request.threshold,
            lags=request.lags,
            alpha=request.alpha,
            stable_frequency=request.stable_frequency,
        )
        return {
            **result,
            "dataset": {key: value for key, value in dataset.items() if key != "returns"},
        }
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Market causal stability failed: {exc}") from exc


class MarketConsensusRequest(BaseModel):
    proxies: Dict[str, str] = Field(default_factory=lambda: dict(DEFAULT_CAUSAL_PROXIES))
    days: int = Field(default=730, ge=90, le=3650)
    windows: int = Field(default=4, ge=2, le=6)
    window_fraction: float = Field(default=0.60, gt=0, le=0.90)
    lags: int = Field(default=1, ge=1, le=8)
    alpha: float = Field(default=1.0, gt=0, le=100)
    threshold: float = Field(default=0.08, ge=0, le=2)
    lambda1: float = Field(default=0.02, ge=0, le=2)
    stable_frequency: float = Field(default=0.75, ge=0.5, le=1.0)


@router.post("/discover/market-graph/consensus")
def market_graph_consensus(request: MarketConsensusRequest):
    try:
        dataset = build_market_return_dataset(
            _get_service(),
            InstrumentResolver(),
            request.proxies,
            days=request.days,
        )
        x = np.asarray(dataset["returns"], dtype=float)
        stability = assess_discovery_stability(
            x,
            dataset["node_ids"],
            windows=request.windows,
            window_fraction=request.window_fraction,
            lambda1=request.lambda1,
            threshold=request.threshold,
            lags=request.lags,
            alpha=request.alpha,
            stable_frequency=request.stable_frequency,
        )
        return {
            **build_consensus_graph(stability),
            "stability_summary": {
                "contemporaneous_stable_edges": stability["contemporaneous"]["stable_edges"],
                "temporal_stable_edges": stability["temporal"]["stable_edges"],
                "direction_conflicts": stability["consensus"]["direction_conflicts"],
            },
            "dataset": {
                key: value for key, value in dataset.items()
                if key != "returns"
            },
        }
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Market causal consensus failed: {exc}") from exc


class ResearchGraphGateRequest(BaseModel):
    nodes: List[str]
    edges: List[Dict[str, Any]]
    min_selection_frequency: float = Field(default=0.75, ge=0.5, le=1.0)
    require_sign_consistency: float = Field(default=0.90, ge=0.5, le=1.0)
    approved: bool = False


@router.post("/discover/market-graph/gate")
def gate_research_graph(request: ResearchGraphGateRequest):
    try:
        return validate_research_graph(
            request.nodes,
            request.edges,
            min_selection_frequency=request.min_selection_frequency,
            require_sign_consistency=request.require_sign_consistency,
            approved=request.approved,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


class MarketCalibrationRequest(BaseModel):
    proxies: Dict[str, str] = Field(default_factory=lambda: dict(DEFAULT_CAUSAL_PROXIES))
    days: int = Field(default=730, ge=90, le=3650)
    windows: int = Field(default=4, ge=2, le=6)
    window_fraction: float = Field(default=0.60, gt=0, le=0.90)
    lags: int = Field(default=1, ge=1, le=8)
    alpha: float = Field(default=1.0, gt=0, le=100)
    threshold: float = Field(default=0.08, ge=0, le=2)
    lambda1: float = Field(default=0.02, ge=0, le=2)
    stable_frequency: float = Field(default=0.75, ge=0.5, le=1.0)
    bootstrap_draws: int = Field(default=100, ge=20, le=1000)
    block_size: int = Field(default=10, ge=1, le=365)
    seed: int = Field(default=42, ge=0, le=10_000_000)
    ridge_alpha: float = Field(default=1.0, gt=0, le=100)


@router.post("/discover/market-graph/calibration")
def market_graph_calibration(request: MarketCalibrationRequest):
    try:
        dataset = build_market_return_dataset(
            _get_service(),
            InstrumentResolver(),
            request.proxies,
            days=request.days,
        )
        x = np.asarray(dataset["returns"], dtype=float)
        stability = assess_discovery_stability(
            x,
            dataset["node_ids"],
            windows=request.windows,
            window_fraction=request.window_fraction,
            lambda1=request.lambda1,
            threshold=request.threshold,
            lags=request.lags,
            alpha=request.alpha,
            stable_frequency=request.stable_frequency,
        )
        consensus = build_consensus_graph(stability)
        calibration = calibrate_consensus_edges(
            x,
            dataset["node_ids"],
            consensus["edges"],
            test_fraction=0.20,
            bootstrap_draws=request.bootstrap_draws,
            block_size=request.block_size,
            seed=request.seed,
            ridge_alpha=request.ridge_alpha,
        )
        return {
            "status": "MARKET_EMPIRICAL_CALIBRATION_READY",
            "consensus": consensus,
            "calibration": calibration,
            "dataset": {
                key: value for key, value in dataset.items()
                if key != "returns"
            },
        }
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Market causal calibration failed: {exc}") from exc
