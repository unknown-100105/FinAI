"""Exact-small-state benchmark for the causal-feasibility pruning hypothesis."""
from __future__ import annotations

from itertools import product
from time import perf_counter
from typing import Any, Mapping, Sequence

from causal_risk.feasibility_pruning import evaluate_prefix_feasibility
from causal_risk.scm import simulate_scm


def benchmark_prefix_certificate(
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
    """Compare conservative prefix pruning with exact completion enumeration.

    This benchmark is intentionally limited to small discrete action spaces.
    It provides an executable correctness test: a sound certificate should not
    hard-prune a prefix that has an admissible completion under the exact
    enumerated baseline.

    The exact baseline is not intended for production. Its purpose is to expose
    the computational effect of avoiding completion enumeration.
    """
    factors = tuple(str(value) for value in factor_ids)
    if not factors or len(set(factors)) != len(factors):
        raise ValueError("factor_ids must be non-empty and unique")
    if tuple(sorted(center)) != tuple(sorted(factors)):
        raise ValueError("center keys must match factor_ids")
    if not 1 <= int(prefix_depth) <= len(factors):
        raise ValueError("prefix_depth must be between 1 and n_factors")
    action_levels = tuple(float(level) for level in levels)
    if not action_levels:
        raise ValueError("levels must be non-empty")
    if scale <= 0:
        raise ValueError("scale must be positive")

    start_certificate = perf_counter()
    candidate_prefixes: list[dict[str, float]] = []
    for chosen in product(action_levels, repeat=prefix_depth):
        prefix = {}
        for factor, level in zip(factors[:prefix_depth], chosen):
            prefix[factor] = float(center[factor]) + level * max(abs(float(center[factor])) * scale, 5.0)
        candidate_prefixes.append(prefix)

    exact_feasible = 0
    false_prunes = 0
    hard_pruned = 0
    exact_completion_evaluations = 0
    certificate_records: list[dict[str, Any]] = []

    remaining = factors[prefix_depth:]
    for prefix in candidate_prefixes:
        certificate = evaluate_prefix_feasibility(
            nodes,
            edges,
            prefix,
            node_bounds,
            target_node=target_node,
            target_interval=target_interval,
        )
        hard_pruned_flag = certificate.hard_infeasible
        if hard_pruned_flag:
            hard_pruned += 1

        prefix_has_feasible_completion = False
        # Enumerate every completion for the exact baseline so the benchmark
        # measures the work that the certificate is intended to avoid.
        for completion_levels in product(action_levels, repeat=len(remaining)):
            full = dict(prefix)
            for factor, level in zip(remaining, completion_levels):
                full[factor] = float(center[factor]) + level * max(
                    abs(float(center[factor])) * scale, 5.0
                )
            result = simulate_scm(
                nodes,
                tuple(
                    (str(edge["source"]), str(edge["target"]), float(edge["weight"]))
                    for edge in edges
                    if int(edge.get("lag", 0)) == 0
                ),
                full,
            )
            exact_completion_evaluations += 1
            target_value = float(result["node_values"][target_node])
            if float(target_interval[0]) <= target_value <= float(target_interval[1]):
                prefix_has_feasible_completion = True

        if prefix_has_feasible_completion:
            exact_feasible += 1
        if hard_pruned_flag and prefix_has_feasible_completion:
            false_prunes += 1
        certificate_records.append({
            "prefix": prefix,
            "hard_pruned": hard_pruned_flag,
            "exactly_feasible_completion_exists": prefix_has_feasible_completion,
            "certificate_margin": certificate.margin,
        })

    certificate_elapsed = perf_counter() - start_certificate
    candidate_count = len(candidate_prefixes)
    return {
        "status": "PRUNING_BENCHMARK_READY",
        "candidate_prefixes": candidate_count,
        "hard_pruned": hard_pruned,
        "exact_feasible_prefixes": exact_feasible,
        "false_prunes": false_prunes,
        "false_prune_rate": false_prunes / max(exact_feasible, 1),
        "exact_completion_evaluations": exact_completion_evaluations,
        "certificate_evaluations": candidate_count,
        "evaluation_reduction_fraction": (
            1.0 - candidate_count / max(exact_completion_evaluations, 1)
        ),
        "certificate_runtime_seconds": round(certificate_elapsed, 8),
        "prefix_depth": prefix_depth,
        "levels": list(action_levels),
        "semantics": (
            "Exact-small-state correctness benchmark. False-prune results are "
            "meaningful for the supplied finite action set and linear SCM; "
            "large real datasets require separate empirical benchmarking."
        ),
        "records": certificate_records,
    }
