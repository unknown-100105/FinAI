"""Empirical diagnostics for research consensus-edge calibration."""
from __future__ import annotations

from typing import Any, Mapping, Sequence

import numpy as np
from sklearn.linear_model import Ridge


def _r2(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    centered = y_true - np.mean(y_true)
    total = float(np.sum(centered * centered))
    if total < 1e-12:
        return 0.0
    return 1.0 - float(np.sum((y_true - y_pred) ** 2)) / total


def _block_indices(
    n: int,
    block_size: int,
    rng: np.random.Generator,
) -> np.ndarray:
    block_size = max(1, min(int(block_size), n))
    starts = rng.integers(
        0,
        max(n - block_size + 1, 1),
        size=int(np.ceil(n / block_size)),
    )
    indices = []
    for start in starts:
        indices.extend(
            range(int(start), min(int(start) + block_size, n))
        )
        if len(indices) >= n:
            break
    return np.asarray(indices[:n], dtype=int)


def calibrate_consensus_edges(
    samples: Sequence[Sequence[float]],
    node_ids: Sequence[str],
    edges: Sequence[Mapping[str, Any]],
    *,
    test_fraction: float = 0.20,
    bootstrap_draws: int = 100,
    block_size: int = 10,
    seed: int = 42,
    ridge_alpha: float = 1.0,
) -> dict[str, Any]:
    """Estimate empirical coefficient diagnostics for consensus candidates.

    Coefficients are standardized conditional associations measured out of
    sample. Ridge regularization is used to reduce instability from
    multicollinear market proxies. These remain empirical associations, not
    identified causal effects.
    """
    X = np.asarray(samples, dtype=float)
    labels = [str(node).strip() for node in node_ids]
    if X.ndim != 2 or X.shape[0] < 60 or X.shape[1] < 2:
        raise ValueError(
            "samples must be a 2-D matrix with at least 60 rows and 2 variables"
        )
    if (
        len(labels) != X.shape[1]
        or len(set(labels)) != len(labels)
        or any(not label for label in labels)
    ):
        raise ValueError("node_ids must uniquely match the sample variables")
    if not 0.1 <= float(test_fraction) <= 0.4:
        raise ValueError("test_fraction must be between 0.1 and 0.4")
    if bootstrap_draws < 20 or bootstrap_draws > 1000:
        raise ValueError("bootstrap_draws must be between 20 and 1000")
    if block_size < 1 or block_size > X.shape[0]:
        raise ValueError("block_size must be between 1 and the sample count")
    if ridge_alpha <= 0:
        raise ValueError("ridge_alpha must be positive")
    if not np.isfinite(X).all():
        raise ValueError("samples contain non-finite values")
    if not edges:
        return {
            "status": "NO_CANDIDATE_EDGES",
            "n_samples": int(X.shape[0]),
            "n_variables": int(X.shape[1]),
            "train_samples": 0,
            "test_samples": 0,
            "calibrations": [],
            "semantics": (
                "No consensus research candidates were supplied for empirical calibration."
            ),
        }

    split = int(np.floor(X.shape[0] * (1.0 - float(test_fraction))))
    split = min(max(split, 40), X.shape[0] - 20)
    train = X[:split]
    test = X[split:]
    rng = np.random.default_rng(seed)
    calibrations = []

    for raw_edge in edges:
        source = str(raw_edge["source"])
        target = str(raw_edge["target"])
        lag = int(raw_edge.get("lag", 0))
        if source not in labels or target not in labels:
            raise ValueError(f"edge references unknown node: {source}->{target}")
        if source == target and lag == 0:
            raise ValueError(
                f"edge contains contemporaneous self-loop: {source}->{target}"
            )
        target_idx = labels.index(target)

        def aligned(matrix: np.ndarray):
            predictor_indices = [
                i for i in range(matrix.shape[1]) if i != target_idx
            ]
            if lag <= 0:
                return (
                    matrix[:, predictor_indices],
                    matrix[:, target_idx],
                    [labels[i] for i in predictor_indices],
                )
            if lag >= len(matrix):
                raise ValueError(
                    f"lag {lag} is too large for the calibration window"
                )
            return (
                matrix[:-lag, predictor_indices],
                matrix[lag:, target_idx],
                [labels[i] for i in predictor_indices],
            )

        train_x, train_y, predictor_labels = aligned(train)
        test_x, test_y, _ = aligned(test)
        source_col = predictor_labels.index(source)

        mean = np.mean(train_x, axis=0)
        std = np.where(
            np.std(train_x, axis=0) < 1e-12,
            1.0,
            np.std(train_x, axis=0),
        )
        y_mean = float(np.mean(train_y))
        y_std = float(np.std(train_y))
        y_std = 1.0 if y_std < 1e-12 else y_std
        Xs = (train_x - mean) / std
        ys = (train_y - y_mean) / y_std

        model = Ridge(alpha=float(ridge_alpha), fit_intercept=True)
        model.fit(Xs, ys)
        beta = model.coef_
        train_pred = (
            model.predict((train_x - mean) / std) * y_std + y_mean
        )
        test_pred = (
            model.predict((test_x - mean) / std) * y_std + y_mean
        )

        singular_values = np.linalg.svd(
            Xs,
            compute_uv=False,
            full_matrices=False,
        )
        condition_number = (
            float(singular_values[0] / max(singular_values[-1], 1e-12))
            if len(singular_values)
            else 0.0
        )

        bootstrap_values = []
        for _ in range(bootstrap_draws):
            idx = _block_indices(len(train_x), block_size, rng)
            bx = train_x[idx]
            by = train_y[idx]
            bmean = np.mean(bx, axis=0)
            bstd = np.where(
                np.std(bx, axis=0) < 1e-12,
                1.0,
                np.std(bx, axis=0),
            )
            by_mean = float(np.mean(by))
            by_std = float(np.std(by))
            by_std = 1.0 if by_std < 1e-12 else by_std
            by_stdized = (by - by_mean) / by_std
            bmodel = Ridge(
                alpha=float(ridge_alpha),
                fit_intercept=True,
            )
            bmodel.fit(
                (bx - bmean) / bstd,
                by_stdized,
            )
            bootstrap_values.append(float(bmodel.coef_[source_col]))

        boot = np.asarray(bootstrap_values, dtype=float)
        q_low, q_high = np.quantile(boot, [0.025, 0.975])
        source_beta = float(beta[source_col])
        consensus_weight = float(raw_edge.get("weight", 0.0))
        sign_matches = (
            float(np.mean(np.sign(boot) == np.sign(source_beta)))
            if len(boot)
            else 0.0
        )

        calibrations.append({
            "edge": f"{source}->{target}"
            + (f"|lag={lag}" if lag else ""),
            "source": source,
            "target": target,
            "lag": lag,
            "consensus_weight": round(consensus_weight, 6),
            "empirical_standardized_coefficient": round(source_beta, 6),
            "bootstrap_ci_95": [
                round(float(q_low), 6),
                round(float(q_high), 6),
            ],
            "bootstrap_sign_consistency": round(sign_matches, 3),
            "coefficient_sign": (
                "positive"
                if source_beta > 0
                else "negative"
                if source_beta < 0
                else "zero"
            ),
            "test_r2": round(_r2(test_y, test_pred), 6),
            "test_mae": round(
                float(np.mean(np.abs(test_y - test_pred))),
                6,
            ),
            "train_r2": round(_r2(train_y, train_pred), 6),
            "absolute_gap_to_consensus_weight": round(
                abs(source_beta - consensus_weight),
                6,
            ),
            "condition_number": round(condition_number, 6),
            "bootstrap_ci_contains_zero": bool(q_low <= 0.0 <= q_high),
            "alignment": (
                "target_t_on_predictors_t_minus_lag"
                if lag > 0
                else "target_t_on_predictors_t"
            ),
            "diagnostic_status": (
                "SIGNAL_ALIGNS_WITH_CONSENSUS"
                if source_beta * consensus_weight > 0
                and not (q_low <= 0.0 <= q_high)
                else "SIGNAL_NEEDS_REVIEW"
            ),
        })

    return {
        "status": "EMPIRICAL_CALIBRATION_READY",
        "n_samples": int(X.shape[0]),
        "n_variables": int(X.shape[1]),
        "train_samples": int(len(train)),
        "test_samples": int(len(test)),
        "split_method": "chronological",
        "estimator": "Ridge",
        "ridge_alpha": float(ridge_alpha),
        "bootstrap": {
            "draws": bootstrap_draws,
            "block_size": block_size,
            "seed": seed,
            "method": "moving-block bootstrap over training observations",
        },
        "calibrations": calibrations,
        "semantics": (
            "Empirical coefficients are standardized conditional associations "
            "with chronological out-of-sample diagnostics; they are not identified "
            "causal effects."
        ),
    }
