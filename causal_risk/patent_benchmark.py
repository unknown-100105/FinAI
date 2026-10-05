"""Reproducible benchmarks for the causal-feasibility patent hypothesis.

The benchmark compares:
1. exhaustive completion evaluation;
2. forward causal interval screening;
3. bidirectional necessary-interval screening;
4. incremental interval propagation accounting.

It is deliberately small-state and research-only. Results are not claims of
real-world financial performance or patentability.
"""
from __future__ import annotations

from itertools import product
import math
from time import perf_counter
from typing import Any, Mapping, Sequence

from causal_risk.bidirectional_feasibility import backward_target_cone
from causal_risk.feasibility_pruning import evaluate_prefix_feasibility
from causal_risk.incremental_feasibility import IncrementalIntervalState
from causal_risk.scm import simulate_scm


def _candidate_value(center: float, level: float, scale: float) -> float:
    return float(center) + float(level) * max(abs(float(center)) * scale, 5.0)


def _finite_edge_tuples(edges: Sequence[Mapping[str, Any]]) -> tuple[tuple[str, str, float], ...]:
    return tuple(
        (str(edge["source"]), str(edge["target"]), float(edge["weight"]))
        for edge in edges
        if int(edge.get("lag", 0)) == 0
    )


def benchmark_patent_mechanism_variants(
    nodes: Sequence[str],
    edges: Sequence[Mapping[str, Any]],
    factor_ids: Sequence[str],
    center: Mapping[str, float],
    levels: Sequence[float],
    node_bounds: Mapping[str, Sequence[float]],
    *,
    target_node: str,
    target_interval: Sequence[float],
    prefix_depth: int = 1,
    scale: float = 0.35,
) -> dict[str, Any]:
    """Compare exhaustive, forward, bidirectional and incremental evaluation.

    The exhaustive baseline enumerates every remaining discrete action for every
    candidate prefix. The pruning variants count an exact completion as
    "retained" only when their cheap screen allows it. For finite action spaces,
    the reported false-prune rate and high-risk prefix recall are exact for the
    supplied benchmark state.
    """
    factors = tuple(str(value) for value in factor_ids)
    labels = tuple(str(value) for value in nodes)
    if not labels or len(set(labels)) != len(labels):
        raise ValueError("nodes must be non-empty and unique")
    if not factors or len(set(factors)) != len(factors):
        raise ValueError("factor_ids must be non-empty and unique")
    if any(factor not in labels for factor in factors):
        raise ValueError("factor_ids must be present in nodes")
    if tuple(sorted(center)) != tuple(sorted(factors)):
        raise ValueError("center keys must match factor_ids")
    if not 1 <= int(prefix_depth) <= len(factors):
        raise ValueError("prefix_depth must be between 1 and n_factors")
    action_levels = tuple(float(level) for level in levels)
    if not action_levels or any(not math.isfinite(level) for level in action_levels):
        raise ValueError("levels must be non-empty and finite")
    if scale <= 0:
        raise ValueError("scale must be positive")

    candidate_prefixes: list[dict[str, float]] = []
    for chosen in product(action_levels, repeat=prefix_depth):
        candidate_prefixes.append({
            factor: _candidate_value(center[factor], level, scale)
            for factor, level in zip(factors[:prefix_depth], chosen)
        })

    full_edges = _finite_edge_tuples(edges)
    remaining = factors[prefix_depth:]

    exact_feasible_prefixes = 0
    exact_completion_evaluations = 0
    prefix_records: list[dict[str, Any]] = []

    forward_hard_pruned = 0
    forward_retained = 0
    forward_false_prunes = 0

    backward = backward_target_cone(
        labels,
        edges,
        node_bounds,
        target_node=target_node,
        target_interval=target_interval,
        intervened_nodes=remaining,
    )
    required = {
        str(node): tuple(float(v) for v in interval)
        for node, interval in backward["required_intervals"].items()
    }
    backward_pruned = 0
    backward_retained = 0
    backward_false_prunes = 0

    for prefix in candidate_prefixes:
        exact_values: list[float] = []
        prefix_is_feasible = False
        for completion in product(action_levels, repeat=len(remaining)):
            full = dict(prefix)
            for factor, level in zip(remaining, completion):
                full[factor] = _candidate_value(center[factor], level, scale)
            result = simulate_scm(labels, full_edges, full)
            exact_completion_evaluations += 1
            target_value = float(result["node_values"][str(target_node)])
            exact_values.append(target_value)
            if float(target_interval[0]) <= target_value <= float(target_interval[1]):
                prefix_is_feasible = True
        exact_feasible_prefixes += int(prefix_is_feasible)

        forward_certificate = evaluate_prefix_feasibility(
            labels,
            edges,
            prefix,
            node_bounds,
            target_node=target_node,
            target_interval=target_interval,
            intervened_nodes=remaining,
        )
        forward_pruned = bool(forward_certificate.hard_infeasible)
        forward_hard_pruned += int(forward_pruned)
        forward_retained += int(not forward_pruned)
        forward_false_prunes += int(forward_pruned and prefix_is_feasible)

        backward_prefix_pruned = False
        backward_reasons: list[str] = []
        for factor, value in prefix.items():
            required_interval = required.get(factor)
            if required_interval is None:
                continue
            lo, hi = required_interval
            if lo > hi:
                backward_prefix_pruned = True
                backward_reasons.append(f"{factor}:empty_necessary_interval")
                break
            if value < lo or value > hi:
                backward_prefix_pruned = True
                backward_reasons.append(
                    f"{factor}={value:.6f} outside necessary interval [{lo:.6f},{hi:.6f}]"
                )
                break
        backward_pruned += int(backward_prefix_pruned)
        backward_retained += int(not backward_prefix_pruned)
        backward_false_prunes += int(backward_prefix_pruned and prefix_is_feasible)

        prefix_records.append({
            "prefix": prefix,
            "exactly_feasible_completion_exists": prefix_is_feasible,
            "target_values_from_exact_completions": [round(v, 6) for v in exact_values],
            "forward_hard_pruned": forward_pruned,
            "forward_certificate": forward_certificate.as_dict(),
            "backward_pruned": backward_prefix_pruned,
            "backward_reasons": backward_reasons,
        })

    # Incremental-vs-full propagation accounting on the same candidate set.
    start_full = perf_counter()
    full_node_evaluations = 0
    full_snapshots: list[dict[str, tuple[float, float]]] = []
    from causal_risk.feasibility_pruning import propagate_interval_bounds

    for prefix in candidate_prefixes:
        full_snapshots.append(
            propagate_interval_bounds(labels, edges, prefix, node_bounds)
        )
        full_node_evaluations += len(labels)
    full_elapsed = perf_counter() - start_full

    start_incremental = perf_counter()
    incremental_node_evaluations = 0
    incremental_matches = 0
    for prefix, expected in zip(candidate_prefixes, full_snapshots):
        state = IncrementalIntervalState.build(labels, edges, node_bounds, {})
        last: dict[str, Any] | None = None
        for node, value in prefix.items():
            last = state.apply_change(node, value)
        if last is not None:
            incremental_node_evaluations += sum(
                len(state._descendants_in_order(node)) for node in prefix
            )
            incremental_matches += int(state.intervals == expected)
    incremental_elapsed = perf_counter() - start_incremental

    incremental_match_rate = (
        incremental_matches / len(candidate_prefixes) if candidate_prefixes else 1.0
    )

    baseline = {
        "candidate_prefixes": len(candidate_prefixes),
        "exact_completion_evaluations": exact_completion_evaluations,
        "high_risk_prefixes": exact_feasible_prefixes,
        "remaining_actions_per_prefix": len(action_levels) ** len(remaining),
    }
    forward = {
        "hard_pruned_prefixes": forward_hard_pruned,
        "retained_prefixes": forward_retained,
        "false_prunes": forward_false_prunes,
        "high_risk_prefix_recall": (
            (exact_feasible_prefixes - forward_false_prunes) / exact_feasible_prefixes
            if exact_feasible_prefixes else 1.0
        ),
        "estimated_expensive_evaluations_avoided": (
            forward_hard_pruned * (len(action_levels) ** len(remaining))
        ),
        "estimated_evaluation_reduction_fraction": (
            forward_hard_pruned / len(candidate_prefixes)
            if candidate_prefixes else 0.0
        ),
    }
    backward_result = {
        "necessary_interval_pruned_prefixes": backward_pruned,
        "retained_prefixes": backward_retained,
        "false_prunes": backward_false_prunes,
        "high_risk_prefix_recall": (
            (exact_feasible_prefixes - backward_false_prunes) / exact_feasible_prefixes
            if exact_feasible_prefixes else 1.0
        ),
        "estimated_expensive_evaluations_avoided": (
            backward_pruned * (len(action_levels) ** len(remaining))
        ),
        "estimated_evaluation_reduction_fraction": (
            backward_pruned / len(candidate_prefixes)
            if candidate_prefixes else 0.0
        ),
        "target_ancestor_required_intervals": {
            node: list(interval)
            for node, interval in required.items()
        },
    }

    return {
        "status": "PATENT_MECHANISM_VARIANT_BENCHMARK_READY",
        "baseline": baseline,
        "forward_certificate": forward,
        "bidirectional_necessary_interval": backward_result,
        "incremental_propagation": {
            "full_node_interval_evaluations": full_node_evaluations,
            "incremental_node_interval_evaluations": incremental_node_evaluations,
            "estimated_node_evaluation_reduction_fraction": (
                1.0 - incremental_node_evaluations / full_node_evaluations
                if full_node_evaluations else 0.0
            ),
            "full_runtime_seconds": round(full_elapsed, 8),
            "incremental_runtime_seconds": round(incremental_elapsed, 8),
            "exact_match_rate": round(incremental_match_rate, 8),
        },
        "correctness": {
            "finite_action_space_high_risk_prefixes": exact_feasible_prefixes,
            "forward_false_prunes": forward_false_prunes,
            "bidirectional_false_prunes": backward_false_prunes,
            "forward_no_false_prune": forward_false_prunes == 0,
            "bidirectional_no_false_prune": backward_false_prunes == 0,
        },
        "configuration": {
            "nodes": list(labels),
            "factor_ids": list(factors),
            "levels": list(action_levels),
            "prefix_depth": int(prefix_depth),
            "scale": float(scale),
            "target_node": str(target_node),
            "target_interval": list(target_interval),
        },
        "records": prefix_records,
        "research_boundary": (
            "This is a deterministic finite-action correctness and compute "
            "accounting benchmark. It is not real-market validation, patent "
            "novelty proof, or evidence of production performance."
        ),
    }
