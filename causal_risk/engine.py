"""Integrated causal-risk engine for FinAI research workflows."""
from __future__ import annotations

from typing import Any, Dict

import numpy as np

from causal_risk.causal_xai import explain_paths
from causal_risk.constraints import validate_allocation, validate_shocks
from causal_risk.schema import DEFAULT_EDGES, DEFAULT_NODES, graph_payload, validate_graph
from causal_risk.scm import simulate_scm
from causal_risk.tail_scenarios import generate_tail_scenarios
from causal_risk.risk_calibration import load_risk_calibration


EDGE_TUPLES = tuple((edge.source, edge.target, edge.weight) for edge in DEFAULT_EDGES)
NODE_IDS = tuple(node.node_id for node in DEFAULT_NODES)
ALLOWED_SHOCKS = ("rates", "supply", "oil", "credit", "usd")


def _clamp(x: float, lo: float = -100.0, hi: float = 100.0) -> float:
    return max(lo, min(hi, x))


def _channels_from_scm(
    values: Dict[str, float],
    allocation: Dict[str, float],
    calibration: Dict[str, Any],
) -> Dict[str, float]:
    coefficients = calibration["coefficients"]
    liquidity = _clamp(values.get("liquidity", 0.0))
    equity = _clamp(
        values.get("equity", 0.0)
        + liquidity * float(coefficients["equity_from_liquidity"])
    )
    debt = _clamp(
        values.get("rates", 0.0) * float(coefficients["debt_from_rates"])
        + values.get("credit", 0.0) * float(coefficients["debt_from_credit"])
        + values.get("oil", 0.0) * float(coefficients["debt_from_oil"])
        + liquidity * float(coefficients["debt_from_liquidity"])
    )
    gold = allocation.get("gold", 0.0) * (
        values.get("usd", 0.0) * float(coefficients["gold_from_usd"])
        + values.get("rates", 0.0) * float(coefficients["gold_from_rates"])
        + values.get("oil", 0.0) * float(coefficients["gold_from_oil"])
    )
    drawdown = (
        allocation.get("equity", 0.0) * equity
        + allocation.get("debt", 0.0) * debt
        + gold
    ) / 100.0
    systemic = _clamp(
        abs(liquidity) * float(coefficients["systemic_liquidity"])
        + abs(equity) * float(coefficients["systemic_equity"])
        + abs(debt) * float(coefficients["systemic_debt"])
        + abs(drawdown) * float(coefficients["systemic_drawdown"]),
        0.0,
        100.0,
    )
    return {
        "liquidity": round(liquidity, 3),
        "equity": round(equity, 3),
        "debt": round(debt, 3),
        "portfolio": round(drawdown, 3),
        "systemic_stress": round(systemic, 3),
    }


def _evaluate_structural_shock(
    shock: Dict[str, float],
    allocation: Dict[str, float],
    calibration: Dict[str, Any],
) -> Dict[str, Any]:
    normalized = {key: value / 100.0 for key, value in shock.items()}
    scm = simulate_scm(NODE_IDS, EDGE_TUPLES, normalized)
    channels = _channels_from_scm(
        {key: value * 100.0 for key, value in scm["node_values"].items()},
        allocation,
        calibration,
    )
    interventions = tuple(key for key in shock if key in ALLOWED_SHOCKS)
    paths = explain_paths(EDGE_TUPLES, interventions, target="portfolio")
    return {"scm": scm, "channels": channels, "paths": paths}


def _percentiles(values: list[float]) -> Dict[str, float]:
    if not values:
        return {"p90": 0.0, "p95": 0.0, "p99": 0.0}
    data = np.asarray(values, dtype=float)
    return {
        "p90": round(float(np.quantile(data, 0.90)), 3),
        "p95": round(float(np.quantile(data, 0.95)), 3),
        "p99": round(float(np.quantile(data, 0.99)), 3),
    }


