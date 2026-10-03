from __future__ import annotations

from collections import defaultdict, deque
from typing import Any, Dict, Iterable, Mapping, Sequence, Tuple


def _topological_order(nodes: Iterable[str], edges: Sequence[Tuple[str, str, float]]) -> list[str]:
    indegree = {node: 0 for node in nodes}
    children: dict[str, list[str]] = defaultdict(list)
    for src, dst, _ in edges:
        indegree[dst] = indegree.get(dst, 0) + 1
        children[src].append(dst)
    queue = deque(sorted(node for node, degree in indegree.items() if degree == 0))
    order = []
    while queue:
        node = queue.popleft()
        order.append(node)
        for child in sorted(children[node]):
            indegree[child] -= 1
            if indegree[child] == 0:
                queue.append(child)
    if len(order) != len(indegree):
        raise ValueError("causal graph contains a contemporaneous cycle")
    return order


def simulate_scm(
    nodes: Iterable[str],
    edges: Sequence[Tuple[str, str, float]],
    interventions: Mapping[str, float],
) -> Dict[str, Any]:
    """Evaluate a lightweight linear structural causal model.

    Intervened nodes are fixed at the supplied value; downstream nodes inherit
    weighted structural effects. Values are normalized stress changes, not prices.
    """
    node_ids = list(nodes)
    order = _topological_order(node_ids, edges)
    parents: dict[str, list[Tuple[str, float]]] = defaultdict(list)
    for src, dst, weight in edges:
        parents[dst].append((src, float(weight)))

    values = {node: 0.0 for node in node_ids}
    forced = set(interventions)
    for node in order:
        if node in forced:
            values[node] = float(interventions[node])
            continue
        values[node] = sum(values[src] * weight for src, weight in parents[node])

    contributions = []
    for src, dst, weight in edges:
        if values[src] == 0:
            continue
        contributions.append(
            {
                "source": src,
                "target": dst,
                "input": round(values[src], 6),
                "weight": round(weight, 6),
                "contribution": round(values[src] * weight, 6),
            }
        )

    return {
        "node_values": {key: round(value, 6) for key, value in values.items()},
        "interventions": {key: float(value) for key, value in interventions.items()},
        "edge_contributions": contributions,
        "order": order,
        "equations": [
            f"{dst} <- " + " + ".join(f"{weight:.2f}*{src}" for src, weight in parents[dst])
            for dst in order
            if parents[dst]
        ],
    }
