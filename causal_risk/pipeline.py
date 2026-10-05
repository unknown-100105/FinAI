"""End-to-end research pipeline for the FinAI causal-risk stack."""
from __future__ import annotations

from typing import Any, Sequence

import numpy as np

from causal_risk.calibration import calibrate_consensus_edges
from causal_risk.consensus import build_consensus_graph
from causal_risk.discovery import notears_linear
from causal_risk.dynamic_discovery import discover_lagged_graph
from causal_risk.regime_benchmark import assign_regimes
from causal_risk.stability import assess_discovery_stability


def run_causal_research_pipeline(
    samples: Sequence[Sequence[float]],
    node_ids: Sequence[str],
    *,
    lambda1: float = 0.02,
    threshold: float = 0.08,
    lags: int = 2,
    alpha: float = 1.0,
    windows: int = 4,
    window_fraction: float = 0.60,
    stable_frequency: float = 0.75,
    bootstrap_draws: int = 100,
    block_size: int = 10,
    ridge_alpha: float = 1.0,
    seed: int = 42,
) -> dict[str, Any]:
    """Run discovery -> stability -> consensus -> empirical calibration as one bundle."""
    X = np.asarray(samples, dtype=float)
    labels = [str(value).strip() for value in node_ids]
    if X.ndim != 2 or X.shape[0] < 60 or X.shape[1] < 2:
        raise ValueError("research pipeline requires at least 60 rows and 2 variables")
    if X.shape[1] != len(labels) or len(set(labels)) != len(labels):
        raise ValueError("node_ids must uniquely match sample variables")
    if not np.isfinite(X).all():
        raise ValueError("samples contain non-finite values")

    contemporaneous = notears_linear(
        X,
        lambda1=lambda1,
        threshold=threshold,
    )
    temporal = discover_lagged_graph(
        X,
        lags=lags,
        alpha=alpha,
        threshold=threshold,
    )
    stability = assess_discovery_stability(
        X,
        labels,
        windows=windows,
        window_fraction=window_fraction,
        lambda1=lambda1,
        threshold=threshold,
        lags=lags,
        alpha=alpha,
        stable_frequency=stable_frequency,
    )
    consensus = build_consensus_graph(stability)
    calibration = calibrate_consensus_edges(
        X,
        labels,
        consensus["edges"],
        bootstrap_draws=bootstrap_draws,
        block_size=block_size,
        seed=seed,
        ridge_alpha=ridge_alpha,
    )
    regimes = assign_regimes(X)

    return {
        "status": "FINAI_CAUSAL_RESEARCH_PIPELINE_READY",
        "dataset": {
            "n_samples": int(X.shape[0]),
            "n_variables": int(X.shape[1]),
            "node_ids": labels,
        },
        "discovery": {
            "contemporaneous": contemporaneous,
            "temporal": temporal,
            "stability": stability,
            "consensus": consensus,
            "calibration": calibration,
        },
        "regime_summary": {
            str(regime): int(np.sum(regimes == regime))
            for regime in np.unique(regimes)
        },
        "production_boundary": (
            "This bundle is research analytics. Consensus graphs require explicit "
            "approval before research counterfactual execution and are not production "
            "investment decisions."
        ),
    }
