"""Research-only counterfactual execution over an explicitly approved graph."""
from __future__ import annotations

from typing import Any, Mapping, Sequence

from causal_risk.engine import _channels_from_scm
from causal_risk.risk_calibration import load_risk_calibration
from causal_risk.scm import simulate_scm
from causal_risk.causal_xai import explain_paths
from causal_risk.constraints import validate_allocation, validate_shocks
from causal_risk.research_graph import validate_research_graph
from causal_risk.schema import DEFAULT_NODES


RESEARCH_SHOCKS = ("rates", "supply", "oil", "credit", "usd")


def run_research_counterfactual(
    shock: Mapping[str, float],
    allocation: Mapping[str, float],
    nodes: Sequence[str],
    edges: Sequence[Mapping[str, Any]],
    *,
    approved: bool = False,
) -> dict[str, Any]:
    gate = validate_research_graph(nodes, edges, approved=approved)
    if not gate["counterfactual_ready"]:
        raise ValueError("research graph is not explicitly approved for counterfactual execution")

    allocation_check = validate_allocation(dict(allocation))
    shock_check = validate_shocks(dict(shock), RESEARCH_SHOCKS)
    if not allocation_check["passed"]:
        raise ValueError("; ".join(allocation_check["errors"]))
    if not shock_check["passed"]:
        raise ValueError("; ".join(shock_check["errors"]))

    node_ids = tuple(str(node) for node in nodes)
    edge_tuples = tuple(
        (
            str(edge["source"]),
            str(edge["target"]),
            float(edge["weight"]),
        )
        for edge in gate["eligible_edges"]
        if int(edge.get("lag", 0)) == 0
    )
    normalized = {str(key): float(value) / 100.0 for key, value in shock.items()}
    scm = simulate_scm(node_ids, edge_tuples, normalized)
    calibration = load_risk_calibration()
    channels = _channels_from_scm(
        {key: value * 100.0 for key, value in scm["node_values"].items()},
        dict(allocation),
        calibration,
    )
    interventions = tuple(key for key in shock if key in RESEARCH_SHOCKS)
    paths = explain_paths(edge_tuples, interventions, target="portfolio")

    return {
        "status": "RESEARCH_COUNTERFACTUAL_EXECUTED",
        "gate": gate,
        "systemic_stress": channels["systemic_stress"],
        "channels": channels,
        "interventions": dict(shock),
        "allocation": dict(allocation),
        "structural_model": {
            "method": "approved research linear SCM",
            "intervention_operator": "do(X=x)",
            "node_values": scm["node_values"],
            "edge_contributions": scm["edge_contributions"],
        },
        "explanation": {
            "primary_path": paths[0]["path"] if paths else [],
            "paths": paths,
        },
        "risk_calibration": {
            "version": calibration.get("version"),
            "status": calibration.get("status"),
            "causal_identification": calibration.get("validation", {}).get("causal_identification", False),
        },
        "production_boundary": (
            "This endpoint executes only an explicitly approved research graph "
            "and does not connect the result to production investment decisions."
        ),
    }
