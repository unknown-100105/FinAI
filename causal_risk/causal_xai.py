from __future__ import annotations

from collections import defaultdict
from typing import Dict, List, Sequence, Tuple


def explain_paths(
    edges: Sequence[Tuple[str, str, float]],
    interventions: Sequence[str],
    target: str = "portfolio",
    max_paths: int = 12,
) -> List[Dict[str, object]]:
    children: dict[str, list[tuple[str, float]]] = defaultdict(list)
    for src, dst, weight in edges:
        children[src].append((dst, float(weight)))

    paths: list[Dict[str, object]] = []

    def walk(node: str, path: list[str], strength: float) -> None:
        if len(paths) >= max_paths:
            return
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
    return paths
