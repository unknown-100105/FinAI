"""Stability analysis for causal discovery research outputs."""
from __future__ import annotations

from collections import defaultdict
from typing import Any, Sequence

import numpy as np

from causal_risk.discovery import notears_linear
from causal_risk.dynamic_discovery import discover_lagged_graph


def _window_slices(n_samples: int, windows: int, fraction: float) -> list[tuple[int, int]]:
    if windows < 2 or windows > 6:
        raise ValueError("windows must be between 2 and 6")
    if fraction <= 0 or fraction > 0.9:
        raise ValueError("window_fraction must be > 0 and <= 0.9")
    width = max(24, int(n_samples * fraction))
    width = min(width, n_samples)
    max_start = n_samples - width
    starts = [0] if max_start == 0 else np.linspace(0, max_start, num=windows, dtype=int).tolist()
    slices = []
    for start in starts:
        item = (int(start), int(start + width))
        if item not in slices:
            slices.append(item)
    return slices


def _edge_statistics(
    observations: Sequence[dict[str, float]],
    windows: int,
    *,
    stable_frequency: float,
) -> dict[str, Any]:
    counts: dict[str, int] = defaultdict(int)
    weights: dict[str, list[float]] = defaultdict(list)
    for edge_map in observations:
        for key, weight in edge_map.items():
            counts[key] += 1
            weights[key].append(float(weight))
    ranked = []
    for key, count in counts.items():
        values = np.asarray(weights[key], dtype=float)
        frequency = count / max(windows, 1)
        ranked.append({
            "edge": key,
            "selection_frequency": round(frequency, 3),
            "windows_selected": int(count),
            "mean_abs_weight": round(float(np.mean(np.abs(values))), 6),
            "std_weight": round(float(np.std(values)), 6),
            "sign_consistency": round(abs(float(np.sum(np.sign(values)))) / len(values), 3),
            "stable": bool(frequency >= stable_frequency),
        })
    ranked.sort(
        key=lambda item: (
            -float(item["selection_frequency"]),
            -float(item["mean_abs_weight"]),
            item["edge"],
        )
    )
    return {
        "windows": windows,
        "edges_observed": len(ranked),
        "stable_edges": sum(1 for item in ranked if item["stable"]),
        "ranked_edges": ranked,
    }


def assess_discovery_stability(
    samples: Sequence[Sequence[float]],
    node_ids: Sequence[str],
    *,
    windows: int = 4,
    window_fraction: float = 0.60,
    lambda1: float = 0.02,
    threshold: float = 0.08,
    lags: int = 1,
    alpha: float = 1.0,
    stable_frequency: float = 0.75,
    max_outer_iter: int = 6,
    max_inner_iter: int = 80,
) -> dict[str, Any]:
    """Measure edge-selection stability across contiguous time windows.

    This is a robustness diagnostic, not a causal-confidence estimator.
    """
    X = np.asarray(samples, dtype=float)
    labels = [str(node).strip() for node in node_ids]
    if X.ndim != 2 or X.shape[0] < 40 or X.shape[1] < 2:
        raise ValueError("samples must be a 2-D matrix with at least 40 rows and 2 variables")
    if len(labels) != X.shape[1] or any(not label for label in labels):
        raise ValueError("node_ids length must match variables and contain no empty ids")
    if not np.isfinite(X).all():
        raise ValueError("samples contain non-finite values")
    if stable_frequency < 0.5 or stable_frequency > 1.0:
        raise ValueError("stable_frequency must be between 0.5 and 1.0")

    specs = _window_slices(X.shape[0], windows, window_fraction)
    contemporaneous_observations = []
    temporal_observations = []
    window_metadata = []

    for index, (start, end) in enumerate(specs, start=1):
        window = X[start:end]
        note = notears_linear(
            window,
            lambda1=lambda1,
            max_outer_iter=max_outer_iter,
            max_inner_iter=max_inner_iter,
            threshold=threshold,
        )
        note_edges = {
            f"{labels[src]}->{labels[dst]}": float(weight)
            for src, row in enumerate(note["adjacency"])
            for dst, weight in enumerate(row)
            if float(weight)
        }
        dynamic = discover_lagged_graph(
            window,
            lags=lags,
            alpha=alpha,
            threshold=threshold,
        )
        dynamic_edges = {
            f"{labels[edge['source']]}->{labels[edge['target']]}|lag={edge['lag']}": float(edge["weight"])
            for edge in dynamic["edges"]
        }
        contemporaneous_observations.append(note_edges)
        temporal_observations.append(dynamic_edges)
        window_metadata.append({
            "window": index,
            "start_row": start,
            "end_row": end,
            "observations": end - start,
            "note_acyclicity": note["acyclicity"],
            "contemporaneous_edges": len(note_edges),
            "temporal_edges": len(dynamic_edges),
        })

    return {
        "status": "research_stability_ready",
        "n_samples": int(X.shape[0]),
        "n_variables": int(X.shape[1]),
        "node_ids": labels,
        "configuration": {
            "windows": len(specs),
            "window_fraction": window_fraction,
            "threshold": threshold,
            "stable_frequency": stable_frequency,
            "lags": lags,
        },
        "windows": window_metadata,
        "contemporaneous": _edge_statistics(
            contemporaneous_observations, len(specs), stable_frequency=stable_frequency
        ),
        "temporal": _edge_statistics(
            temporal_observations, len(specs), stable_frequency=stable_frequency
        ),
        "semantics": "Selection frequency across contiguous time windows is a robustness diagnostic, not causal confidence or validated identification.",
    }
