"""Walk-forward ensemble for market-movement scenarios.

This module does not claim a universally best market model. It evaluates several
model families on the available historical window and reports their backtest
error/directional accuracy before forming a weighted ensemble scenario.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Dict, List

import numpy as np
from sklearn.ensemble import HistGradientBoostingRegressor, RandomForestRegressor
from sklearn.linear_model import LinearRegression


@dataclass
class ModelReport:
    name: str
    available: bool
    mae_percent: float | None
    directional_accuracy_percent: float | None
    next_return_percent: float | None
    weight: float


def _features(closes: np.ndarray, volumes: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    X, y = [], []
    for i in range(10, len(closes) - 1):
        returns = np.diff(np.log(closes[: i + 1]))
        lag = [returns[-k] for k in (1, 2, 3, 5, 8, 10)]
        mean5 = float(np.mean(returns[-5:]))
        mean10 = float(np.mean(returns[-10:]))
        vol10 = float(np.std(returns[-10:]))
        vol_ratio = float(volumes[i] / max(np.mean(volumes[max(0, i - 10): i + 1]), 1e-9))
        X.append(lag + [mean5, mean10, vol10, vol_ratio])
        y.append(float(returns[-1 + 1]))
    return np.asarray(X, dtype=float), np.asarray(y, dtype=float)


def _dataset(closes: np.ndarray, volumes: np.ndarray):
    returns = np.diff(np.log(closes))
    X, y = [], []
    for i in range(10, len(returns)):
        recent = returns[:i]
        row = [
            recent[-k] for k in (1, 2, 3, 5, 8, 10)
        ] + [
            float(np.mean(recent[-5:])),
            float(np.mean(recent[-10:])),
            float(np.std(recent[-10:])),
            float(volumes[i] / max(np.mean(volumes[max(0, i - 10): i + 1]), 1e-9)),
        ]
        X.append(row)
        y.append(float(returns[i]))
    return np.asarray(X, dtype=float), np.asarray(y, dtype=float)


def _latest_features(closes: np.ndarray, volumes: np.ndarray) -> np.ndarray:
    returns = np.diff(np.log(closes))
    return np.asarray([[
        returns[-k] for k in (1, 2, 3, 5, 8, 10)
    ] + [
        float(np.mean(returns[-5:])),
        float(np.mean(returns[-10:])),
        float(np.std(returns[-10:])),
        float(volumes[-1] / max(np.mean(volumes[-10:]), 1e-9)),
    ]], dtype=float)


def _metrics(actual: np.ndarray, predicted: np.ndarray) -> tuple[float, float]:
    errors = np.abs(predicted - actual) * 100
    mae = float(np.mean(errors))
    directional = float(np.mean(np.sign(predicted) == np.sign(actual)) * 100)
    return mae, directional


def analyze_market_movement(bars: List[Any]) -> Dict[str, Any]:
    if len(bars) < 80:
        return {
            "status": "INSUFFICIENT_HISTORY",
            "message": "At least 80 OHLCV bars are recommended for a meaningful walk-forward comparison.",
            "models": [],
            "ensemble": None,
        }

    closes = np.asarray([float(bar.close) for bar in bars], dtype=float)
    volumes = np.asarray([float(bar.volume or 0) for bar in bars], dtype=float)

    log_returns = np.diff(np.log(closes))
    split = max(40, int(len(log_returns) * 0.7))
    train_close = closes[: split + 1]
    test_returns = log_returns[split:]
    reports: List[ModelReport] = []
    forecasts: Dict[str, float] = {}

    # Persistence / momentum baseline.
    momentum_pred = float(np.mean(log_returns[-5:]))
    baseline_pred = np.repeat(momentum_pred, len(test_returns))
    mae, directional = _metrics(test_returns, baseline_pred)
    reports.append(ModelReport("Momentum baseline", True, mae, directional, momentum_pred * 100, 0.0))
    forecasts["Momentum baseline"] = momentum_pred

    # Linear trend on normalized time.
    x_train = np.arange(len(train_close), dtype=float).reshape(-1, 1)
    lr = LinearRegression().fit(x_train, train_close)
    future_price = float(lr.predict([[len(closes)]])[0])
    linear_pred = future_price / closes[-1] - 1
    test_x = np.arange(split + 1, len(closes), dtype=float).reshape(-1, 1)
    lr_prices = lr.predict(test_x)
    lr_returns = np.diff(lr_prices) / np.maximum(lr_prices[:-1], 1e-12)
    if len(lr_returns) == len(test_returns):
        mae, directional = _metrics(test_returns, lr_returns)
    else:
        mae, directional = (mae, directional)
    reports.append(ModelReport("Linear trend", True, mae, directional, linear_pred * 100, 0.0))
    forecasts["Linear trend"] = linear_pred

    X, y = _dataset(closes, volumes)
    latest = _latest_features(closes, volumes)
    test_start = max(40, int(len(X) * 0.7))
    X_train, X_test = X[:test_start], X[test_start:]
    y_train, y_test = y[:test_start], y[test_start:]

    rf = RandomForestRegressor(
        n_estimators=180, max_depth=5, min_samples_leaf=4,
        random_state=42, n_jobs=-1,
    )
    rf.fit(X_train, y_train)
    rf_pred = float(rf.predict(latest)[0])
    rf_test = rf.predict(X_test)
    mae, directional = _metrics(y_test, rf_test)
    reports.append(ModelReport("Random forest", True, mae, directional, rf_pred * 100, 0.0))
    forecasts["Random forest"] = rf_pred

    hgb = HistGradientBoostingRegressor(
        max_depth=4, learning_rate=0.04, max_iter=160,
        l2_regularization=0.2, random_state=42,
    )
    hgb.fit(X_train, y_train)
    hgb_pred = float(hgb.predict(latest)[0])
    hgb_test = hgb.predict(X_test)
    mae, directional = _metrics(y_test, hgb_test)
    reports.append(ModelReport("Gradient boosting", True, mae, directional, hgb_pred * 100, 0.0))
    forecasts["Gradient boosting"] = hgb_pred

    scored = []
    for report in reports:
        quality = 1.0 / max(report.mae_percent or 1.0, 0.0001)
        report.weight = quality
        scored.append(quality)

    total_weight = sum(scored) or 1.0
    for report in reports:
        report.weight /= total_weight

    ensemble_return = sum(report.weight * forecasts[report.name] for report in reports)
    agreement = sum(report.weight for report in reports if np.sign(forecasts[report.name]) == np.sign(ensemble_return))

    last_close = float(closes[-1])
    return {
        "status": "ANALYZED",
        "bar_count": len(bars),
        "models": [asdict(report) for report in reports],
        "ensemble": {
            "next_return_scenario_percent": round(ensemble_return * 100, 4),
            "direction": "upside" if ensemble_return > 0 else "downside" if ensemble_return < 0 else "neutral",
            "model_agreement_percent": round(agreement * 100, 2),
            "reference_last_close": last_close,
        },
        "method": "Walk-forward comparison of momentum baseline, linear trend, random forest and histogram gradient boosting.",
        "warning": "This is a research scenario, not a guaranteed price prediction. Backtest metrics are in-sample to the requested historical window and can change with regime shifts.",
    }
