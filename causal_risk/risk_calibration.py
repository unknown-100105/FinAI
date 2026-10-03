"""Risk-channel calibration and provenance utilities.

This module separates explicit scenario parameters from empirical edge
calibration. It provides a reproducible supervised calibrator for future
outcome-labelled datasets without silently treating associations as causal.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping, Sequence

import numpy as np
from sklearn.linear_model import Ridge

DEFAULT_CONFIG_PATH = Path(__file__).resolve().parents[1] / "configs" / "causal_risk_calibration.json"


def load_risk_calibration(path: str | Path | None = None) -> dict[str, Any]:
    config_path = Path(path) if path is not None else DEFAULT_CONFIG_PATH
    with config_path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    if not isinstance(payload, dict) or "coefficients" not in payload:
        raise ValueError("risk calibration config must contain coefficients")
    return payload


def _standardize(X: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    mean = np.mean(X, axis=0)
    scale = np.std(X, axis=0)
    safe_scale = np.where(scale < 1e-12, 1.0, scale)
    return (X - mean) / safe_scale, mean, safe_scale


def calibrate_risk_target(
    samples: Sequence[Sequence[float]],
    target: Sequence[float],
    feature_names: Sequence[str],
    *,
    alpha: float = 1.0,
) -> dict[str, Any]:
    """Fit a chronological Ridge model for an observed risk outcome.

    This is an empirical association calibrator. It does not identify causal
    effects and requires an externally defined, outcome-labelled target.
    """
    X = np.asarray(samples, dtype=float)
    y = np.asarray(target, dtype=float)
    names = [str(name).strip() for name in feature_names]
    if X.ndim != 2 or X.shape[0] < 60 or X.shape[1] < 2:
        raise ValueError("samples must be 2-D with at least 60 rows and 2 variables")
    if y.ndim != 1 or len(y) != X.shape[0]:
        raise ValueError("target must be a 1-D vector aligned to samples")
    if len(names) != X.shape[1] or len(set(names)) != len(names):
        raise ValueError("feature_names must uniquely match sample columns")
    if not np.isfinite(X).all() or not np.isfinite(y).all():
        raise ValueError("samples and target must be finite")
    if alpha <= 0:
        raise ValueError("alpha must be positive")

    split = int(np.floor(len(X) * 0.8))
    train_x, test_x = X[:split], X[split:]
    train_y, test_y = y[:split], y[split:]
    train_z, mean, scale = _standardize(train_x)
    test_z = (test_x - mean) / scale

    y_mean = float(np.mean(train_y))
    y_scale = float(np.std(train_y))
    y_scale = 1.0 if y_scale < 1e-12 else y_scale
    train_zy = (train_y - y_mean) / y_scale
    model = Ridge(alpha=float(alpha))
    model.fit(train_z, train_zy)

    pred = model.predict(test_z)
    total = float(np.sum((test_y - np.mean(test_y)) ** 2))
    r2 = 0.0 if total < 1e-12 else 1.0 - float(np.sum((test_y - pred * y_scale - y_mean) ** 2)) / total

    return {
        "status":"EMPIRICAL_RISK_CALIBRATION_READY",
        "estimator":"Ridge",
        "alpha":float(alpha),
        "train_samples":int(len(train_x)),
        "test_samples":int(len(test_x)),
        "chronological_split":True,
        "coefficients":{
            name:round(float(value),6)
            for name,value in zip(names,model.coef_)
        },
        "test_r2":round(float(r2),6),
        "test_mae":round(float(np.mean(np.abs(test_y - (pred * y_scale + y_mean)))),6),
        "semantics":"Standardized predictive associations for an externally observed risk target; not identified causal effects."
    }
