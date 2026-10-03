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

    nodes = ["rates", "credit", "liquidity", "equity", "portfolio"]
    edges = [
        {"source": "rates", "target": "credit", "weight": 0.7},
        {"source": "credit", "target": "liquidity", "weight": 0.8},
        {"source": "liquidity", "target": "equity", "weight": 0.9},
        {"source": "equity", "target": "portfolio", "weight": 0.8},
    ]
    bounds = {node: (-100.0, 100.0) for node in nodes}

    result = benchmark_patent_mechanism_variants(
        nodes,
        edges,
        ["credit", "rates"],
        {"credit": 10.0, "rates": 10.0},
        [-2.0, -1.0, 1.0, 2.0],
        bounds,
        target_node="portfolio",
        target_interval=(5.0, 9.0),
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
