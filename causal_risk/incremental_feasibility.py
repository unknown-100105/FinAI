"""Incremental causal-feasibility evaluation for candidate stress prefixes."""
from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from typing import Any, Mapping, Sequence

import math


def _contribution_interval(parent: tuple[float, float], weight: float) -> tuple[float, float]:
    lo, hi = parent
    a, b = weight * lo, weight * hi
    return min(a, b), max(a, b)


@dataclass
class IncrementalIntervalState:
    nodes: tuple[str, ...]
    parents: dict[str, tuple[tuple[str, float], ...]]
    children: dict[str, tuple[str, ...]]
    bounds: dict[str, tuple[float, float]]
    order: tuple[str, ...]
    intervals: dict[str, tuple[float, float]]
    fixed: dict[str, float]
    interval_node_evaluations: int = 0

    @classmethod
    def build(
        cls,
        nodes: Sequence[str],
        edges: Sequence[Mapping[str, Any]],
        node_bounds: Mapping[str, Sequence[float]],
        fixed_values: Mapping[str, float] | None = None,
    ) -> "IncrementalIntervalState":
        labels = tuple(str(node) for node in nodes)
        if not labels or len(set(labels)) != len(labels):
            raise ValueError("nodes must be non-empty and unique")
        bounds: dict[str, tuple[float, float]] = {}
        for node in labels:
            if node not in node_bounds:
                raise ValueError(f"node_bounds missing node: {node}")
            raw = node_bounds[node]
            if len(raw) != 2:
                raise ValueError(f"node_bounds[{node}] must contain [lower, upper]")
            lo, hi = float(raw[0]), float(raw[1])
            if not math.isfinite(lo) or not math.isfinite(hi) or lo > hi:
                raise ValueError(f"node_bounds[{node}] must be finite with lower <= upper")
            bounds[node] = (lo, hi)

        parent_lists: dict[str, list[tuple[str, float]]] = {node: [] for node in labels}
        child_lists: dict[str, list[str]] = {node: [] for node in labels}
        indegree = {node: 0 for node in labels}
        for index, raw in enumerate(edges):
            source = str(raw["source"])
            target = str(raw["target"])
            lag = int(raw.get("lag", 0))
            if lag != 0:
                continue
            if source not in indegree or target not in indegree:
                raise ValueError(f"edge {index} references unknown node")
            if source == target:
                raise ValueError("contemporaneous self-loop is not supported")
            weight = float(raw["weight"])
            parent_lists[target].append((source, weight))
            child_lists[source].append(target)
            indegree[target] += 1

        queue = sorted(node for node, degree in indegree.items() if degree == 0)
        order: list[str] = []
        while queue:
            node = queue.pop(0)
            order.append(node)
            for child in sorted(child_lists[node]):
                indegree[child] -= 1
                if indegree[child] == 0:
                    queue.append(child)
        if len(order) != len(labels):
            raise ValueError("contemporaneous graph contains a directed cycle")

        state = cls(
            nodes=labels,
            parents={node: tuple(parent_lists[node]) for node in labels},
            children={node: tuple(sorted(child_lists[node])) for node in labels},
            bounds=bounds,
            order=tuple(order),
            intervals={},
            fixed={},
        )
        state.set_fixed(fixed_values or {})
        return state

    def _recompute_node(self, node: str) -> None:
        self.interval_node_evaluations += 1
        if node in self.fixed:
            value = self.fixed[node]
            self.intervals[node] = (value, value)
            return
        if not self.parents[node]:
            self.intervals[node] = self.bounds[node]
            return
        lo = 0.0
        hi = 0.0
        for parent, weight in self.parents[node]:
            p_lo, p_hi = self.intervals[parent]
            c_lo, c_hi = _contribution_interval((p_lo, p_hi), weight)
            lo += c_lo
            hi += c_hi
        bound_lo, bound_hi = self.bounds[node]
        self.intervals[node] = (max(lo, bound_lo), min(hi, bound_hi))

    def _descendants_in_order(self, changed_node: str) -> tuple[str, ...]:
        affected = {changed_node}
        stack = [changed_node]
        while stack:
            current = stack.pop()
            for child in self.children[current]:
                if child not in affected:
                    affected.add(child)
                    stack.append(child)
        return tuple(node for node in self.order if node in affected)

    def set_fixed(self, fixed_values: Mapping[str, float]) -> None:
        fixed = {str(key): float(value) for key, value in fixed_values.items()}
        unknown = [node for node in fixed if node not in self.bounds]
        if unknown:
            raise ValueError(f"fixed_values references unknown nodes: {unknown}")
        self.fixed = fixed
        self.intervals.clear()
        for node in self.order:
            self._recompute_node(node)

    def preview_change(self, node: str, value: float) -> dict[str, Any]:
        node = str(node)
        value = float(value)
        if node not in self.bounds or not math.isfinite(value):
            raise ValueError("node must exist and value must be finite")

        old_fixed = dict(self.fixed)
        old_intervals = dict(self.intervals)
        old_count = self.interval_node_evaluations

        self.fixed[node] = value
        for affected in self._descendants_in_order(node):
            self._recompute_node(affected)

        result = {
            "intervals": dict(self.intervals),
            "reachable_interval": self.intervals[node] if node in self.intervals else None,
            "node_evaluations": self.interval_node_evaluations - old_count,
            "affected_nodes": list(self._descendants_in_order(node)),
        }

        self.fixed = old_fixed
        self.intervals = old_intervals
        self.interval_node_evaluations = old_count
        return result

    def target_interval_preview(
        self,
        node: str,
        value: float,
        *,
        target_node: str,
        target_interval: Sequence[float],
    ) -> dict[str, Any]:
        if len(target_interval) != 2:
            raise ValueError("target_interval must contain [lower, upper]")
        target_lo, target_hi = float(target_interval[0]), float(target_interval[1])
        if not math.isfinite(target_lo) or not math.isfinite(target_hi) or target_lo > target_hi:
            raise ValueError("target_interval must be finite with lower <= upper")
        preview = self.preview_change(node, value)
        reachable_lo, reachable_hi = preview["intervals"][str(target_node)]
        margin = min(reachable_hi - target_lo, target_hi - reachable_lo)
        preview.update({
            "target_node": str(target_node),
            "target_interval": [target_lo, target_hi],
            "margin": float(margin),
            "hard_infeasible": margin < 0.0,
        })
        return preview
