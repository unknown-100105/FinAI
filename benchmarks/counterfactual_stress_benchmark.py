"""Seeded stress benchmark for counterfactual interval-screening safety.

Each case constructs a bounded linear DAG, samples a concrete feasible world
under an intervention, and asks the interval screen to retain that known-feasible
action. This checks a safety property across varied graph shapes; it is not
real-market validation or a proof of universal soundness.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import random
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from finance_engine.counterfactual_screening import (
    BoundedLinearDAG,
    CounterfactualAction,
    Interval,
    LinearNode,
)


SEED = 20261015
CASE_COUNT = 500
COEFFICIENTS = (-1.0, -0.5, 0.5, 1.0)
INTERCEPTS = (-0.5, 0.0, 0.5)
DOMAIN = Interval(-1_000_000.0, 1_000_000.0)


def run_case(case_index: int, rng: random.Random) -> dict:
    count = rng.randint(3, 9)
    names = [f"v{i}" for i in range(count)]
    nodes = []
    edge_count = 0
    negative_edge_count = 0

    for index, name in enumerate(names):
        parents = {
            names[parent_index]: rng.choice(COEFFICIENTS)
            for parent_index in range(index)
            if rng.random() < 0.35
        }
        edge_count += len(parents)
        negative_edge_count += sum(weight < 0 for weight in parents.values())
        nodes.append(
            LinearNode(
                name=name,
                domain=DOMAIN,
                parents=parents,
                intercept=rng.choice(INTERCEPTS),
                noise=Interval(-0.25, 0.25),
            )
        )

    model = BoundedLinearDAG(nodes)
    action_node = names[rng.randrange(count - 1)]
    intervention_value = rng.uniform(-2.0, 2.0)
    action = CounterfactualAction(
        f"stress_{case_index}",
        {action_node: Interval(intervention_value, intervention_value)},
    )

    # Build one concrete world that satisfies the intervention and structural
    # equations. Its target value is therefore a known-feasible witness.
    world_rng = random.Random(SEED + 100_003 + case_index)
    values: dict[str, float] = {}
    for name in model.order:
        node = model.nodes[name]
        if name == action_node:
            value = intervention_value
        else:
            value = node.intercept + world_rng.uniform(node.noise.low, node.noise.high)
            value += sum(weight * values[parent] for parent, weight in node.parents.items())
        if not node.domain.low <= value <= node.domain.high:
            raise AssertionError(f"Generated witness outside domain in case {case_index}: {name}={value}")
        values[name] = value

    target = names[-1]
    target_value = values[target]
    epsilon = 1e-6 * max(1.0, abs(target_value))
    target_band = Interval(target_value - epsilon, target_value + epsilon)
    certificate = model.screen_actions(target, target_band, [action])[0]
    retained = certificate.status == "RETAIN"

    return {
        "case": case_index,
        "node_count": count,
        "edge_count": edge_count,
        "negative_edge_count": negative_edge_count,
        "action_node": action_node,
        "target": target,
        "known_feasible_target_value": target_value,
        "certificate_status": certificate.status,
        "certificate_reason": certificate.reason,
        "known_feasible_action_retained": retained,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=None)
    parser.add_argument("--cases", type=int, default=CASE_COUNT)
    args = parser.parse_args()
    if args.cases < 1:
        parser.error("--cases must be at least 1")

    rng = random.Random(SEED)
    records = [run_case(index, rng) for index in range(args.cases)]
    false_prunes = [record for record in records if not record["known_feasible_action_retained"]]
    report = {
        "benchmark": "seeded_known_feasible_counterfactual_stress",
        "seed": SEED,
        "cases": args.cases,
        "passed_cases": args.cases - len(false_prunes),
        "known_feasible_false_prunes": len(false_prunes),
        "false_prune_rate": len(false_prunes) / args.cases,
        "total_edges": sum(record["edge_count"] for record in records),
        "negative_edges": sum(record["negative_edge_count"] for record in records),
        "max_nodes": max(record["node_count"] for record in records),
        "all_known_feasible_actions_retained": not false_prunes,
        "records": records,
        "research_boundary": (
            "Seeded synthetic safety stress test only; not real-market validation, "
            "universal soundness proof, patent novelty evidence, or production performance."
        ),
    }
    payload = json.dumps(report, indent=2, sort_keys=True)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(payload + "\n", encoding="utf-8")
    print(json.dumps({key: value for key, value in report.items() if key != "records"}, indent=2))
    if false_prunes:
        print(json.dumps({"false_prune_examples": false_prunes[:5]}, indent=2))
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
