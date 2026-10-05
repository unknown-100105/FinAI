"""Consensus-gating utilities for causal discovery research."""
from __future__ import annotations

from typing import Any, Dict


def build_consensus_graph(stability: Dict[str, Any]) -> Dict[str, Any]:
    """Create a research candidate graph from stable, non-conflicting edges.

    This gate is deliberately downstream of stability analysis. It does not
    claim that the retained edges are identified causal effects.
    """
    candidates = []
    rejected = []

    for modality in ("contemporaneous", "temporal"):
        block = stability.get(modality, {})
        for edge in block.get("ranked_edges", []):
            item = {
                "edge": edge["edge"],
                "modality": modality,
                "selection_frequency": edge["selection_frequency"],
                "sign_consistency": edge["sign_consistency"],
                "mean_weight": edge.get("mean_weight", 0.0),
                "mean_abs_weight": edge["mean_abs_weight"],
                "stable": edge["stable"],
                "direction_conflict": edge.get("direction_conflict", False),
                "consensus_eligible": edge.get("consensus_eligible", False),
            }
            (candidates if item["consensus_eligible"] else rejected).append(item)

    candidates.sort(key=lambda item: (-float(item["selection_frequency"]), item["edge"], item["modality"]))
    rejected.sort(key=lambda item: (item["edge"], item["modality"]))

    graph_edges = []
    for item in candidates:
        key = item["edge"]
        lag = 0
        edge_key = key
        if "|lag=" in key:
            edge_key, lag_text = key.split("|lag=", 1)
            lag = int(lag_text)
        source, target = edge_key.split("->", 1)
        graph_edges.append({
            "source": source,
            "target": target,
            "weight": item["mean_weight"],
            "lag": lag,
            "modality": "consensus-" + item["modality"],
            "selection_frequency": item["selection_frequency"],
            "sign_consistency": item["sign_consistency"],
        })

    conflict_count = sum(
        1
        for modality in ("contemporaneous", "temporal")
        for edge in stability.get(modality, {}).get("direction_conflicts", [])
    )

    return {
        "status": "CONSENSUS_RESEARCH_GRAPH_READY" if candidates else "NO_CONSENSUS_EDGES",
        "edge_count": len(graph_edges),
        "edges": graph_edges,
        "rejected_edge_count": len(rejected),
        "rejected_edges": rejected,
        "direction_conflicts": conflict_count,
        "safety_boundary": "Consensus edges are research candidates only. They must be independently identified and empirically validated before influencing production decisions.",
    }
