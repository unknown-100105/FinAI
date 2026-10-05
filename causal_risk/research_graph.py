"""Explicit approval gate for research-derived causal graphs."""
from __future__ import annotations

from collections import defaultdict, deque
from typing import Any, Mapping, Sequence


def validate_research_graph(
    nodes: Sequence[str],
    edges: Sequence[Mapping[str, Any]],
    *,
    min_selection_frequency: float = 0.75,
    require_sign_consistency: float = 0.90,
    approved: bool = False,
) -> dict[str, Any]:
    """Validate a discovered graph before it can be used in research counterfactuals.

    Approval is explicit and caller-controlled. This function never promotes a
    graph to production decision logic by itself.
    """
    labels = [str(node).strip() for node in nodes]
    errors: list[str] = []
    warnings: list[str] = []

    if len(labels) < 2 or any(not label for label in labels):
        errors.append("graph requires at least two non-empty node ids")
    if len(set(labels)) != len(labels):
        errors.append("graph node ids must be unique")
    if not 0.5 <= float(min_selection_frequency) <= 1.0:
        errors.append("min_selection_frequency must be between 0.5 and 1.0")
    if not 0.5 <= float(require_sign_consistency) <= 1.0:
        errors.append("require_sign_consistency must be between 0.5 and 1.0")

    node_set = set(labels)
    normalized: list[dict[str, Any]] = []
    adjacency: dict[str, list[str]] = defaultdict(list)

    for index, raw in enumerate(edges):
        try:
            source = str(raw["source"]).strip()
            target = str(raw["target"]).strip()
            weight = float(raw["weight"])
        except (KeyError, TypeError, ValueError):
            errors.append(f"edge {index} is missing valid source, target, or weight")
            continue

        lag = int(raw.get("lag", 0))
        frequency = float(raw.get("selection_frequency", 1.0))
        sign_consistency = float(raw.get("sign_consistency", 0.0))

        if source not in node_set or target not in node_set:
            errors.append(f"edge {index} references an unknown node")
        if source == target and lag == 0:
            errors.append(f"edge {index} contains a contemporaneous self-loop")
        if not (-2.0 <= weight <= 2.0):
            errors.append(f"edge {index} has an implausible research weight outside [-2,2]")
        if not 0.0 <= frequency <= 1.0:
            errors.append(f"edge {index} has invalid selection_frequency")
        if not 0.0 <= sign_consistency <= 1.0:
            errors.append(f"edge {index} has invalid sign_consistency")

        item = {
            "source": source,
            "target": target,
            "weight": weight,
            "lag": lag,
            "selection_frequency": frequency,
            "sign_consistency": sign_consistency,
            "stable": frequency >= min_selection_frequency,
            "sign_consistent": sign_consistency >= require_sign_consistency,
        }
        normalized.append(item)

        if lag == 0 and source != target:
            adjacency[source].append(target)

    # Kahn topological check for contemporaneous structure only. Lagged edges
    # are allowed to form temporal feedback across time without creating a
    # same-slice cycle.
    indegree = {node: 0 for node in labels}
    for source, children in adjacency.items():
        for target in children:
            indegree[target] += 1

    queue = deque(node for node, degree in indegree.items() if degree == 0)
    visited = 0
    while queue:
        node = queue.popleft()
        visited += 1
        for child in adjacency[node]:
            indegree[child] -= 1
            if indegree[child] == 0:
                queue.append(child)

    if visited != len(labels):
        errors.append("contemporaneous research graph contains a directed cycle")

    eligible = []
    rejected = []
    for item in normalized:
        if item["selection_frequency"] >= min_selection_frequency and item["sign_consistency"] >= require_sign_consistency:
            eligible.append(item)
        else:
            rejected.append({
                **item,
                "rejection_reasons": [
                    reason
                    for reason, failed in (
                        ("selection_frequency_below_threshold", item["selection_frequency"] < min_selection_frequency),
                        ("sign_consistency_below_threshold", item["sign_consistency"] < require_sign_consistency),
                    )
                    if failed
                ],
            })

    if not eligible:
        warnings.append("no edges meet the stability/sign-consistency gate")
    if normalized and len(rejected) > len(eligible):
        warnings.append("more candidate edges were rejected than retained")

    structurally_valid = not errors
    research_eligible = structurally_valid and bool(eligible)
    counterfactual_ready = research_eligible and bool(approved)

    return {
        "status": (
            "APPROVED_FOR_RESEARCH_COUNTERFACTUAL"
            if counterfactual_ready
            else "RESEARCH_GRAPH_ELIGIBLE_PENDING_APPROVAL"
            if research_eligible
            else "RESEARCH_GRAPH_REJECTED"
        ),
        "structurally_valid": structurally_valid,
        "research_eligible": research_eligible,
        "explicit_approval": bool(approved),
        "counterfactual_ready": counterfactual_ready,
        "nodes": labels,
        "candidate_edge_count": len(normalized),
        "eligible_edge_count": len(eligible),
        "rejected_edge_count": len(rejected),
        "eligible_edges": eligible,
        "rejected_edges": rejected,
        "thresholds": {
            "min_selection_frequency": min_selection_frequency,
            "require_sign_consistency": require_sign_consistency,
        },
        "errors": errors,
        "warnings": warnings,
        "safety_boundary": "This gate creates an explicit research approval state. It does not authorize or connect the graph to production investment decisions.",
    }
