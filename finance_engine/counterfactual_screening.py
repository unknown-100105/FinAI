"""Conservative feasibility screening for bounded linear counterfactual DAGs.

Experimental FinAI component. This does not discover causal relationships;
callers must supply a validated structural model. Masked scenarios are those
that cannot reach the target interval under the supplied bounds. RETAIN means
only that the cheap screen could not prove the scenario impossible.
"""
from __future__ import annotations

from dataclasses import dataclass, field
import hashlib
import heapq
import json
import math
from typing import Callable, Iterable, Mapping


@dataclass(frozen=True, order=True)
class Interval:
    """Closed, finite interval [low, high]."""
    low: float
    high: float

    def __post_init__(self) -> None:
        if not math.isfinite(self.low) or not math.isfinite(self.high):
            raise ValueError("Interval bounds must be finite numbers.")
        if self.low > self.high:
            raise ValueError("Interval lower bound must not exceed upper bound.")

    @classmethod
    def point(cls, value: float) -> "Interval":
        return cls(float(value), float(value))

    def __add__(self, other: "Interval") -> "Interval":
        return Interval(self.low + other.low, self.high + other.high)

    def __sub__(self, other: "Interval") -> "Interval":
        return Interval(self.low - other.high, self.high - other.low)

    def scale(self, coefficient: float) -> "Interval":
        if not math.isfinite(coefficient):
            raise ValueError("Linear coefficients must be finite numbers.")
        if coefficient == 0:
            return Interval.point(0.0)
        pair = (self.low * coefficient, self.high * coefficient)
        return Interval(min(pair), max(pair))

    def intersection(self, other: "Interval") -> "Interval | None":
        low, high = max(self.low, other.low), min(self.high, other.high)
        return Interval(low, high) if low <= high else None

    def intersects(self, other: "Interval") -> bool:
        return max(self.low, other.low) <= min(self.high, other.high)

    def as_list(self) -> list[float]:
        return [self.low, self.high]


@dataclass(frozen=True)
class LinearNode:
    """Structural equation x = intercept + sum(coefficient * parent) + noise."""
    name: str
    domain: Interval
    parents: Mapping[str, float] = field(default_factory=dict)
    intercept: float = 0.0
    noise: Interval = Interval(0.0, 0.0)

    def __post_init__(self) -> None:
        if not self.name or not self.name.strip():
            raise ValueError("Node name must be non-empty.")
        if not math.isfinite(self.intercept):
            raise ValueError("Node intercept must be finite.")
        if any(not parent or not math.isfinite(c) for parent, c in self.parents.items()):
            raise ValueError("Parent names and coefficients must be valid.")


@dataclass(frozen=True)
class CounterfactualAction:
    """Candidate intervention; each intervention value is a bounded interval."""
    action_id: str
    interventions: Mapping[str, Interval]

    def __post_init__(self) -> None:
        if not self.action_id or not self.action_id.strip():
            raise ValueError("Action id must be non-empty.")


@dataclass(frozen=True)
class ScreeningCertificate:
    action_id: str
    status: str
    reason: str
    graph_version: str
    target: str
    target_interval: Interval
    reachable_target_interval: Interval | None
    backward_checks: tuple[tuple[str, Interval, Interval], ...]
    recomputed_nodes: tuple[str, ...]
    interval_equations_evaluated: int

    def as_dict(self) -> dict:
        return {
            "action_id": self.action_id,
            "status": self.status,
            "reason": self.reason,
            "graph_version": self.graph_version,
            "target": self.target,
            "target_interval": self.target_interval.as_list(),
            "reachable_target_interval": (
                self.reachable_target_interval.as_list()
                if self.reachable_target_interval is not None else None
            ),
            "backward_checks": [
                {"intervention_node": name,
                 "action_interval": action_iv.as_list(),
                 "necessary_interval": needed_iv.as_list()}
                for name, action_iv, needed_iv in self.backward_checks
            ],
            "recomputed_nodes": list(self.recomputed_nodes),
            "interval_equations_evaluated": self.interval_equations_evaluated,
        }


