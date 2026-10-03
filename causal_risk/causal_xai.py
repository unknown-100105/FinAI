from __future__ import annotations

from collections import defaultdict
from typing import Dict, List, Sequence, Tuple


def explain_paths(
    edges: Sequence[Tuple[str, str, float]],
    interventions: Sequence[str],
    target: str = "portfolio",
    max_paths: int = 12,
) -> List[Dict[str, object]]:
    """Enumerate directed structural paths and rank them by path strength."""
    children: dict[str, list[tuple[str, float]]] = defaultdict(list)
    for src, dst, weight in edges:
        children[src].append((dst, float(weight)))

    paths: list[Dict[str, object]] = []

    def walk(node: str, path: list[str], strength: float) -> None:
        if node == target:
            paths.append(
                {
                    "path": path,
                    "strength": round(strength, 6),
                    "type": "structural-causal-path",
                }
            )
            return
        for child, weight in sorted(children[node], key=lambda item: abs(item[1]), reverse=True):
            if child in path:
                continue
            walk(child, path + [child], strength * weight)

    for root in interventions:
        walk(root, [root], 1.0)

    paths.sort(key=lambda item: float(item["strength"]), reverse=True)
    return paths[:max_paths]
