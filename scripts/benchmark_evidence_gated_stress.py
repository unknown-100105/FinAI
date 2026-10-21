"""Reproducible smoke benchmark for evidence-gated counterfactual stress testing.

This uses synthetic evidence metadata and fixed shocks only to verify the
pipeline and emit comparable summary metrics. It is NOT empirical validation,
a financial forecast, or evidence of improved realized tail coverage.
Run from the repository root:
    python scripts/benchmark_evidence_gated_stress.py --draws 64 --seed 42
"""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from typing import Any

from causal_risk.engine import run_counterfactual
from causal_risk.evidence_gate import required_evidence_claims
from causal_risk.evidence_gated_stress import run_evidence_gated_stress_test
from causal_risk.tail_scenarios import generate_tail_scenarios


def synthetic_evidence(shock: dict[str, float], as_of: str) -> list[dict[str, Any]]:
    return [
        {
            "evidence_id": f"synthetic-{index:03d}",
            "source": "SYNTHETIC_SMOKE_FIXTURE_NOT_A_REAL_SOURCE",
            "observed_at": as_of,
            "confidence": 0.99,
            "supports": [claim],
        }
        for index, claim in enumerate(required_evidence_claims(shock))
    ]


def summarize(shocks: list[dict[str, float]], allocation: dict[str, float]) -> dict[str, Any]:
    impacts: list[float] = []
    rejected = 0
    for shock in shocks:
        try:
            result = run_counterfactual(shock, allocation)
            impacts.append(abs(float(result["channels"]["portfolio"])))
        except (ValueError, TypeError, KeyError):
            rejected += 1
    impacts.sort()
    p95 = impacts[min(len(impacts) - 1, int(0.95 * (len(impacts) - 1)))] if impacts else None
    return {
        "input_scenarios": len(shocks),
        "evaluated_scenarios": len(impacts),
        "invalid_or_infeasible_count": rejected,
        "invalid_or_infeasible_rate": rejected / len(shocks) if shocks else 0.0,
        "p95_absolute_portfolio_impact": p95,
        "max_absolute_portfolio_impact": max(impacts) if impacts else None,
        "realized_tail_coverage": None,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--draws", type=int, default=64)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()
    if not 8 <= args.draws <= 5000:
        parser.error("--draws must be between 8 and 5000")

    as_of = datetime.now(timezone.utc).isoformat()
    base_shock = {"rates": 35.0, "usd": 20.0, "oil": 15.0, "credit": 25.0}
    allocation = {"equity": 55.0, "debt": 30.0, "gold": 10.0, "cash": 5.0}
    evidence = synthetic_evidence(base_shock, as_of)

    unconstrained = generate_tail_scenarios(
        base_shock, draws=args.draws, seed=args.seed, distribution="student_t_copula"
    )
    unconstrained_shocks = [item["shock"] for item in unconstrained["scenarios"]]
    gated = run_evidence_gated_stress_test(
        base_shock,
        allocation,
        evidence,
        as_of=as_of,
        include_tail_scenarios=True,
        tail_draws=args.draws,
        tail_seed=args.seed,
        tail_distribution="student_t_copula",
    )
    conventional = [
        {"rates": 50.0, "usd": 10.0, "oil": 10.0, "credit": 30.0},
        {"rates": -25.0, "usd": 35.0, "oil": 40.0, "credit": 20.0},
        {"rates": 70.0, "usd": 20.0, "oil": 25.0, "credit": 45.0},
        {"rates": -40.0, "usd": -20.0, "oil": -30.0, "credit": 10.0},
    ]
    gated_impacts = [
        abs(float(item["portfolio_impact"]))
        for item in gated.get("scenario_results", [])
    ]
    output = {
        "benchmark": "finai-egfc-smoke-benchmark-v1",
        "status": gated["status"],
        "seed": args.seed,
        "draws": args.draws,
        "warning": (
            "Synthetic evidence fixture only. This smoke benchmark checks repeatability "
            "and pipeline wiring, not empirical superiority or realized tail coverage."
        ),
        "evidence_gated": {
            "status": gated["status"],
            "accepted_scenarios": gated.get("summary", {}).get("accepted_scenarios", 0),
            "rejected_scenarios": gated.get("summary", {}).get("rejected_scenarios", 0),
            "p95_absolute_portfolio_impact": gated.get("summary", {}).get("p95_absolute_portfolio_impact"),
            "max_absolute_portfolio_impact": gated.get("summary", {}).get("max_absolute_portfolio_impact"),
            "realized_tail_coverage": None,
        },
        "unconstrained_tail_generation": summarize(unconstrained_shocks, allocation),
        "conventional_deterministic_stress_suite": summarize(conventional, allocation),
        "interpretation": {
            "can_claim_empirical_improvement": False,
            "required_next_step": (
                "Replace synthetic evidence with timestamped licensed data, define a "
                "chronological holdout, and compare tail coverage/calibration against realized losses."
            ),
            "gated_accepted_scenario_count": len(gated_impacts),
        },
    }
    print(json.dumps(output, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
