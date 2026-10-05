"""Empirical calibration of structural risk-channel parameters.

The default FinAI risk configuration is intentionally a research prior. This
module provides a reproducible way to replace those priors with coefficients
estimated from an externally observed, point-in-time outcome dataset.

The fitted coefficients remain predictive/associational parameters. They are
not causal estimates merely because they are used inside an SCM.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping, Sequence

import json
import numpy as np
from sklearn.linear_model import Ridge


COEFFICIENT_KEYS = (
    "equity_from_liquidity",
    "debt_from_rates",
    "debt_from_credit",
    "debt_from_oil",
    "debt_from_liquidity",
    "gold_from_usd",
    "gold_from_rates",
    "gold_from_oil",
    "systemic_liquidity",
    "systemic_equity",
    "systemic_debt",
    "systemic_drawdown",
)


def _fit_standardized_ridge(
    X: np.ndarray,
    y: np.ndarray,
    *,
    alpha: float,
    split: int,
) -> tuple[np.ndarray, dict[str, Any]]:
    train_x, test_x = X[:split], X[split:]
    train_y, test_y = y[:split], y[split:]
    mean = np.mean(train_x, axis=0)
    scale = np.std(train_x, axis=0)
    scale = np.where(scale < 1e-12, 1.0, scale)
    y_mean = float(np.mean(train_y))
    y_scale = float(np.std(train_y))
    y_scale = 1.0 if y_scale < 1e-12 else y_scale
    train_z = (train_x - mean) / scale
    test_z = (test_x - mean) / scale
    target_z = (train_y - y_mean) / y_scale

    model = Ridge(alpha=float(alpha))
    model.fit(train_z, target_z)

    train_pred = model.predict(train_z) * y_scale + y_mean
    test_pred = model.predict(test_z) * y_scale + y_mean

    ss_total = float(np.sum((test_y - np.mean(test_y)) ** 2))
    ss_resid = float(np.sum((test_y - test_pred) ** 2))
    test_r2 = 0.0 if ss_total < 1e-12 else 1.0 - ss_resid / ss_total
    return (
        model.coef_ * y_scale / scale,
        {
            "train_samples": int(len(train_x)),
            "test_samples": int(len(test_x)),
            "test_r2": round(float(test_r2), 6),
            "test_mae": round(float(np.mean(np.abs(test_y - test_pred))), 6),
        },
    )


def fit_channel_calibration(
    scm_samples: Sequence[Mapping[str, float]],
    observed_channels: Mapping[str, Sequence[float]],
    *,
    alpha: float = 1.0,
) -> dict[str, Any]:
    """Fit the exact coefficient schema consumed by _channels_from_scm.

    scm_samples should contain point-in-time structural values for variables
    produced by the SCM. observed_channels should contain externally observed
    realized channel outcomes aligned to the same rows.

    Required observed outcomes:
      equity, debt, gold, portfolio, systemic_stress

    The fitted bundle is predictive/associational calibration, not causal
    identification.
    """
    if alpha <= 0:
        raise ValueError("alpha must be positive")
    samples = [dict(row) for row in scm_samples]
    n = len(samples)
    if n < 80:
        raise ValueError("at least 80 aligned point-in-time samples are required")

    required = {"equity", "debt", "gold", "portfolio", "systemic_stress"}
    missing = sorted(required - set(observed_channels))
    if missing:
        raise ValueError(
            "observed_channels missing required outcomes: " + ", ".join(missing)
        )

    targets = {
        key: np.asarray(observed_channels[key], dtype=float)
        for key in required
    }
    if any(len(value) != n for value in targets.values()):
        raise ValueError("all observed channel outcomes must align to scm_samples")
    if not all(np.isfinite(value).all() for value in targets.values()):
        raise ValueError("observed channel outcomes must be finite")

    def values(name: str) -> np.ndarray:
        array = np.asarray([float(row.get(name, 0.0)) for row in samples], dtype=float)
        if not np.isfinite(array).all():
            raise ValueError(f"scm_samples contain non-finite values for {name}")
        return array

    rates = values("rates")
    credit = values("credit")
    oil = values("oil")
    usd = values("usd")
    liquidity = values("liquidity")
    structural_equity = values("equity")
    portfolio = targets["portfolio"]

    split = int(np.floor(n * 0.8))
    split = min(max(split, 60), n - 20)

    coefficients: dict[str, float] = {}
    diagnostics: dict[str, Any] = {}

    eq_coef, eq_diag = _fit_standardized_ridge(
        liquidity.reshape(-1, 1),
        targets["equity"] - structural_equity,
        alpha=alpha,
        split=split,
    )
    coefficients["equity_from_liquidity"] = float(eq_coef[0])
    diagnostics["equity_channel"] = eq_diag

    debt_coef, debt_diag = _fit_standardized_ridge(
        np.column_stack([rates, credit, oil, liquidity]),
        targets["debt"],
        alpha=alpha,
        split=split,
    )
    for key, value in zip(
        ("debt_from_rates", "debt_from_credit", "debt_from_oil", "debt_from_liquidity"),
        debt_coef,
    ):
        coefficients[key] = float(value)
    diagnostics["debt_channel"] = debt_diag

    gold_coef, gold_diag = _fit_standardized_ridge(
        np.column_stack([usd, rates, oil]),
        targets["gold"],
        alpha=alpha,
        split=split,
    )
    for key, value in zip(
        ("gold_from_usd", "gold_from_rates", "gold_from_oil"),
        gold_coef,
    ):
        coefficients[key] = float(value)
    diagnostics["gold_channel"] = gold_diag

    systemic_coef, systemic_diag = _fit_standardized_ridge(
        np.column_stack([
            np.abs(liquidity),
            np.abs(targets["equity"]),
            np.abs(targets["debt"]),
            np.abs(portfolio),
        ]),
        targets["systemic_stress"],
        alpha=alpha,
        split=split,
    )
    for key, value in zip(
        ("systemic_liquidity", "systemic_equity", "systemic_debt", "systemic_drawdown"),
        systemic_coef,
    ):
        coefficients[key] = float(value)
    diagnostics["systemic_stress"] = systemic_diag

    if set(coefficients) != set(COEFFICIENT_KEYS):
        raise RuntimeError("fitted coefficient schema is incomplete")

    return {
        "version": "empirical-fit-v1",
        "status": "empirical_fit",
        "provenance": (
            "Chronological Ridge calibration from externally observed channel "
            "outcomes. These are predictive associations, not identified causal effects."
        ),
        "coefficients": {
            key: round(float(coefficients[key]), 8)
            for key in COEFFICIENT_KEYS
        },
        "validation": {
            "empirical_fit_available": True,
            "causal_identification": False,
            "chronological_split": True,
            "train_samples": int(split),
            "test_samples": int(n - split),
            "estimator": "Ridge",
            "alpha": float(alpha),
            "diagnostics": diagnostics,
        },
    }


def save_channel_calibration_bundle(
    bundle: Mapping[str, Any],
    path: str | Path,
) -> str:
    """Write an already-reviewed empirical calibration bundle to JSON."""
    payload = dict(bundle)
    if payload.get("status") != "empirical_fit":
        raise ValueError("only an empirical_fit bundle may be saved")
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return str(destination)
