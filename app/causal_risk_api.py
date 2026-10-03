from typing import Any, Dict, List
import numpy as np
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from causal_risk.discovery import notears_linear
from causal_risk.dynamic_discovery import discover_lagged_graph
from causal_risk.engine import graph_snapshot, run_counterfactual
from causal_risk.tail_scenarios import generate_tail_scenarios
from causal_risk.temporal_gnn import architecture_metadata
from causal_risk.market_dataset import DEFAULT_CAUSAL_PROXIES, build_market_return_dataset
from app.market_api import _get_service
from market_data.resolver import InstrumentResolver

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


class DiscoveryGraphRequest(BaseModel):
    samples: List[List[float]]
    node_ids: List[str] | None = None
    lambda1: float = Field(default=0.02, ge=0, le=2)
    threshold: float = Field(default=0.10, ge=0, le=2)
    lags: int = Field(default=1, ge=1, le=8)
    alpha: float = Field(default=1.0, gt=0, le=100)


@router.post("/discover/graph")
def discover_graph(request: DiscoveryGraphRequest):
    try:
        x = np.asarray(request.samples, dtype=float)
        if x.ndim != 2 or x.shape[1] < 2:
            raise ValueError("samples must contain at least 2 variables")
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
