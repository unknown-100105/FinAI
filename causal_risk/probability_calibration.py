"""Optional probability calibration for FinAI risk/model scores.

This module is deliberately separate from causal_risk.calibration, which
estimates edge-coefficient diagnostics. It calibrates binary probabilities
against held-out labels. Callers are responsible for using a chronological or
otherwise leakage-safe calibration split.

The Calibre dependency requires Python 3.12+; the default backend therefore
uses Calibre when installed and falls back to scikit-learn isotonic regression.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

import numpy as np
from sklearn.isotonic import IsotonicRegression

Backend = Literal["auto", "calibre", "sklearn_isotonic"]


def _validated_arrays(scores, labels, sample_weight=None):
    x = np.asarray(scores, dtype=float)
    y = np.asarray(labels, dtype=float)
    if x.ndim != 1 or y.ndim != 1:
        raise ValueError("scores and labels must be one-dimensional")
    if x.size != y.size or x.size < 2:
        raise ValueError("scores and labels must have the same length >= 2")
    if not np.isfinite(x).all() or not np.isfinite(y).all():
        raise ValueError("scores and labels must contain only finite values")
    if np.any((x < 0.0) | (x > 1.0)):
        raise ValueError("scores must be probabilities in [0, 1]")
    if np.any((y != 0.0) & (y != 1.0)):
        raise ValueError("labels must be binary values 0 or 1")
    if np.unique(y).size < 2:
        raise ValueError("labels must contain both classes to fit calibration")
    weights = None
    if sample_weight is not None:
        weights = np.asarray(sample_weight, dtype=float)
        if weights.ndim != 1 or weights.size != x.size:
            raise ValueError("sample_weight must be one-dimensional and match scores")
        if not np.isfinite(weights).all() or np.any(weights < 0):
            raise ValueError("sample_weight must be finite and non-negative")
        if float(weights.sum()) <= 0:
            raise ValueError("sample_weight must have positive total weight")
    return x, y, weights


@dataclass
class ProbabilityCalibrationReport:
    n_samples: int
    brier_score: float
    expected_calibration_error: float
    calibration_in_the_large: float
    distinct_probability_count: int
    bins: int


def evaluate_probability_calibration(labels, probabilities, *, n_bins: int = 10):
    """Report Brier score and equal-mass ECE on an untouched evaluation set."""
    y = np.asarray(labels, dtype=float)
    p = np.asarray(probabilities, dtype=float)
    if y.ndim != 1 or p.ndim != 1 or y.size != p.size or y.size == 0:
        raise ValueError("labels and probabilities must be non-empty matching vectors")
    if not np.isfinite(y).all() or not np.isfinite(p).all():
        raise ValueError("labels and probabilities must be finite")
    if np.any((y != 0.0) & (y != 1.0)):
        raise ValueError("labels must be binary values 0 or 1")
    if np.any((p < 0.0) | (p > 1.0)):
        raise ValueError("probabilities must be in [0, 1]")
    if not isinstance(n_bins, int) or n_bins < 1:
        raise ValueError("n_bins must be a positive integer")

    order = np.argsort(p, kind="mergesort")
    chunks = np.array_split(order, min(n_bins, p.size))
    ece = 0.0
    for indices in chunks:
        if indices.size:
            ece += (indices.size / p.size) * abs(
                float(np.mean(y[indices])) - float(np.mean(p[indices]))
            )
    return ProbabilityCalibrationReport(
        n_samples=int(y.size),
        brier_score=float(np.mean((p - y) ** 2)),
        expected_calibration_error=float(ece),
        calibration_in_the_large=float(np.mean(p) - np.mean(y)),
        distinct_probability_count=int(np.unique(p).size),
        bins=int(sum(bool(chunk.size) for chunk in chunks)),
    )


class ProbabilityCalibrator:
    """Fit Calibre if installed, otherwise use scikit-learn isotonic regression.

    Do not fit this object on the same observations used to train the predictor.
    """

    def __init__(self, backend: Backend = "auto") -> None:
        if backend not in {"auto", "calibre", "sklearn_isotonic"}:
            raise ValueError(f"Unsupported calibration backend: {backend}")
        self.requested_backend = backend
        self.backend: str | None = None
        self._model = None

    def fit(self, scores, labels, sample_weight=None):
        x, y, weights = _validated_arrays(scores, labels, sample_weight)
        if self.requested_backend in {"auto", "calibre"}:
            try:
                from calibre import CenteredIsotonicCalibrator
            except ImportError as exc:
                if self.requested_backend == "calibre":
                    raise RuntimeError(
                        "Calibre is not installed in this Python environment. "
                        "Install requirements-calibre.txt with Python 3.12+."
                    ) from exc
            else:
                self._model = CenteredIsotonicCalibrator()
                if weights is None:
                    self._model.fit(x, y)
                else:
                    self._model.fit(x, y, sample_weight=weights)
                self.backend = "calibre_centered_isotonic"
                return self

        model = IsotonicRegression(y_min=0.0, y_max=1.0, out_of_bounds="clip")
        model.fit(x, y, sample_weight=weights)
        self._model = model
        self.backend = "sklearn_isotonic"
        return self

    def transform(self, scores) -> np.ndarray:
        if self._model is None:
            raise RuntimeError("ProbabilityCalibrator must be fitted before transform")
        x = np.asarray(scores, dtype=float)
        if x.ndim != 1 or not np.isfinite(x).all():
            raise ValueError("scores must be a finite one-dimensional vector")
        if np.any((x < 0.0) | (x > 1.0)):
            raise ValueError("scores must be probabilities in [0, 1]")
        if self.backend == "sklearn_isotonic":
            result = self._model.predict(x)
        else:
            result = self._model.transform(x)
        return np.clip(np.asarray(result, dtype=float), 0.0, 1.0)
