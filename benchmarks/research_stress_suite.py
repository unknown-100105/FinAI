"""Expanded deterministic stress suite for FinAI's research-only pruning mechanisms.

This suite checks finite-action correctness across multiple target bands and scales.
It does not validate real-market performance, causal identification, or patent novelty.
"""
from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from causal_risk.patent_benchmark import benchmark_patent_mechanism_variants


def run_suite() -> dict:
    nodes = ["rates", "credit", "portfolio"]
    edges = [
        {"source": "rates", "target": "portfolio", "weight": 0.8},
        {"source": "credit", "target": "portfolio", "weight": 0.1},
    ]
    bounds = {
        "rates": (-100.0, 100.0),
        "credit": (0.0, 20.0),
        "portfolio": (-100.0, 100.0),
    }
    scenarios = [
        {"name": "baseline", "target_interval": (8.0, 12.0), "scale": 0.35},
        {"name": "narrow_band", "target_interval": (10.0, 11.0), "scale": 0.35},
        {"name": "lower_tail", "target_interval": (-15.0, -8.0), "scale": 0.35},
        {"name": "upper_tail", "target_interval": (20.0, 30.0), "scale": 0.35},
        {"name": "wide_band", "target_interval": (-25.0, 25.0), "scale": 0.2},
        {"name": "wide_scale", "target_interval": (8.0, 12.0), "scale": 0.5},
        {"name": "near_zero", "target_interval": (-1.0, 1.0), "scale": 0.5},
        {"name": "far_upper", "target_interval": (40.0, 50.0), "scale": 0.5},
    ]
    results = []
    failures = []
    for scenario in scenarios:
        result = benchmark_patent_mechanism_variants(
            nodes,
            edges,
            ["rates", "credit"],
            {"rates": 10.0, "credit": 10.0},
            [-1.0, -0.5, 0.5, 1.0],
            bounds,
            target_node="portfolio",
            target_interval=scenario["target_interval"],
            prefix_depth=1,
            scale=scenario["scale"],
        )
        row = {
            "name": scenario["name"],
            "target_interval": list(scenario["target_interval"]),
            "scale": scenario["scale"],
            "candidate_prefixes": result["baseline"]["candidate_prefixes"],
            "exact_completion_evaluations": result["baseline"]["exact_completion_evaluations"],
            "forward_false_prunes": result["forward_certificate"]["false_prunes"],
            "bidirectional_false_prunes": result["bidirectional_necessary_interval"]["false_prunes"],
            "forward_recall": result["forward_certificate"]["high_risk_prefix_recall"],
            "bidirectional_recall": result["bidirectional_necessary_interval"]["high_risk_prefix_recall"],
            "incremental_exact_match_rate": result["incremental_propagation"]["exact_match_rate"],
        }
        results.append(row)
        if result["correctness"]["forward_no_false_prune"] is not True:
            failures.append(f"{scenario['name']}: forward screen false-pruned a feasible prefix")
        if result["correctness"]["bidirectional_no_false_prune"] is not True:
            failures.append(f"{scenario['name']}: bidirectional screen false-pruned a feasible prefix")
        if result["incremental_propagation"]["exact_match_rate"] != 1.0:
            failures.append(f"{scenario['name']}: incremental propagation differed from full propagation")

    return {
        "schema_version": "1.0",
        "benchmark": "finai_research_pruning_stress_suite",
        "status": "passed" if not failures else "failed",
        "scenario_count": len(scenarios),
        "passed_scenarios": len(scenarios) - len(failures),
        "failure_count": len(failures),
        "failures": failures,
        "scenarios": results,
        "research_boundary": (
            "Deterministic finite-action synthetic stress tests only; not real-market validation, "
            "causal identification evidence, profitability evidence, or proof of patent novelty."
        ),
    }


def main() -> int:
    report = run_suite()
    output = ROOT / "benchmarks" / "research_stress_report.json"
    output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True))
    print(f"Full report: {output}")
    return 0 if report["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
