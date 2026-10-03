"""Causal-feasibility screening for generative financial stress trajectories.

This module provides a research mechanism for evaluating partial stress prefixes
with cheap interval arithmetic before invoking a full structural causal model.
The interval certificate is conservative for a linear DAG with explicit node
bounds: a prefix is hard-infeasible only when its reachable target interval cannot
overlap the admissible target interval.

The adaptive controller is deliberately separated from the hard certificate.
Budget-based heuristic pruning never changes the hard-infeasibility semantics.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Sequence

import math
import numpy as np


@dataclass(frozen=True)
class FeasibilityCertificate:
    target_node: str
    target_interval: tuple[float, float]
    reachable_interval: tuple[float, float]
    hard_infeasible: bool
    margin: float
    empirical_support_ok: bool
    fixed_violations: tuple[str, ...]
    reason: str
    intervened_nodes: tuple[str, ...] = ()

    def as_dict(self) -> dict[str, Any]:
        return {
            "target_node": self.target_node,
            "target_interval": list(self.target_interval),
            "reachable_interval": list(self.reachable_interval),
            "hard_infeasible": self.hard_infeasible,
            "margin": round(float(self.margin), 8),
            "empirical_support_ok": self.empirical_support_ok,
            "fixed_violations": list(self.fixed_violations),
            "reason": self.reason,
            "intervened_nodes": list(self.intervened_nodes),
            "certificate_type": "conservative_linear_dag_interval_outer_bound",
        }


def _validate_interval(interval: Sequence[float], name: str) -> tuple[float, float]:
    if len(interval) != 2:
        raise ValueError(f"{name} must contain [lower, upper]")
    lo, hi = float(interval[0]), float(interval[1])
    if not math.isfinite(lo) or not math.isfinite(hi) or lo > hi:
        raise ValueError(f"{name} must be finite with lower <= upper")
    return lo, hi


def _contribution_interval(
    parent_interval: tuple[float, float],
    weight: float,
) -> tuple[float, float]:
    lo, hi = parent_interval
    a, b = weight * lo, weight * hi
    return min(a, b), max(a, b)


def propagate_interval_bounds(
    nodes: Sequence[str],
    edges: Sequence[Mapping[str, Any]],
    fixed_values: Mapping[str, float],
    node_bounds: Mapping[str, Sequence[float]],
    intervened_nodes: Sequence[str] = (),
) -> dict[str, tuple[float, float]]:
    """Propagate linear SCM intervals through a contemporaneous DAG."""
    labels = [str(node) for node in nodes]
    if len(labels) < 1 or len(set(labels)) != len(labels):
        raise ValueError("nodes must be non-empty and unique")

    bounds = {
        node: _validate_interval(node_bounds[node], f"node_bounds[{node}]")
        for node in labels
        if node in node_bounds
    }
    missing = [node for node in labels if node not in bounds]
    if missing:
        raise ValueError(f"node_bounds missing nodes: {missing}")

    fixed = {str(k): float(v) for k, v in fixed_values.items()}
    intervened = {str(node) for node in intervened_nodes}
    unknown_fixed = [node for node in fixed if node not in labels]
    unknown_intervened = [node for node in intervened if node not in labels]
    if unknown_intervened:
        raise ValueError(f"intervened_nodes references unknown nodes: {unknown_intervened}")
    overlap = sorted(set(fixed) & intervened)
    if overlap:
        raise ValueError(f"fixed_values and intervened_nodes overlap: {overlap}")
    if unknown_fixed:
        raise ValueError(f"fixed_values references unknown nodes: {unknown_fixed}")
    if not np.isfinite(np.asarray(list(fixed.values()), dtype=float)).all():
        raise ValueError("fixed_values must be finite")

    parents: dict[str, list[tuple[str, float]]] = {node: [] for node in labels}
    children: dict[str, list[str]] = {node: [] for node in labels}
    indegree = {node: 0 for node in labels}

    for index, raw in enumerate(edges):
        source = str(raw["source"])
        target = str(raw["target"])
        weight = float(raw["weight"])
        lag = int(raw.get("lag", 0))
        if source not in indegree or target not in indegree:
            raise ValueError(f"edge {index} references an unknown node")
        if lag != 0:
            continue
        if source == target:
            raise ValueError("contemporaneous self-loop is not supported")
        parents[target].append((source, weight))
        children[source].append(target)
        indegree[target] += 1

    queue = sorted(node for node, degree in indegree.items() if degree == 0)
    order: list[str] = []
    while queue:
        node = queue.pop(0)
        order.append(node)
        for child in sorted(children[node]):
            indegree[child] -= 1
            if indegree[child] == 0:
                queue.append(child)
    if len(order) != len(labels):
        raise ValueError("contemporaneous graph contains a directed cycle")

    intervals: dict[str, tuple[float, float]] = {}
    for node in order:
        if node in fixed:
            intervals[node] = (fixed[node], fixed[node])
            continue
        if node in intervened:
            intervals[node] = bounds[node]
            continue
        if parents[node]:
            lo = 0.0
            hi = 0.0
            for parent, weight in parents[node]:
                p_lo, p_hi = intervals[parent]
                c_lo, c_hi = _contribution_interval((p_lo, p_hi), weight)
                lo += c_lo
                hi += c_hi
            base_lo, base_hi = bounds[node]
            intervals[node] = (max(lo, base_lo), min(hi, base_hi))
        else:
            intervals[node] = bounds[node]
    return intervals


def evaluate_prefix_feasibility(
    nodes: Sequence[str],
    edges: Sequence[Mapping[str, Any]],
    fixed_values: Mapping[str, float],
    node_bounds: Mapping[str, Sequence[float]],
    *,
    target_node: str,
    target_interval: Sequence[float],
    intervened_nodes: Sequence[str] = (),
    empirical_center: Mapping[str, float] | None = None,
    empirical_scale: Mapping[str, float] | None = None,
    max_standardized_deviation: float = 4.0,
) -> FeasibilityCertificate:
    """Build a conservative hard-feasibility certificate for a partial prefix."""
    target_lo, target_hi = _validate_interval(target_interval, "target_interval")
    labels = {str(node) for node in nodes}
    if str(target_node) not in labels:
        raise ValueError("target_node must exist in nodes")
    fixed = {str(k): float(v) for k, v in fixed_values.items()}
    intervened = tuple(dict.fromkeys(str(node) for node in intervened_nodes))
    unknown_intervened = [node for node in intervened if node not in labels]
    if str(target_node) in intervened:
        raise ValueError("target_node cannot be a future intervention")
    overlap = sorted(set(fixed) & set(intervened))
    if unknown_intervened:
        raise ValueError(f"intervened_nodes references unknown nodes: {unknown_intervened}")
    if overlap:
        raise ValueError(f"fixed_values and intervened_nodes overlap: {overlap}")

    violations: list[str] = []
    for node, value in fixed.items():
        lo, hi = _validate_interval(node_bounds[node], f"node_bounds[{node}]")
        if value < lo or value > hi:
            violations.append(
                f"{node}={value:.6f} outside hard bounds [{lo:.6f},{hi:.6f}]"
            )

    support_ok = True
    if empirical_center is not None or empirical_scale is not None:
        if empirical_center is None or empirical_scale is None:
            raise ValueError("empirical_center and empirical_scale must be supplied together")
        if max_standardized_deviation <= 0 or not math.isfinite(max_standardized_deviation):
            raise ValueError("max_standardized_deviation must be positive and finite")
        for node, value in fixed.items():
            if node not in empirical_center or node not in empirical_scale:
                continue
            center = float(empirical_center[node])
            scale = float(empirical_scale[node])
            if not math.isfinite(center) or not math.isfinite(scale) or scale <= 0:
                raise ValueError(f"invalid empirical center/scale for {node}")
            z = abs((value - center) / scale)
            if z > max_standardized_deviation:
                support_ok = False
                violations.append(
                    f"{node} standardized deviation {z:.6f} exceeds "
                    f"{max_standardized_deviation:.6f}"
                )

    if violations:
        return FeasibilityCertificate(
            target_node=str(target_node),
            target_interval=(target_lo, target_hi),
            reachable_interval=(float("nan"), float("nan")),
            hard_infeasible=True,
            margin=float("-inf"),
            empirical_support_ok=support_ok,
            fixed_violations=tuple(violations),
            reason="fixed-prefix constraint violation",
            intervened_nodes=intervened,
        )

    intervals = propagate_interval_bounds(
        nodes,
        edges,
        fixed,
        node_bounds,
        intervened_nodes=intervened,
    )
    reachable_lo, reachable_hi = intervals[str(target_node)]
    margin = min(reachable_hi - target_lo, target_hi - reachable_lo)
    hard_infeasible = margin < 0.0
    reason = (
        "target interval has no overlap with conservative reachable interval"
        if hard_infeasible
        else "target interval overlaps conservative reachable interval"
    )
    return FeasibilityCertificate(
        target_node=str(target_node),
        target_interval=(target_lo, target_hi),
        reachable_interval=(reachable_lo, reachable_hi),
        hard_infeasible=hard_infeasible,
        margin=margin,
        empirical_support_ok=support_ok,
        fixed_violations=(),
        reason=reason,
        intervened_nodes=intervened,
    )


@dataclass
class AdaptivePruningController:
    """Budget controller for post-certificate heuristic pruning.

    The hard certificate remains authoritative. This controller adapts only the
    secondary margin used to reduce compute after all hard-infeasible candidates
    have already been removed.
    """

    target_full_eval_fraction: float = 0.25
    margin_step: float = 0.05
    margin_floor: float = -1.0
    margin_ceiling: float = 1.0
    minimum_high_risk_recall: float = 0.99
    current_margin: float = 0.0

    def __post_init__(self) -> None:
        if not 0.0 < self.target_full_eval_fraction <= 1.0:
            raise ValueError("target_full_eval_fraction must be in (0,1]")
        if self.margin_step <= 0:
            raise ValueError("margin_step must be positive")
        if not 0.0 < self.minimum_high_risk_recall <= 1.0:
            raise ValueError("minimum_high_risk_recall must be in (0,1]")
        if self.margin_floor > self.margin_ceiling:
            raise ValueError("margin_floor must not exceed margin_ceiling")
        self.current_margin = float(
            min(max(self.current_margin, self.margin_floor), self.margin_ceiling)
        )

    def update(
        self,
        observed_full_eval_fraction: float,
        observed_high_risk_recall: float | None = None,
    ) -> float:
        observed = float(observed_full_eval_fraction)
        if not math.isfinite(observed) or not 0.0 <= observed <= 1.0:
            raise ValueError("observed_full_eval_fraction must be between 0 and 1")
        if observed_high_risk_recall is not None:
            recall = float(observed_high_risk_recall)
            if not math.isfinite(recall) or not 0.0 <= recall <= 1.0:
                raise ValueError("observed_high_risk_recall must be between 0 and 1")
            if recall < self.minimum_high_risk_recall:
                # Recall protection dominates compute optimization.
                self.current_margin = self.margin_floor
                return self.current_margin
        if observed > self.target_full_eval_fraction:
            self.current_margin = min(
                self.margin_ceiling,
                self.current_margin + self.margin_step,
            )
        elif observed < self.target_full_eval_fraction:
            self.current_margin = max(
                self.margin_floor,
                self.current_margin - self.margin_step,
            )
        return self.current_margin

    def metadata(self) -> dict[str, float]:
        return {
            "target_full_eval_fraction": self.target_full_eval_fraction,
            "current_margin": self.current_margin,
            "margin_step": self.margin_step,
            "minimum_high_risk_recall": self.minimum_high_risk_recall,
        }


def screen_candidate_actions(
    nodes: Sequence[str],
    edges: Sequence[Mapping[str, Any]],
    prefix: Mapping[str, float],
    candidate_actions: Mapping[str, Sequence[float]],
    node_bounds: Mapping[str, Sequence[float]],
    *,
    target_node: str,
    target_interval: Sequence[float],
    empirical_center: Mapping[str, float] | None = None,
    empirical_scale: Mapping[str, float] | None = None,
    controller: AdaptivePruningController | None = None,
) -> dict[str, Any]:
    """Evaluate one-step candidate actions using certificates.

    Each candidate receives a certificate before any expensive structural
    simulation. Hard-infeasible candidates are always pruned. Optional budget
    pruning applies only to hard-feasible candidates with low certificate margin.
    """
    results: list[dict[str, Any]] = []
    total = 0
    hard_pruned = 0
    heuristic_pruned = 0

    for node, actions in candidate_actions.items():
        for action in actions:
            total += 1
            candidate = dict(prefix)
            candidate[str(node)] = float(action)
            certificate = evaluate_prefix_feasibility(
                nodes,
                edges,
                candidate,
                node_bounds,
                target_node=target_node,
                target_interval=target_interval,
                empirical_center=empirical_center,
                empirical_scale=empirical_scale,
            )
            heuristic = (
                controller is not None
                and not certificate.hard_infeasible
                and certificate.margin < controller.current_margin
            )
            pruned = certificate.hard_infeasible or heuristic
            if certificate.hard_infeasible:
                hard_pruned += 1
            elif heuristic:
                heuristic_pruned += 1
            results.append({
                "node": str(node),
                "action": float(action),
                "pruned": pruned,
                "prune_type": (
                    "hard_certificate"
                    if certificate.hard_infeasible
                    else "adaptive_budget"
                    if heuristic
                    else "accepted"
                ),
                "certificate": certificate.as_dict(),
            })

    accepted = total - hard_pruned - heuristic_pruned
    return {
        "status": "CAUSAL_FEASIBILITY_SCREENING_READY",
        "total_candidates": total,
        "accepted_candidates": accepted,
        "hard_pruned_candidates": hard_pruned,
        "adaptive_pruned_candidates": heuristic_pruned,
        "full_evaluation_fraction": accepted / total if total else 0.0,
        "candidates": results,
        "controller": controller.metadata() if controller else None,
        "semantics": (
            "Hard pruning is conservative for the stated linear-DAG bounds. "
            "Adaptive budget pruning is heuristic and must be recall-validated "
            "against a full-evaluation baseline."
        ),
    }
