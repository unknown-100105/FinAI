"""Dependency-light calibration metrics for predicted binary-event probabilities.

Use only on held-out predictions for a clearly defined event. This module does
not turn causal edge coefficients into probabilities or establish causality.
"""
from __future__ import annotations
import math
from typing import Sequence
import numpy as np


def _validate(probabilities: Sequence[float], outcomes: Sequence[int]):
    p = np.asarray(probabilities, dtype=float)
    y = np.asarray(outcomes, dtype=float)
    if p.ndim != 1 or y.ndim != 1 or p.size != y.size or p.size == 0:
        raise ValueError("inputs must be non-empty equal-length 1-D arrays")
    if not np.isfinite(p).all() or not np.isfinite(y).all():
        raise ValueError("inputs must be finite")
    if ((p < 0) | (p > 1)).any():
        raise ValueError("probabilities must be within [0, 1]")
    if not np.isin(y, [0.0, 1.0]).all():
        raise ValueError("outcomes must be binary values 0 or 1")
    return p, y


def calibration_metrics(probabilities: Sequence[float], outcomes: Sequence[int], *, n_bins: int = 10) -> dict:
    """Return Brier score, log loss, ECE and reliability-bin diagnostics."""
    p, y = _validate(probabilities, outcomes)
    if not isinstance(n_bins, int) or not 2 <= n_bins <= 100:
        raise ValueError("n_bins must be an integer between 2 and 100")
    clipped = np.clip(p, 1e-12, 1.0 - 1e-12)
    brier = float(np.mean((p - y) ** 2))
    loss = float(-np.mean(y * np.log(clipped) + (1-y) * np.log(1-clipped)))
    edges = np.linspace(0, 1, n_bins + 1)
    bins, ece = [], 0.0
    for i in range(n_bins):
        mask = (p >= edges[i]) & ((p < edges[i+1]) if i < n_bins-1 else (p <= edges[i+1]))
        count = int(mask.sum())
        mean_p = float(p[mask].mean()) if count else None
        observed = float(y[mask].mean()) if count else None
        if count:
            ece += count / len(p) * abs(mean_p - observed)
        bins.append({"bin": i, "lower": float(edges[i]), "upper": float(edges[i+1]), "count": count, "mean_probability": mean_p, "observed_rate": observed})
    return {"status": "CALIBRATION_METRICS_READY", "n_samples": int(len(p)), "n_positive": int(y.sum()), "n_bins": n_bins, "brier_score": brier, "log_loss": loss, "expected_calibration_error": float(ece), "bins": bins, "limitations": ["ECE depends on binning.", "Use chronological/walk-forward evaluation for financial time series.", "Calibration metrics do not establish causal validity."]}


def chronological_split(probabilities: Sequence[float], outcomes: Sequence[int], *, test_fraction: float = 0.2):
    """Split ordered observations without shuffling future data into training."""
    p, y = _validate(probabilities, outcomes)
    if not math.isfinite(float(test_fraction)) or not 0.1 <= test_fraction <= 0.5:
        raise ValueError("test_fraction must be between 0.1 and 0.5")
    split = int(len(p) * (1 - float(test_fraction)))
    if split < 1 or split >= len(p):
        raise ValueError("not enough observations for split")
    return p[:split], y[:split], p[split:], y[split:]
