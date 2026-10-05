"""Regime-aware evaluation utilities for FinAI research models."""
from __future__ import annotations

from typing import Any, Mapping, Sequence

import numpy as np


def assign_regimes(
    samples: Sequence[Sequence[float]],
    *,
    volatility_window: int = 20,
    high_vol_quantile: float = 0.80,
) -> np.ndarray:
    X = np.asarray(samples, dtype=float)
    if X.ndim != 2 or X.shape[0] <= volatility_window:
        raise ValueError("insufficient samples for regime assignment")
    if not np.isfinite(X).all():
        raise ValueError("samples contain non-finite values")
    if not 0.5 < high_vol_quantile < 1.0:
        raise ValueError("high_vol_quantile must be between 0.5 and 1.0")
    row_vol = np.sqrt(np.mean(X * X, axis=1))
    rolling = np.array([
        np.std(row_vol[max(0, i - volatility_window + 1): i + 1])
        for i in range(len(row_vol))
    ])
    threshold = float(np.quantile(rolling[volatility_window:], high_vol_quantile))
    return np.where(rolling >= threshold, "high_volatility", "baseline")


def evaluate_predictions(
    y_true: Sequence[float],
    y_pred: Sequence[float],
    regimes: Sequence[str],
) -> dict[str, Any]:
    y = np.asarray(y_true, dtype=float)
    p = np.asarray(y_pred, dtype=float)
    r = np.asarray(regimes)
    if len(y) != len(p) or len(y) != len(r) or len(y) == 0:
        raise ValueError("prediction arrays must align")
    if not np.isfinite(y).all() or not np.isfinite(p).all():
        raise ValueError("predictions must be finite")

    results = {}
    for regime in np.unique(r):
        mask = r == regime
        mae = float(np.mean(np.abs(y[mask] - p[mask])))
        rmse = float(np.sqrt(np.mean((y[mask] - p[mask]) ** 2)))
        results[str(regime)] = {
            "samples": int(mask.sum()),
            "mae": round(mae, 6),
            "rmse": round(rmse, 6),
        }
    return {
        "status": "REGIME_BENCHMARK_READY",
        "regimes": results,
        "semantics": "Regime-conditioned descriptive evaluation; not evidence of causal identification.",
    }
