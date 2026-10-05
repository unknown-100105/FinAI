"""Research-grade walk-forward market scenario ensemble for FinAI.

The module reports historical validation evidence across several model families.
It intentionally avoids a universal "best model" claim and does not turn a
historical benchmark into a guaranteed forecast.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Dict, List

import numpy as np
from sklearn.ensemble import ExtraTreesRegressor, HistGradientBoostingRegressor, RandomForestRegressor
from sklearn.linear_model import HuberRegressor, Ridge
from sklearn.metrics import mean_absolute_error, mean_squared_error
from sklearn.model_selection import TimeSeriesSplit
from sklearn.neural_network import MLPRegressor
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler


@dataclass
class ModelReport:
    name: str
    available: bool
    mae_percent: float | None
    rmse_percent: float | None
    directional_accuracy_percent: float | None
    cv_mae_percent: float | None
    cv_mae_std_percent: float | None
    next_return_percent: float | None
    weight: float
    stability: str = "unknown"


FEATURE_NAMES = (
    "return_lag_1", "return_lag_2", "return_lag_3", "return_lag_5",
    "return_lag_8", "return_lag_10", "mean_return_5", "mean_return_10",
    "volatility_10", "volatility_20", "volume_ratio", "volume_zscore",
    "price_momentum_5", "price_momentum_20", "return_skew_20",
)


def _safe_returns(closes: np.ndarray) -> np.ndarray:
    clean = np.maximum(np.asarray(closes, dtype=float), 1e-12)
    return np.diff(np.log(clean))


def _features(closes: np.ndarray, volumes: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    returns = _safe_returns(closes)
    X, y = [], []
    for i in range(20, len(returns)):
        recent = returns[:i]
        vol_window = volumes[max(0, i - 20): i + 1]
        mean_volume = max(float(np.mean(vol_window)), 1e-9)
        volume_std = max(float(np.std(vol_window)), 1e-9)
        last20 = recent[-20:]
        skew = float(np.mean(((last20 - np.mean(last20)) / max(np.std(last20), 1e-9)) ** 3))
        row = [
            recent[-1], recent[-2], recent[-3], recent[-5], recent[-8], recent[-10],
            float(np.mean(recent[-5:])), float(np.mean(recent[-10:])),
            float(np.std(recent[-10:])), float(np.std(recent[-20:])),
            float(volumes[i] / mean_volume),
            float((volumes[i] - np.mean(vol_window)) / volume_std),
            float(np.sum(recent[-5:])),
            float(np.sum(recent[-20:])),
            skew,
        ]
        X.append(row)
        y.append(float(returns[i]))
    return np.asarray(X, dtype=float), np.asarray(y, dtype=float)


def _latest_features(closes: np.ndarray, volumes: np.ndarray) -> np.ndarray:
    returns = _safe_returns(closes)
    vol_window = volumes[-21:]
    mean_volume = max(float(np.mean(vol_window)), 1e-9)
    volume_std = max(float(np.std(vol_window)), 1e-9)
    last20 = returns[-20:]
    skew = float(np.mean(((last20 - np.mean(last20)) / max(np.std(last20), 1e-9)) ** 3))
    return np.asarray([[
        returns[-1], returns[-2], returns[-3], returns[-5], returns[-8], returns[-10],
        float(np.mean(returns[-5:])), float(np.mean(returns[-10:])),
        float(np.std(returns[-10:])), float(np.std(returns[-20:])),
        float(volumes[-1] / mean_volume),
        float((volumes[-1] - np.mean(vol_window)) / volume_std),
        float(np.sum(returns[-5:])),
        float(np.sum(returns[-20:])),
        skew,
    ]], dtype=float)


def _models() -> Dict[str, Any]:
    return {
        "ridge": make_pipeline(StandardScaler(), Ridge(alpha=1.0)),
        "huber": make_pipeline(StandardScaler(), HuberRegressor(epsilon=1.35, max_iter=500)),
        "random_forest": RandomForestRegressor(
            n_estimators=220, max_depth=6, min_samples_leaf=4, random_state=42, n_jobs=-1
        ),
        "extra_trees": ExtraTreesRegressor(
            n_estimators=220, max_depth=8, min_samples_leaf=3, random_state=42, n_jobs=-1
        ),
        "hist_gradient_boosting": HistGradientBoostingRegressor(
            learning_rate=0.04, max_iter=180, max_leaf_nodes=15,
            l2_regularization=0.2, random_state=42
        ),
        "mlp": make_pipeline(
            StandardScaler(),
            MLPRegressor(hidden_layer_sizes=(48, 24), early_stopping=True,
                         validation_fraction=0.15, max_iter=700, random_state=42)
        ),
    }


def _regression_metrics(actual: np.ndarray, predicted: np.ndarray) -> tuple[float, float, float]:
    mae = float(mean_absolute_error(actual, predicted) * 100)
    rmse = float(np.sqrt(mean_squared_error(actual, predicted)) * 100)
    directional = float(np.mean(np.sign(predicted) == np.sign(actual)) * 100)
    return mae, rmse, directional


def _walk_forward_cv(model: Any, X: np.ndarray, y: np.ndarray) -> tuple[float | None, float | None]:
    if len(X) < 45:
        return None, None
    splits = min(3, max(2, len(X) // 25))
    tscv = TimeSeriesSplit(n_splits=splits)
    scores: List[float] = []
    for train_idx, test_idx in tscv.split(X):
        try:
            model.fit(X[train_idx], y[train_idx])
            pred = model.predict(X[test_idx])
            scores.append(float(mean_absolute_error(y[test_idx], pred) * 100))
        except Exception:
            continue
    if not scores:
        return None, None
    return round(float(np.mean(scores)), 4), round(float(np.std(scores)), 4)


def analyze_market_movement(bars: List[Any]) -> Dict[str, Any]:
    if len(bars) < 100:
        return {
            "status": "INSUFFICIENT_HISTORY",
            "message": "At least 100 OHLCV bars are recommended for the enhanced walk-forward comparison.",
            "models": [],
            "ensemble": None,
        }

    closes = np.asarray([float(bar.close) for bar in bars], dtype=float)
    volumes = np.asarray([float(bar.volume or 0) for bar in bars], dtype=float)
    if not np.isfinite(closes).all() or not np.isfinite(volumes).all() or np.any(closes <= 0):
        raise ValueError("OHLCV contains invalid close/volume values")

    X, y = _features(closes, volumes)
    latest = _latest_features(closes, volumes)
    split = max(50, int(len(X) * 0.8))
    split = min(split, len(X) - 1)
    X_train, X_test = X[:split], X[split:]
    y_train, y_test = y[:split], y[split:]

    reports: List[ModelReport] = []
    forecasts: Dict[str, float] = {}

    # Naive momentum baseline establishes whether ML beats a simple reference.
    momentum_pred = float(np.mean(y_train[-5:]))
    baseline_test = np.repeat(momentum_pred, len(y_test))
    mae, rmse, directional = _regression_metrics(y_test, baseline_test)
    reports.append(ModelReport(
        "Momentum baseline", True, round(mae, 4), round(rmse, 4),
        round(directional, 2), None, None, round(momentum_pred * 100, 4), 0.0, "reference"
    ))
    forecasts["Momentum baseline"] = momentum_pred

    for name, model in _models().items():
        try:
            cv_mae, cv_std = _walk_forward_cv(model, X_train, y_train)
            model.fit(X_train, y_train)
            prediction = float(model.predict(latest)[0])
            test_prediction = model.predict(X_test)
            mae, rmse, directional = _regression_metrics(y_test, test_prediction)
            stability = "stable" if cv_std is not None and cv_std <= max(0.5, cv_mae * 0.35) else "variable"
            reports.append(ModelReport(
                name.replace("_", " ").title(),
                True, round(mae, 4), round(rmse, 4), round(directional, 2),
                cv_mae, cv_std, round(prediction * 100, 4), 0.0, stability
            ))
            forecasts[reports[-1].name] = prediction
        except Exception as exc:
            reports.append(ModelReport(
                name.replace("_", " ").title(), False, None, None, None,
                None, None, None, 0.0, f"error: {str(exc)[:120]}"
            ))

    qualities = []
    for report in reports:
        if report.mae_percent is not None and report.mae_percent > 0:
            # Combine holdout error and CV error to avoid overweighting one lucky split.
            cv = report.cv_mae_percent if report.cv_mae_percent is not None else report.mae_percent
            quality = 1.0 / max((report.mae_percent * 0.6 + cv * 0.4), 0.01)
        else:
            quality = 0.0
        qualities.append(quality)

    total = sum(qualities) or 1.0
    for report, quality in zip(reports, qualities):
        report.weight = round(quality / total, 4)

    usable = [report for report in reports if report.available and report.name in forecasts]
    if not usable:
        return {"status": "MODEL_FAILURE", "models": [asdict(report) for report in reports], "ensemble": None}

    ensemble_return = sum(report.weight * forecasts[report.name] for report in usable)
    agreement = sum(
        report.weight
        for report in usable
        if np.sign(forecasts[report.name]) == np.sign(ensemble_return)
    )
    last_close = float(closes[-1])
    return {
        "status": "ANALYZED",
        "bar_count": len(bars),
        "feature_count": len(FEATURE_NAMES),
        "features": list(FEATURE_NAMES),
        "models": [asdict(report) for report in reports],
        "ensemble": {
            "next_return_scenario_percent": round(ensemble_return * 100, 4),
            "direction": "upside" if ensemble_return > 0 else "downside" if ensemble_return < 0 else "neutral",
            "model_agreement_percent": round(agreement * 100, 2),
            "reference_last_close": last_close,
            "ensemble_method": "error-weighted holdout + time-series-CV evidence",
            "uncertainty_note": "Agreement is model-consistency evidence, not forecast certainty.",
        },
        "validation": {
            "split": "chronological 80/20 holdout",
            "cross_validation": "expanding-window TimeSeriesSplit",
            "train_samples": len(y_train),
            "test_samples": len(y_test),
        },
        "method": "Multi-model walk-forward research arena with naive baseline, linear robust regression, tree ensembles and MLP.",
        "warning": "Historical validation can fail under regime shifts. This module reports scenarios and model evidence, not guaranteed future returns.",
    }
