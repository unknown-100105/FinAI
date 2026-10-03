"""Run the deterministic patent-mechanism research benchmark."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from causal_risk.patent_benchmark import benchmark_patent_mechanism_variants


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=None)
    args = parser.parse_args()

    nodes = ["rates", "credit", "portfolio"]
    edges = [
        {"source": "rates", "target": "portfolio", "weight": 0.8},
        {"source": "credit", "target": "portfolio", "weight": 0.1},
    ]
    bounds = {"rates": (-100.0, 100.0), "credit": (0.0, 20.0), "portfolio": (-100.0, 100.0)}

    result = benchmark_patent_mechanism_variants(
        nodes,
        edges,
        ["rates", "credit"],
        {"rates": 10.0, "credit": 10.0},
        [-1.0, -0.5, 0.5, 1.0],
        bounds,
        target_node="portfolio",
        target_interval=(8.0, 12.0),
        prefix_depth=1,
        scale=0.35,
    )
    payload = json.dumps(result, indent=2, sort_keys=True)

    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(payload + "\n", encoding="utf-8")
    print(payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