def _evaluate_tail_scenarios(
    tail: Dict[str, Any],
    allocation: Dict[str, float],
    calibration: Dict[str, Any],
) -> Dict[str, Any]:
    evaluated = []
    systemic_values: list[float] = []
    portfolio_values: list[float] = []

    for scenario in tail["scenarios"]:
        shock = {str(key): float(value) for key, value in scenario["shock"].items()}
        result = _evaluate_structural_shock(shock, allocation, calibration)
        channels = result["channels"]
        systemic_values.append(float(channels["systemic_stress"]))
        portfolio_values.append(float(channels["portfolio"]))
        evaluated.append(
            {
                "scenario_id": scenario["scenario_id"],
                "shock": shock,
                "tail_score": scenario["tail_score"],
                "systemic_stress": channels["systemic_stress"],
                "portfolio_impact": channels["portfolio"],
                "channels": {
                    key: channels[key]
                    for key in ("liquidity", "equity", "debt")
                },
                "primary_path": result["paths"][0]["path"] if result["paths"] else [],
            }
        )

    systemic_pct = _percentiles(systemic_values)
    portfolio_pct = _percentiles([abs(value) for value in portfolio_values])
    worst = max(
        evaluated,
        key=lambda item: float(item["systemic_stress"]),
        default=None,
    )

    return {
        "status": "SCM_EVALUATED",
        "scenario_count": len(evaluated),
        "summary": {
            "mean_systemic_stress": round(float(np.mean(systemic_values)), 3)
            if systemic_values
            else 0.0,
            "max_systemic_stress": round(float(max(systemic_values)), 3)
            if systemic_values
            else 0.0,
            "systemic_stress_p90": systemic_pct["p90"],
            "systemic_stress_p95": systemic_pct["p95"],
            "systemic_stress_p99": systemic_pct["p99"],
            "mean_portfolio_impact": round(float(np.mean(portfolio_values)), 3)
            if portfolio_values
            else 0.0,
            "absolute_portfolio_impact_p90": portfolio_pct["p90"],
            "absolute_portfolio_impact_p95": portfolio_pct["p95"],
            "absolute_portfolio_impact_p99": portfolio_pct["p99"],
            "highest_stress_scenario_id": worst["scenario_id"] if worst else None,
        },
        "scenarios": evaluated,
    }


def run_counterfactual(
    shock: Dict[str, float],
    allocation: Dict[str, float],
    *,
    include_tail_scenarios: bool = False,
    tail_correlation: Any = None,
    tail_distribution: str = "gaussian",
    tail_degrees_of_freedom: float = 5.0,
) -> Dict[str, Any]:
    shock = {str(key): float(value) for key, value in shock.items()}
    allocation = {str(key): float(value) for key, value in allocation.items()}
    calibration = load_risk_calibration()

    allocation_check = validate_allocation(allocation)
    shock_check = validate_shocks(shock, ALLOWED_SHOCKS)
    if not allocation_check["passed"]:
        raise ValueError("; ".join(allocation_check["errors"]))
    if not shock_check["passed"]:
        raise ValueError("; ".join(shock_check["errors"]))

    structural = _evaluate_structural_shock(shock, allocation, calibration)
    scm = structural["scm"]
    channels = structural["channels"]
    paths = structural["paths"]

    result: Dict[str, Any] = {
        "systemic_stress": channels["systemic_stress"],
        "channels": {
            key: channels[key]
            for key in ("liquidity", "equity", "debt", "portfolio")
        },
        "interventions": shock,
        "allocation": allocation,
        "structural_model": {
            "method": "linear structural causal model",
            "intervention_operator": "do(X=x)",
            "node_values": scm["node_values"],
            "edge_contributions": scm["edge_contributions"],
        },
        "explanation": {
            "paths": paths,
            "primary_path": paths[0]["path"] if paths else [],
            "statement": (
                "Effects are propagated through directed structural edges; "
                "this is an intrinsic causal-path explanation, not post-hoc "
                "feature attribution."
            ),
        },
        "validation": {
            "allocation": allocation_check,
            "shocks": shock_check,
            "graph_errors": validate_graph(DEFAULT_NODES, DEFAULT_EDGES),
        },
        "research_status": {
            "notears": "module_available",
            "dynamic_discovery": "lagged_research_baseline_available",
            "temporal_gnn": "architecture_stage",
            "gfnets": "interface_ready_not_trained",
            "risk_calibration": calibration.get("status", "unknown"),
        },
        "risk_calibration": {
            "version": calibration.get("version"),
            "status": calibration.get("status"),
            "provenance": calibration.get("provenance"),
            "validation": calibration.get("validation", {}),
        },
        "assumptions": (
            "Structural coefficients are explicit research parameters loaded "
            "from a versioned calibration configuration. Scenario outputs are "
            "not forecasts or identified causal effects."
        ),
    }
    if include_tail_scenarios:
        tail = generate_tail_scenarios(
            shock,
            correlation=tail_correlation,
            distribution=tail_distribution,
            degrees_of_freedom=tail_degrees_of_freedom,
        )
        result["tail_scenarios"] = tail
        result["tail_evaluation"] = _evaluate_tail_scenarios(
            tail, allocation, calibration
        )
    return result


def graph_snapshot() -> Dict[str, Any]:
    graph = graph_payload()
    graph.update(
        {
            "engine": "finai-causal-risk-v0.3",
            "semantics": "directed structural graph for counterfactual propagation",
            "learned_components_status": {
                "notears_linear": "implemented",
                "dynamic_lagged_discovery": "implemented_research_baseline",
                "tgat": "architecture_stage",
                "kg_embeddings": "research_prototype_available",
                "gfnets": "research_prototype_available",
            },
            "graph_validation": validate_graph(DEFAULT_NODES, DEFAULT_EDGES),
            "risk_calibration": {
                "config_version": load_risk_calibration().get("version"),
                "status": load_risk_calibration().get("status"),
            },
        }
    )
    return graph
