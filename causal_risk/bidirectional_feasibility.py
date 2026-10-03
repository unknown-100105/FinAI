"""Bidirectional causal-feasibility pruning for financial stress search."""
from __future__ import annotations

from collections import defaultdict, deque
from typing import Any, Mapping, Sequence
import math


def _interval(raw: Sequence[float], name: str) -> tuple[float, float]:
    if len(raw) != 2:
        raise ValueError(f"{name} must contain [lower, upper]")
    lo, hi = float(raw[0]), float(raw[1])
    if not math.isfinite(lo) or not math.isfinite(hi) or lo > hi:
        raise ValueError(f"{name} must be finite with lower <= upper")
    return lo, hi


def backward_required_parent_interval(
    parent_bounds: Sequence[float],
    target_interval: Sequence[float],
    other_parent_contributions: Sequence[Sequence[float]],
    weight: float,
) -> tuple[float, float]:
    """Return a necessary parent interval for a linear target equation.

    Given y = w*x + sum(other contributions), every target-feasible assignment
    must place x inside this interval. The interval is necessary, not sufficient,
    so intersecting it with a candidate action range can safely remove actions
    that cannot reach the target.
    """
    p_lo, p_hi = _interval(parent_bounds, "parent_bounds")
    t_lo, t_hi = _interval(target_interval, "target_interval")
    w = float(weight)
    if not math.isfinite(w) or abs(w) < 1e-12:
        return p_lo, p_hi

    other_lo = 0.0
    other_hi = 0.0
    for raw in other_parent_contributions:
        lo, hi = _interval(raw, "other_parent_contribution")
        other_lo += lo
        other_hi += hi

    if w > 0:
        required_lo = (t_lo - other_hi) / w
        required_hi = (t_hi - other_lo) / w
    else:
        required_lo = (t_hi - other_lo) / w
        required_hi = (t_lo - other_hi) / w
    lo = max(p_lo, min(required_lo, required_hi))
    hi = min(p_hi, max(required_lo, required_hi))
    return lo, hi


def backward_target_cone(
    nodes: Sequence[str],
    edges: Sequence[Mapping[str, Any]],
    node_bounds: Mapping[str, Sequence[float]],
    *,
    target_node: str,
    target_interval: Sequence[float],
    intervened_nodes: Sequence[str] = (),
) -> dict[str, Any]:
    """Compute a conservative necessary interval for ancestors of a target."""
    labels = tuple(str(node) for node in nodes)
    if not labels or len(set(labels)) != len(labels):
        raise ValueError("nodes must be non-empty and unique")
    if str(target_node) not in labels:
        raise ValueError("target_node must exist in nodes")
    intervened = {str(node) for node in intervened_nodes}
    unknown_intervened = sorted(intervened - set(labels))
    if unknown_intervened:
        raise ValueError(f"intervened_nodes references unknown nodes: {unknown_intervened}")

    bounds = {node: _interval(node_bounds[node], f"node_bounds[{node}]") for node in labels}
    parents: dict[str, list[tuple[str, float]]] = defaultdict(list)
    children: dict[str, list[str]] = defaultdict(list)
    for index, raw in enumerate(edges):
        if int(raw.get("lag", 0)) != 0:
            continue
        source = str(raw["source"])
        target = str(raw["target"])
        if source not in bounds or target not in bounds or source == target:
            raise ValueError(f"invalid contemporaneous edge {index}")
        weight = float(raw["weight"])
        if not math.isfinite(weight):
            raise ValueError("edge weights must be finite")
        parents[target].append((source, weight))
        children[source].append(target)

    # Restrict to the ancestor cone to avoid unrelated graph work.
    ancestor_set = {str(target_node)}
    queue = [str(target_node)]
    reverse: dict[str, list[str]] = defaultdict(list)
    for child, plist in parents.items():
        for parent, _ in plist:
            reverse[child].append(parent)
    while queue:
        current = queue.pop()
        # A future intervention severs incoming structural edges for the
        # purposes of this necessary-condition calculation. Its value can be
        # chosen by the generator, so upstream ancestors cannot be required
        # from the target interval through this node.
        if current != str(target_node) and current in intervened:
            continue
        for parent in reverse[current]:
            if parent not in ancestor_set:
                ancestor_set.add(parent)
                queue.append(parent)

    required = {node: bounds[node] for node in labels}
    required[str(target_node)] = _interval(target_interval, "target_interval")

    # Process from target backwards. The calculated interval for each parent is
    # a necessary condition for the child target interval, not a sufficient set.
    backward_queue = deque([str(target_node)])
    visited = set()
    while backward_queue:
        child = backward_queue.popleft()
        if child in visited:
            continue
        visited.add(child)
        child_required = required[child]
        if child != str(target_node) and child in intervened:
            continue
        plist = parents[child]
        for parent, weight in plist:
            others = [
                required[other]
                for other, _ in plist
                if other != parent
            ]
            parent_required = backward_required_parent_interval(
                bounds[parent],
                child_required,
                others,
                weight,
            )
            current = required[parent]
            required[parent] = (
                max(current[0], parent_required[0]),
                min(current[1], parent_required[1]),
            )
            if required[parent][0] > required[parent][1]:
                required[parent] = (1.0, 0.0)
            if parent in ancestor_set:
                backward_queue.append(parent)

    return {
        "status": "BIDIRECTIONAL_TARGET_CONE_READY",
        "target_node": str(target_node),
        "target_interval": list(required[str(target_node)]),
        "required_intervals": {node: list(interval) for node, interval in required.items()},
        "intervened_nodes": sorted(intervened),
        "ancestor_nodes": sorted(ancestor_set),
        "semantics": (
            "Intervals are necessary conditions for reaching the target under "
            "the stated linear-DAG bounds. They are conservative for pruning: "
            "failure to intersect a required interval proves infeasibility, "
            "while intersection does not prove feasibility."
        ),
    }