class BoundedLinearDAG:
    """Interval-bound structural model for conservative pre-simulation screening."""

    def __init__(self, nodes: Iterable[LinearNode]) -> None:
        node_list = list(nodes)
        self.nodes = {node.name: node for node in node_list}
        if len(self.nodes) != len(node_list):
            raise ValueError("Node names must be unique.")
        if not self.nodes:
            raise ValueError("A DAG must contain at least one node.")
        for node in node_list:
            for parent in node.parents:
                if parent not in self.nodes:
                    raise ValueError(f"Node {node.name!r} references unknown parent {parent!r}.")

        self.order = self._topological_order()
        self.children = {name: set() for name in self.nodes}
        for node in self.nodes.values():
            for parent, coefficient in node.parents.items():
                if coefficient != 0:
                    self.children[parent].add(node.name)

        payload = [
            {"name": n.name, "domain": n.domain.as_list(),
             "parents": sorted((p, float(c)) for p, c in n.parents.items()),
             "intercept": float(n.intercept), "noise": n.noise.as_list()}
            for n in sorted(self.nodes.values(), key=lambda item: item.name)
        ]
        self.graph_version = hashlib.sha256(
            json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest()[:20]

    def _topological_order(self) -> tuple[str, ...]:
        indegree = {
            name: sum(1 for c in node.parents.values() if c != 0)
            for name, node in self.nodes.items()
        }
        children = {name: [] for name in self.nodes}
        for node in self.nodes.values():
            for parent, coefficient in node.parents.items():
                if coefficient != 0:
                    children[parent].append(node.name)
        ready = [name for name, degree in indegree.items() if degree == 0]
        heapq.heapify(ready)
        order = []
        while ready:
            parent = heapq.heappop(ready)
            order.append(parent)
            for child in sorted(children[parent]):
                indegree[child] -= 1
                if indegree[child] == 0:
                    heapq.heappush(ready, child)
        if len(order) != len(self.nodes):
            raise ValueError("Structural model must be acyclic; cycle detected.")
        return tuple(order)

    def _equation_interval(self, node: LinearNode, ranges: Mapping[str, Interval]) -> Interval:
        value = Interval.point(node.intercept) + node.noise
        for parent, coefficient in node.parents.items():
            if coefficient != 0:
                value = value + ranges[parent].scale(coefficient)
        clipped = value.intersection(node.domain)
        if clipped is None:
            raise ValueError(f"No reachable value for node {node.name!r} inside its declared domain.")
        return clipped

    def baseline_ranges(self) -> dict[str, Interval]:
        ranges = {}
        for name in self.order:
            ranges[name] = self._equation_interval(self.nodes[name], ranges)
        return ranges

    def descendants(self, seed_nodes: Iterable[str]) -> set[str]:
        seen, pending = set(seed_nodes), list(seed_nodes)
        while pending:
            for child in self.children[pending.pop()]:
                if child not in seen:
                    seen.add(child)
                    pending.append(child)
        return seen

    def backward_necessary_ranges(
        self, target: str, target_interval: Interval
    ) -> tuple[dict[str, Interval], bool]:
        """Reverse-propagate conservative necessary intervals using declared domains.

        Parent dependencies are relaxed to their domains. This deliberately
        over-approximates feasible parent values to avoid aggressive pruning.
        """
        if target not in self.nodes:
            raise ValueError(f"Unknown target node: {target}")
        target_allowed = target_interval.intersection(self.nodes[target].domain)
        if target_allowed is None:
            return {}, True
        needed = {target: target_allowed}

        for child_name in reversed(self.order):
            child_needed = needed.get(child_name)
            if child_needed is None:
                continue
            child = self.nodes[child_name]
            base = child_needed - Interval.point(child.intercept) - child.noise
            for parent, coefficient in child.parents.items():
                if coefficient == 0:
                    continue
                residual = base
                for sibling, sibling_coefficient in child.parents.items():
                    if sibling != parent and sibling_coefficient != 0:
                        residual = residual - self.nodes[sibling].domain.scale(sibling_coefficient)
                parent_candidate = residual.scale(1.0 / coefficient).intersection(
                    self.nodes[parent].domain
                )
                if parent_candidate is None:
                    return needed, True
                previous = needed.get(parent)
                if previous is None:
                    needed[parent] = parent_candidate
                else:
                    combined = previous.intersection(parent_candidate)
                    if combined is None:
                        return needed, True
                    needed[parent] = combined
        return needed, False

    def screen_actions(
        self, target: str, target_interval: Interval,
        actions: Iterable[CounterfactualAction],
    ) -> list[ScreeningCertificate]:
        if target not in self.nodes:
            raise ValueError(f"Unknown target node: {target}")
        action_list = list(actions)
        ids = [a.action_id for a in action_list]
        if len(ids) != len(set(ids)):
            raise ValueError("Action ids must be unique within a screening batch.")
        for action in action_list:
            unknown = set(action.interventions) - set(self.nodes)
            if unknown:
                raise ValueError(
                    f"Action {action.action_id!r} references unknown nodes: {sorted(unknown)}"
                )

        baseline = self.baseline_ranges()
        necessary, globally_impossible = self.backward_necessary_ranges(target, target_interval)
        certificates = []

        for action in action_list:
            checks, normalized, reason = [], {}, None
            for node_name, proposed in action.interventions.items():
                in_domain = proposed.intersection(self.nodes[node_name].domain)
                if in_domain is None:
                    reason = f"INTERVENTION_OUTSIDE_DOMAIN:{node_name}"
                    break
                normalized[node_name] = in_domain
                needed = necessary.get(node_name)
                if needed is not None:
                    checks.append((node_name, in_domain, needed))
                    if not in_domain.intersects(needed):
                        reason = f"BACKWARD_CERTIFICATE_DISJOINT:{node_name}"
                        break

            if reason is None and globally_impossible:
                reason = "TARGET_INTERVAL_UNREACHABLE_BY_BOUNDED_MODEL"

            affected = self.descendants(normalized) if normalized else set()
            ranges = dict(baseline)
            recomputed, equation_evaluations = [], 0
            reachable_target = None if reason else baseline[target]

            if reason is None:
                for name in self.order:
                    if name not in affected:
                        continue
                    node = self.nodes[name]
                    if name in normalized:
                        value = normalized[name].intersection(node.domain)
                        if value is None:
                            reason = f"INTERVENTION_OUTSIDE_DOMAIN:{name}"
                            reachable_target = None
                            break
                        ranges[name] = value
                    else:
                        try:
                            ranges[name] = self._equation_interval(node, ranges)
                            equation_evaluations += 1
                        except ValueError:
                            reason = f"NO_REACHABLE_STATE:{name}"
                            reachable_target = None
                            break
                    recomputed.append(name)
                if reason is None:
                    reachable_target = ranges[target]
                    if not reachable_target.intersects(target_interval):
                        reason = "FORWARD_REACHABILITY_DISJOINT"

            certificates.append(ScreeningCertificate(
                action_id=action.action_id,
                status="MASK" if reason else "RETAIN",
                reason=reason or "POSSIBLE_TARGET_REQUIRES_EXACT_EVALUATION",
                graph_version=self.graph_version,
                target=target,
                target_interval=target_interval,
                reachable_target_interval=reachable_target,
                backward_checks=tuple(checks),
                recomputed_nodes=tuple(recomputed),
                interval_equations_evaluated=equation_evaluations,
            ))
        return certificates


def benchmark_screening(
    model: BoundedLinearDAG,
    target: str,
    target_interval: Interval,
    actions: Iterable[CounterfactualAction],
    reference_evaluator: Callable[[CounterfactualAction], bool],
) -> dict:
    """Compare screened candidates against a caller-supplied reference evaluator.

    The reference evaluator is called for every candidate to validate the screen,
    and again for retained candidates to model a filtered run. The callback may
    be analytic/exhaustive or sampled; all recall claims inherit its limitations.
    A production path would call the expensive evaluator only for RETAIN actions.
    """
    action_list = list(actions)
    certificates = model.screen_actions(target, target_interval, action_list)
    by_id = {c.action_id: c for c in certificates}
    exhaustive = {a.action_id: bool(reference_evaluator(a)) for a in action_list}
    retained = [a for a in action_list if by_id[a.action_id].status == "RETAIN"]
    screened = {a.action_id: bool(reference_evaluator(a)) for a in retained}
    exhaustive_feasible = {i for i, ok in exhaustive.items() if ok}
    screened_feasible = {i for i, ok in screened.items() if ok}
    missed = sorted(exhaustive_feasible - screened_feasible)
    pruned = [a.action_id for a in action_list if by_id[a.action_id].status == "MASK"]
    masked_feasible = sorted(exhaustive_feasible.intersection(pruned))
    recall = (
        len(exhaustive_feasible - set(missed)) / len(exhaustive_feasible)
        if exhaustive_feasible else 1.0
    )
    return {
        "graph_version": model.graph_version,
        "target": target,
        "target_interval": target_interval.as_list(),
        "candidate_count": len(action_list),
        "masked_count": len(pruned),
        "retained_count": len(retained),
        "exhaustive_reference_evaluation_calls": len(action_list),
        "screened_reference_evaluation_calls": len(retained),
        "candidate_evaluations_avoided": len(pruned),
        "candidate_evaluation_reduction_fraction": len(pruned) / len(action_list) if action_list else 0.0,
        "interval_equations_evaluated": sum(c.interval_equations_evaluated for c in certificates),
        "exhaustive_reference_feasible_action_ids": sorted(exhaustive_feasible),
        "screened_reference_feasible_action_ids": sorted(screened_feasible),
        "missed_reference_feasible_action_ids": missed,
        "masked_reference_feasible_action_ids": masked_feasible,
        "reference_recall": recall,
        "all_reference_feasible_actions_retained": not masked_feasible,
        "validation_reference_calls_including_crosscheck": len(action_list) + len(retained),
        "certificates": [c.as_dict() for c in certificates],
    }
