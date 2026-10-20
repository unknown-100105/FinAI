"""Evidence-gated and feasibility-certified counterfactual stress-test pipeline."""
from __future__ import annotations

from typing import Any, Mapping, Sequence

import numpy as np

from causal_risk.engine import ALLOWED_SHOCKS, run_counterfactual
from causal_risk.evidence_gate import evaluate_evidence_gate
from causal_risk.feasibility_pruning import evaluate_prefix_feasibility
from causal_risk.schema import DEFAULT_EDGES, DEFAULT_NODES
from causal_risk.tail_scenarios import generate_tail_scenarios


def _graph_edges() -> list[dict[str, Any]]:
    return [
        {
            "source": edge.source,
            "target": edge.target,
            "weight": edge.weight,
            "lag": edge.lag,
        }
        for edge in DEFAULT_EDGES
    ]


def _default_bounds() -> dict[str, tuple[float, float]]:
    return {node.node_id: (-100.0, 100.0) for node in DEFAULT_NODES}


def _certify_shock(
    shock: Mapping[str, float],
    *,
    node_bounds: Mapping[str, Sequence[float]],
    target_interval: Sequence[float],
) -> dict[str, Any]:
    try:
        values = {str(key): float(value) for key, value in shock.items()}
        if set(values) - set(ALLOWED_SHOCKS):
            raise ValueError("unknown shock factor")
        certificate = evaluate_prefix_feasibility(
            [node.node_id for node in DEFAULT_NODES],
            _graph_edges(),
            values,
            node_bounds,
            target_node="portfolio",
            target_interval=target_interval,
        )
        return {
            "passed": not certificate.hard_infeasible and not certificate.support_infeasible,
            "certificate": certificate.as_dict(),
        }
    except (TypeError, ValueError, OverflowError) as exc:
        return {
            "passed": False,
            "certificate": {
                "hard_infeasible": True,
                "reason": str(exc),
                "certificate_type": "input_validation",
            },
        }


