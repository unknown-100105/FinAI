"""Reproducible research experiments for FinAI Finish Line 2."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Sequence

import numpy as np

from causal_risk.discovery import notears_linear
from causal_risk.patent_benchmark import benchmark_patent_mechanism_variants
from causal_risk.pruning_benchmark import benchmark_prefix_certificate
from causal_risk.research_evaluation import perturb_features


@dataclass(frozen=True)
class ChronologicalSplit:
    train_end: int
    validation_end: int
    test_start: int
    test_end: int


def make_chronological_split(
    n_rows: int,
    *,
    train_fraction: float = 0.60,
    validation_fraction: float = 0.20,
) -> ChronologicalSplit:
    n = int(n_rows)
    if n < 30:
        raise ValueError("at least 30 rows are required")
    if not 0.5 <= train_fraction < 0.9:
        raise ValueError("train_fraction must be between 0.5 and 0.9")
    if not 0.05 <= validation_fraction < 0.4:
        raise ValueError("validation_fraction must be between 0.05 and 0.4")
    if train_fraction + validation_fraction >= 0.95:
        raise ValueError("train_fraction + validation_fraction must be below 0.95")
    train_end = int(n * train_fraction)
    validation_end = train_end + int(n * validation_fraction)
    if validation_end >= n:
        raise ValueError("chronological split leaves no test rows")
    return ChronologicalSplit(
        train_end=train_end,
        validation_end=validation_end,
        test_start=validation_end,
        test_end=n,
    )


def generate_synthetic_financial_system(
    *,
    n_rows: int = 600,
    seed: int = 42,
    regime_change: int | None = None,
) -> dict[str, Any]:
    """Generate a controlled point-in-time DAG dataset with a known graph.

    This is an engineering/research validation dataset, not evidence about
    real-world financial relationships.
    """
    if n_rows < 100 or n_rows > 5000:
        raise ValueError("n_rows must be between 100 and 5000")
    rng = np.random.default_rng(seed)
    regime = n_rows // 2 if regime_change is None else int(regime_change)
    if not 40 <= regime < n_rows:
        raise ValueError("regime_change must leave sufficient observations in each regime")

    rates = rng.normal(0.0, 1.0, n_rows)
    usd = rng.normal(0.0, 0.8, n_rows)
    supply = rng.normal(0.0, 1.1, n_rows)

    oil = 0.35 * usd + 0.25 * supply + rng.normal(0.0, 0.55, n_rows)
    credit = 0.72 * rates + 0.28 * oil + rng.normal(0.0, 0.50, n_rows)
    liquidity = 0.61 * supply + 0.68 * credit + rng.normal(0.0, 0.45, n_rows)
    equity = 0.64 * rates + 0.52 * oil + 0.57 * credit + 0.74 * liquidity
    equity += rng.normal(0.0, 0.65, n_rows)
    portfolio = 0.83 * equity + rng.normal(0.0, 0.50, n_rows)

    # Introduce a controlled structural regime shift after the cutoff.
    equity[regime:] += -0.35 * liquidity[regime:]
    portfolio[regime:] += -0.20 * credit[regime:]

    values = np.column_stack(
        [rates, usd, oil, supply, credit, liquidity, equity, portfolio]
    )
    timestamps = np.arange(n_rows, dtype=np.int64)
    return {
        "status": "SYNTHETIC_POINT_IN_TIME_DATASET_READY",
        "timestamps": timestamps.tolist(),
        "values": values.tolist(),
        "node_ids": [
            "rates",
            "usd",
            "oil",
            "supply",
            "credit",
            "liquidity",
            "equity",
            "portfolio",
        ],
        "known_edges": [
            ["usd", "oil"],
            ["supply", "oil"],
            ["rates", "credit"],
            ["oil", "credit"],
            ["supply", "liquidity"],
            ["credit", "liquidity"],
            ["rates", "equity"],
            ["oil", "equity"],
            ["credit", "equity"],
            ["liquidity", "equity"],
            ["equity", "portfolio"],
        ],
        "regime_change_index": regime,
        "research_boundary": (
            "Synthetic controlled data for validating algorithms and leakage "
            "handling. It is not real financial evidence."
        ),
    }


def run_discovery_holdout_experiment(
    values: Sequence[Sequence[float]],
    *,
    threshold: float = 0.10,
    lambda1: float = 0.02,
) -> dict[str, Any]:
    X = np.asarray(values, dtype=float)
    if X.ndim != 2 or X.shape[1] < 2:
        raise ValueError("values must be a finite matrix with at least two variables")
    if not np.isfinite(X).all():
        raise ValueError("values contain non-finite values")
    split = make_chronological_split(X.shape[0])
    train = X[: split.train_end]
    validation = X[split.train_end : split.validation_end]
    test = X[split.test_start : split.test_end]

    learned = notears_linear(
        train,
        threshold=threshold,
        lambda1=lambda1,
    )
    return {
        "status": "DISCOVERY_FUTURE_HOLDOUT_READY",
        "split": split.__dict__,
        "train_shape": list(train.shape),
        "validation_shape": list(validation.shape),
        "test_shape": list(test.shape),
        "discovery": learned,
        "future_holdout_isolation": True,
        "research_boundary": (
            "NOTEARS is fit only on the earlier training segment. "
            "This validates chronological isolation, not causal identification."
        ),
    }


def run_patent_mechanism_benchmark() -> dict[str, Any]:
    nodes = ["rates", "credit", "liquidity", "equity", "portfolio"]
    edges = [
        {"source": "rates", "target": "credit", "weight": 0.7},
        {"source": "credit", "target": "liquidity", "weight": 0.8},
        {"source": "liquidity", "target": "equity", "weight": 0.9},
        {"source": "equity", "target": "portfolio", "weight": 0.8},
    ]
    bounds = {node: (-100.0, 100.0) for node in nodes}
    benchmark = benchmark_patent_mechanism_variants(
        nodes,
        edges,
        ["rates", "credit"],
        {"rates": 10.0, "credit": 10.0},
        [-1.0, -0.5, 0.5, 1.0],
        bounds,
        target_node="portfolio",
        target_interval=(35.0, 55.0),
        prefix_depth=1,
    )
    forward = benchmark["forward_certificate"]
    compatibility = {
        "false_prunes": forward["false_prunes"],
        "evaluation_reduction_fraction": forward["estimated_evaluation_reduction_fraction"],
    }
    return {
        "status": "PATENT_MECHANISM_BENCHMARK_READY",
        "benchmark": {**compatibility, "variants": benchmark},
        "technical_effects_to_measure": [
            "expensive_SCM_evaluations_avoided",
            "latency",
            "peak_memory",
            "high_risk_trajectory_recall",
            "false_pruning_rate",
        ],
        "research_boundary": (
            "Finite-action controlled benchmark only. Real financial validation "
            "requires point-in-time external data and future-only evaluation."
        ),
    }


def build_ood_suite(values: Sequence[Sequence[float]]) -> dict[str, Any]:
    base = np.asarray(values, dtype=float)
    return {
        "normal": base.tolist(),
        "scaled": perturb_features(base, scale=1.5).tolist(),
        "noisy": perturb_features(base, noise_std=0.25, seed=43).tolist(),
        "missing_first_feature": perturb_features(base, missing_columns=[0]).tolist(),
    }
