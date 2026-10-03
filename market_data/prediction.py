"""Walk-forward market movement model arena for FinAI.

The engine deliberately avoids claiming a universally "best" predictor. It trains
several model families on the same causal feature set, evaluates them chronologically,
and produces an auditable ensemble plus feature-level explanations.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Dict, List, Sequence, Tuple

import numpy as np
from sklearn.ensemble import ExtraTreesClassifier, GradientBoostingClassifier, HistGradientBoostingClassifier, RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.neural_network import MLPClassifier
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from .models import MarketBar


FEATURE_NAMES = (
    "return_1",
    "return_3",
    "return_5",
    "sma_5_gap",
    "sma_20_gap",
    "ema_12_gap",
    "volatility_10",
    "volume_ratio",
    "range_pct",
    "rsi_14",
)


@dataclass(frozen=True)
class ModelResult:
    model_id: str
    family: str
    status: str
    direction: str
    probability_up: float | None
    validation_accuracy: float | None
    validation_samples: int
    weight: float
    feature_importance: Dict[str, float]
    note: str = ""


def _feature_row(values: Sequence[float], volumes: Sequence[float], index: int) -> List[float] | None:
    if index < 20:
        return None
    window = np.asarray(values[: index + 1], dtype=float)
    close = float(window[-1])
    if close <= 0:
        return None

    def ret(period: int) -> float:
        if len(window) <= period or window[-1 - period] == 0:
            return 0.0
        return float(window[-1] / window[-1 - period] - 1.0)

    def sma(period: int) -> float:
        return float(np.mean(window[-period:]))

    ema12 = float(window[0])
    alpha = 2.0 / 13.0
    for value in window[1:]:
        ema12 = alpha * float(value) + (1.0 - alpha) * ema12

    returns = np.diff(window[-11:]) / window[-11:-1]
    volatility = float(np.std(returns)) if len(returns) > 1 else 0.0

    vol_window = np.asarray(volumes[: index + 1], dtype=float)
    vol = float(vol_window[-1]) if len(vol_window) else 0.0
    prior_volumes = vol_window[-21:-1]
    volume_ratio = vol / float(np.mean(prior_volumes)) if prior_volumes.size and np.mean(prior_volumes) > 0 else 1.0

    gains = []
    losses = []
    changes = np.diff(window[-15:])
    for change in changes:
        gains.append(max(float(change), 0.0))
        losses.append(max(-float(change), 0.0))
    avg_gain = float(np.mean(gains)) if gains else 0.0
    avg_loss = float(np.mean(losses)) if losses else 0.0
    rsi = 100.0 if avg_loss == 0 else 100.0 - 100.0 / (1.0 + avg_gain / avg_loss)

    return [
        ret(1),
        ret(3),
        ret(5),
        close / sma(5) - 1.0,
        close / sma(20) - 1.0,
        close / ema12 - 1.0,
        volatility,
        volume_ratio,
        (float(np.max(window[-5:])) - float(np.min(window[-5:]))) / close,
        rsi / 100.0,
    ]


def _dataset(bars: Sequence[MarketBar], horizon: int) -> Tuple[np.ndarray, np.ndarray]:
    closes = [float(b.close) for b in bars]
    volumes = [float(b.volume or 0.0) for b in bars]
    rows: List[List[float]] = []
    targets: List[int] = []
    for i in range(20, max(20, len(bars) - horizon)):
        row = _feature_row(closes, volumes, i)
        if row is None:
            continue
        future = closes[i + horizon]
        rows.append(row)
        targets.append(1 if future > closes[i] else 0)
    if not rows:
        return np.empty((0, len(FEATURE_NAMES))), np.empty((0,), dtype=int)
    return np.asarray(rows, dtype=float), np.asarray(targets, dtype=int)


def _models() -> Dict[str, Any]:
    return {
        "logistic": make_pipeline(StandardScaler(), LogisticRegression(max_iter=1000, random_state=42)),
        "random_forest": RandomForestClassifier(n_estimators=240, min_samples_leaf=3, random_state=42, n_jobs=-1),
        "extra_trees": ExtraTreesClassifier(n_estimators=240, min_samples_leaf=3, random_state=42, n_jobs=-1),
        "gradient_boosting": GradientBoostingClassifier(random_state=42),
        "hist_gradient_boosting": HistGradientBoostingClassifier(max_iter=180, random_state=42),
        "mlp": make_pipeline(StandardScaler(), MLPClassifier(hidden_layer_sizes=(32, 16), max_iter=500, early_stopping=True, random_state=42)),
    }


def _importance(model: Any) -> Dict[str, float]:
    estimator = getattr(model, "named_steps", {}).get("logisticregression", model)
    raw = getattr(estimator, "feature_importances_", None)
    if raw is None:
        coef = getattr(estimator, "coef_", None)
        if coef is not None:
            raw = np.abs(np.asarray(coef)).mean(axis=0)
    if raw is None:
        return {name: 0.0 for name in FEATURE_NAMES}
    values = np.asarray(raw, dtype=float).reshape(-1)
    total = float(values.sum()) or 1.0
    return {name: round(float(value / total), 4) for name, value in zip(FEATURE_NAMES, values)}


def _direction(probability: float | None) -> str:
    if probability is None:
        return "unavailable"
    if probability >= 0.55:
        return "bullish"
    if probability <= 0.45:
        return "bearish"
    return "neutral"


def run_model_arena(bars: Sequence[MarketBar], horizon: int = 5) -> Dict[str, Any]:
    """Train/evaluate multiple models chronologically and create an ensemble."""
    if horizon < 1:
        raise ValueError("horizon must be positive")
    X, y = _dataset(bars, horizon)
    if len(X) < 60 or len(np.unique(y)) < 2:
        return {
            "status": "INSUFFICIENT_DATA",
            "horizon": horizon,
            "models": [],
            "ensemble": {"direction": "unavailable", "probability_up": None, "confidence": None},
            "features": list(FEATURE_NAMES),
            "note": "At least 60 labelled observations with both classes are required for a reliable model arena.",
        }

    split = max(40, int(len(X) * 0.8))
    if split >= len(X):
        split = len(X) - 1
    X_train, X_test = X[:split], X[split:]
    y_train, y_test = y[:split], y[split:]
    latest_row = X[-1].reshape(1, -1)

    results: List[ModelResult] = []
    probabilities: List[float] = []
    weights: List[float] = []

    for model_id, model in _models().items():
        try:
            model.fit(X_train, y_train)
            pred = model.predict(X_test)
            accuracy = float(np.mean(pred == y_test)) if len(y_test) else None
            probability = float(model.predict_proba(latest_row)[0][1]) if hasattr(model, "predict_proba") else float(model.predict(latest_row)[0])
            score = max(0.05, (accuracy or 0.5) - 0.5)
            weight = score
            probabilities.append(probability)
            weights.append(weight)
            results.append(ModelResult(
                model_id=model_id,
                family=type(getattr(model, "steps", [(None, model)])[-1][1]).__name__ if hasattr(model, "steps") else type(model).__name__,
                status="READY",
                direction=_direction(probability),
                probability_up=round(probability, 4),
                validation_accuracy=None if accuracy is None else round(accuracy, 4),
                validation_samples=len(y_test),
                weight=0.0,
                feature_importance=_importance(model),
                note="Chronological holdout; no random train/test shuffle.",
            ))
        except Exception as exc:
            results.append(ModelResult(
                model_id=model_id, family=type(model).__name__, status="ERROR",
                direction="unavailable", probability_up=None, validation_accuracy=None,
                validation_samples=0, weight=0.0, feature_importance={},
                note=str(exc)[:180],
            ))

    total_weight = sum(weights) or float(len(probabilities) or 1)
    weighted_probability = sum(p * w for p, w in zip(probabilities, weights)) / total_weight if probabilities else None
    usable = [r for r in results if r.status == "READY" and r.probability_up is not None]
    for i, result in enumerate(results):
        if result.status == "READY" and i < len(weights):
            results[i] = ModelResult(**{**asdict(result), "weight": round(weights[i] / total_weight, 4)})

    agreement = None
    if usable:
        bullish = sum(1 for r in usable if r.direction == "bullish")
        bearish = sum(1 for r in usable if r.direction == "bearish")
        agreement = round(max(bullish, bearish) / len(usable), 4)

    return {
        "status": "READY",
        "horizon": horizon,
        "models": [asdict(result) for result in results],
        "ensemble": {
            "direction": _direction(weighted_probability),
            "probability_up": None if weighted_probability is None else round(weighted_probability, 4),
            "confidence": agreement,
            "model_count": len(usable),
        },
        "features": list(FEATURE_NAMES),
        "validation": {
            "method": "chronological holdout",
            "train_samples": len(y_train),
            "test_samples": len(y_test),
        },
    }
