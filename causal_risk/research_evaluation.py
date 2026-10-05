"""Research evaluation utilities for the FinAI causal stress loop."""
from __future__ import annotations

from typing import Any, Mapping, Sequence

import numpy as np


def _finite_vector(values: Sequence[float], name: str) -> np.ndarray:
    array = np.asarray(values, dtype=float).reshape(-1)
    if len(array) < 1 or not np.isfinite(array).all():
        raise ValueError(f"{name} must be a non-empty finite vector")
    return array


def tail_backtest_metrics(
    realized_loss: Sequence[float],
    forecast_var: Sequence[float],
    *,
    level: float = 0.95,
) -> dict[str, Any]:
    """Evaluate exceedance coverage of a VaR series without assuming iid data."""
    realized = _finite_vector(realized_loss, "realized_loss")
    var = _finite_vector(forecast_var, "forecast_var")
    if len(realized) != len(var):
        raise ValueError("realized_loss and forecast_var must align")
    if not 0.5 < level < 1.0:
        raise ValueError("level must be between 0.5 and 1.0")
    exceedances = realized > var
    expected_rate = 1.0 - level
    observed_rate = float(np.mean(exceedances))
    return {
        "status": "TAIL_BACKTEST_READY",
        "observations": int(len(realized)),
        "level": float(level),
        "expected_exceedance_rate": round(expected_rate, 6),
        "observed_exceedance_rate": round(observed_rate, 6),
        "coverage_error": round(float(abs(observed_rate - expected_rate)), 6),
        "exceedance_count": int(np.sum(exceedances)),
        "semantics": (
            "Unconditional VaR coverage diagnostic. It does not prove model "
            "correctness or independence of exceedances."
        ),
    }


def scenario_quality_metrics(
    scenarios: Sequence[Sequence[float]],
    empirical_samples: Sequence[Sequence[float]] | None = None,
    *,
    causal_edge_matrix: Sequence[Sequence[float]] | None = None,
) -> dict[str, Any]:
    """Measure diversity, empirical support and causal sign alignment."""
    X = np.asarray(scenarios, dtype=float)
    if X.ndim != 2 or X.shape[0] < 2 or X.shape[1] < 1:
        raise ValueError("scenarios must contain at least two rows")
    if not np.isfinite(X).all():
        raise ValueError("scenarios must be finite")

    pairwise = np.linalg.norm(X[:, None, :] - X[None, :, :], axis=2)
    upper = pairwise[np.triu_indices(len(X), k=1)]
    diversity = float(np.mean(upper)) if len(upper) else 0.0

    support_distance = None
    if empirical_samples is not None:
        E = np.asarray(empirical_samples, dtype=float)
        if E.ndim != 2 or E.shape[1] != X.shape[1] or not np.isfinite(E).all():
            raise ValueError("empirical_samples must align with scenario dimensions")
        nearest = []
        for row in X:
            nearest.append(float(np.min(np.linalg.norm(E - row, axis=1))))
        support_distance = float(np.mean(nearest))

    causal_alignment = None
    if causal_edge_matrix is not None:
        edges = np.asarray(causal_edge_matrix, dtype=float)
        if edges.shape != (X.shape[1], X.shape[1]):
            raise ValueError("causal_edge_matrix must match scenario dimension")
        mask = edges != 0
        if np.any(mask):
            relation = edges[mask][None, :] * (
                X[:, :, None] * X[:, None, :]
            )[:, mask]
            causal_alignment = float(np.mean(1.0 / (1.0 + np.exp(-relation))))
        else:
            causal_alignment = 1.0

    return {
        "status": "SCENARIO_QUALITY_READY",
        "scenario_count": int(X.shape[0]),
        "factor_count": int(X.shape[1]),
        "mean_pairwise_distance": round(diversity, 6),
        "mean_nearest_empirical_distance": (
            round(support_distance, 6) if support_distance is not None else None
        ),
        "causal_direction_alignment": (
            round(causal_alignment, 6) if causal_alignment is not None else None
        ),
        "semantics": (
            "Descriptive scenario-quality measures for research comparison; "
            "no single metric establishes scenario realism."
        ),
    }


def ablation_summary(
    results: Mapping[str, Mapping[str, float]],
    *,
    primary_metric: str,
) -> dict[str, Any]:
    """Create a transparent metric table without declaring a universal winner."""
    if not results:
        raise ValueError("results must contain at least one model")
    rows = []
    for name, metrics in results.items():
        if primary_metric not in metrics:
            raise ValueError(f"{name} is missing primary metric {primary_metric}")
        rows.append({
            "model": str(name),
            "primary_metric": round(float(metrics[primary_metric]), 6),
            "metrics": {str(k): float(v) for k, v in metrics.items()},
        })
    rows.sort(key=lambda item: item["primary_metric"])
    return {
        "status": "ABLATION_SUMMARY_READY",
        "primary_metric": primary_metric,
        "rows": rows,
        "semantics": (
            "Ordered numerical results for an explicitly chosen metric. "
            "Interpretation and statistical significance require the study design."
        ),
    }


def perturb_features(
    samples: Sequence[Sequence[float]],
    *,
    scale: float = 1.0,
    missing_columns: Sequence[int] = (),
    noise_std: float = 0.0,
    seed: int = 42,
) -> np.ndarray:
    """Create deterministic robustness/OOD perturbations."""
    X = np.asarray(samples, dtype=float).copy()
    if X.ndim != 2 or not np.isfinite(X).all():
        raise ValueError("samples must be a finite 2-D matrix")
    if scale <= 0 or noise_std < 0:
        raise ValueError("scale must be positive and noise_std non-negative")
    if any(int(index) < 0 or int(index) >= X.shape[1] for index in missing_columns):
        raise ValueError("missing_columns contains an invalid index")
    rng = np.random.default_rng(seed)
    X *= float(scale)
    if noise_std:
        X += rng.normal(scale=noise_std, size=X.shape)
    for index in missing_columns:
        X[:, int(index)] = 0.0
    return X