def run_evidence_gated_stress_test(
    shock: Mapping[str, float],
    allocation: Mapping[str, float],
    evidence: Sequence[Mapping[str, Any]],
    *,
    as_of: str | None = None,
    minimum_confidence: float = 0.6,
    max_age_days: int = 180,
    include_tail_scenarios: bool = True,
    tail_draws: int = 64,
    tail_seed: int = 42,
    tail_distribution: str = "student_t_copula",
    tail_degrees_of_freedom: float = 5.0,
    node_bounds: Mapping[str, Sequence[float]] | None = None,
    target_interval: Sequence[float] = (-100.0, 100.0),
) -> dict[str, Any]:
    """Run only after evidence coverage passes; reject infeasible tail scenarios.

    Bounds and the target interval are explicit model assumptions. The default
    bounds are broad engineering guards, not empirically calibrated market limits.
    """
    shock_values = {str(key): float(value) for key, value in shock.items()}
    allocation_values = {str(key): float(value) for key, value in allocation.items()}
    gate = evaluate_evidence_gate(
        shock_values,
        evidence,
        as_of=as_of,
        minimum_confidence=minimum_confidence,
        max_age_days=max_age_days,
    )
    if not gate["passed"]:
        return {
            "status": "EVIDENCE_GATE_REJECTED",
            "evidence_gate": gate,
            "feasibility": {"status": "NOT_RUN"},
            "scenario_results": [],
            "summary": {
                "accepted_scenarios": 0,
                "rejected_scenarios": 0,
                "reason": "required evidence is missing, stale, low-confidence, or invalid",
            },
        }

    # Validate and calculate the requested base intervention with the existing
    # deterministic engine; do not replace it with generated text.
    base_result = run_counterfactual(
        shock_values,
        allocation_values,
        include_tail_scenarios=False,
    )
    bounds = dict(node_bounds or _default_bounds())
    base_certificate = _certify_shock(
        shock_values,
        node_bounds=bounds,
        target_interval=target_interval,
    )
    if not base_certificate["passed"]:
        return {
            "status": "FEASIBILITY_REJECTED",
            "evidence_gate": gate,
            "base_result": base_result,
            "feasibility": base_certificate,
            "scenario_results": [],
            "summary": {
                "accepted_scenarios": 0,
                "rejected_scenarios": 1,
                "reason": "base intervention failed declared feasibility constraints",
            },
        }

    evaluated: list[dict[str, Any]] = [{
        "scenario_id": "base",
        "status": "accepted",
        "shock": shock_values,
        "feasibility": base_certificate,
        "portfolio_impact": base_result["channels"]["portfolio"],
        "systemic_stress": base_result["systemic_stress"],
        "explanation": base_result["explanation"],
    }]
    rejected: list[dict[str, Any]] = []

    if include_tail_scenarios:
        generated = generate_tail_scenarios(
            shock_values,
            draws=max(8, min(int(tail_draws), 5000)),
            seed=int(tail_seed),
            distribution=tail_distribution,
            degrees_of_freedom=tail_degrees_of_freedom,
        )
        for item in generated["scenarios"]:
            scenario_shock = {
                str(key): float(value)
                for key, value in item["shock"].items()
            }
            certificate = _certify_shock(
                scenario_shock,
                node_bounds=bounds,
                target_interval=target_interval,
            )
            if not certificate["passed"]:
                rejected.append({
                    "scenario_id": item["scenario_id"],
                    "shock": scenario_shock,
                    "reason": certificate["certificate"].get("reason"),
                    "feasibility": certificate,
                })
                continue
            try:
                result = run_counterfactual(
                    scenario_shock,
                    allocation_values,
                    include_tail_scenarios=False,
                )
            except (TypeError, ValueError, OverflowError) as exc:
                rejected.append({
                    "scenario_id": item["scenario_id"],
                    "shock": scenario_shock,
                    "reason": str(exc),
                    "feasibility": certificate,
                })
                continue
            evaluated.append({
                "scenario_id": item["scenario_id"],
                "status": "accepted",
                "shock": scenario_shock,
                "tail_score": item.get("tail_score"),
                "feasibility": certificate,
                "portfolio_impact": result["channels"]["portfolio"],
                "systemic_stress": result["systemic_stress"],
                "explanation": result["explanation"],
            })

    impacts = np.asarray(
        [abs(float(item["portfolio_impact"])) for item in evaluated],
        dtype=float,
    )
    return {
        "status": "EVIDENCE_GATED_STRESS_TEST_COMPLETE",
        "evidence_gate": gate,
        "base_result": base_result,
        "feasibility": base_certificate,
        "generation": {
            "method": "seeded tail sampler plus hard feasibility certificate",
            "distribution": tail_distribution if include_tail_scenarios else None,
            "seed": int(tail_seed),
            "draws_requested": int(tail_draws) if include_tail_scenarios else 0,
            "gflownet_trained": False,
        },
        "scenario_results": evaluated,
        "rejected_scenarios": rejected,
        "summary": {
            "accepted_scenarios": len(evaluated),
            "rejected_scenarios": len(rejected),
            "feasibility_rejection_rate": (
                len(rejected) / (len(rejected) + len(evaluated) - 1)
                if len(rejected) + len(evaluated) > 1
                else 0.0
            ),
            "mean_absolute_portfolio_impact": round(float(np.mean(impacts)), 4),
            "p95_absolute_portfolio_impact": round(float(np.quantile(impacts, 0.95)), 4),
            "max_absolute_portfolio_impact": round(float(np.max(impacts)), 4),
            "realized_tail_coverage": None,
            "realized_tail_coverage_note": (
                "Requires chronological held-out realized outcomes; it is not inferred "
                "from simulated scenario impacts."
            ),
        },
        "assumptions": [
            "Evidence coverage verifies declared source, freshness, confidence and claim mapping; it does not prove causality.",
            "The graph is supplied by the configured research model and is not identified by this call.",
            "Feasibility certificates are conditional on the declared linear-DAG bounds and target interval.",
            "The default bounds are broad engineering guards and require domain calibration.",
        ],
    }
