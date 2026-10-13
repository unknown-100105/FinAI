"""Reproducible synthetic benchmark for FinAI counterfactual screening.

Engineering smoke benchmark only; this is not financial validation or evidence
of patentability. Uses a synthetic bounded DAG and a fixed-seed sampling oracle.
"""
from __future__ import annotations

import json
from pathlib import Path
import random
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from finance_engine.counterfactual_screening import (
    BoundedLinearDAG, CounterfactualAction, Interval, LinearNode, benchmark_screening,
)


def build_synthetic_model() -> BoundedLinearDAG:
    return BoundedLinearDAG([
        LinearNode("rate_shock", Interval(-5, 5)),
        LinearNode("funding_spread", Interval(-10, 10),
                   parents={"rate_shock": 1.5}, intercept=1.0,
                   noise=Interval(-0.5, 0.5)),
        LinearNode("default_rate", Interval(-25, 25),
                   parents={"funding_spread": 2.0}, noise=Interval(-1.0, 1.0)),
        LinearNode("portfolio_loss", Interval(-20, 20),
                   parents={"default_rate": 0.8}, intercept=2.0,
                   noise=Interval(-0.5, 0.5)),
    ])


def make_actions() -> list[CounterfactualAction]:
    ranges = [(-5, -4), (-3, -2), (-1, 0), (0.5, 1),
              (1.5, 2), (2, 2.5), (3, 3.5), (4, 5)]
    return [
        CounterfactualAction(f"rate_shock_{i}", {"rate_shock": Interval(low, high)})
        for i, (low, high) in enumerate(ranges)
    ]


def sampled_feasibility_oracle(model, target: str, target_band: Interval, trials: int = 5000):
    def evaluate(action: CounterfactualAction) -> bool:
        seed = 20261013 + sum((i + 1) * ord(char) for i, char in enumerate(action.action_id))
        rng = random.Random(seed)
        for _ in range(trials):
            values, valid = {}, True
            for name in model.order:
                node = model.nodes[name]
                if name in action.interventions:
                    chosen = action.interventions[name].intersection(node.domain)
                    if chosen is None:
                        valid = False
                        break
                    value = rng.uniform(chosen.low, chosen.high)
                else:
                    value = node.intercept + rng.uniform(node.noise.low, node.noise.high)
                    value += sum(coef * values[parent] for parent, coef in node.parents.items())
                if value < node.domain.low or value > node.domain.high:
                    valid = False
                    break
                values[name] = value
            if valid and target_band.low <= values[target] <= target_band.high:
                return True
        return False
    return evaluate


def main() -> None:
    model = build_synthetic_model()
    target, target_band = "portfolio_loss", Interval(10, 15)
    report = benchmark_screening(
        model, target, target_band, make_actions(),
        sampled_feasibility_oracle(model, target, target_band),
    )
    output_path = ROOT / "benchmarks" / "counterfactual_screening_benchmark.json"
    output_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in report.items() if k != "certificates"}, indent=2))
    print(f"\nFull certificates written to: {output_path}")
    if not report["all_exhaustive_feasible_actions_retained"]:
        raise SystemExit("FAIL: screening masked at least one oracle-feasible action")


if __name__ == "__main__":
    main()
