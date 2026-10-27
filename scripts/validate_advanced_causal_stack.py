"""Reproducible, synthetic-only smoke validation for FinAI's advanced causal stack.

Run from the repository root:
    python scripts/validate_advanced_causal_stack.py

This is an engineering smoke check, not evidence of causal identification or
market-prediction performance. It deliberately uses seeded synthetic data.
"""
from __future__ import annotations

import json
import platform
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def _record(name: str, fn) -> dict[str, Any]:
    started = time.perf_counter()
    try:
        payload = fn()
        return {
            "name": name,
            "status": "PASS",
            "elapsed_seconds": round(time.perf_counter() - started, 6),
            "result": payload,
        }
    except Exception as exc:  # report every check; do not hide partial failures
        return {
            "name": name,
            "status": "FAIL",
            "elapsed_seconds": round(time.perf_counter() - started, 6),
            "error_type": type(exc).__name__,
            "error": str(exc),
        }


def _calibration() -> dict[str, Any]:
    from causal_risk.risk_calibration import calibrate_risk_target

    rng = np.random.default_rng(20261027)
    x = rng.normal(size=(100, 3))
    y = 0.5 * x[:, 0] - 0.2 * x[:, 1] + rng.normal(scale=0.2, size=100)
    result = calibrate_risk_target(x, y, ["rates", "credit", "oil"], alpha=1.0)
    if result.get("status") != "EMPIRICAL_RISK_CALIBRATION_READY":
        raise AssertionError(f"unexpected calibration status: {result.get('status')}")
    if result.get("chronological_split") is not True:
        raise AssertionError("calibration must report chronological holdout")
    return {
        "status": result.get("status"),
        "train_samples": result.get("train_samples"),
        "test_samples": result.get("test_samples"),
        "chronological_split": result.get("chronological_split"),
    }


def _causal_pipeline() -> dict[str, Any]:
    from causal_risk.pipeline import run_causal_research_pipeline

    rng = np.random.default_rng(20261028)
    x = rng.normal(size=(100, 3))
    x[:, 1] += 0.5 * x[:, 0]
    result = run_causal_research_pipeline(
        x,
        ["rates", "credit", "oil"],
        windows=2,
        bootstrap_draws=20,
        block_size=5,
        lags=1,
    )
    if result.get("status") != "FINAI_CAUSAL_RESEARCH_PIPELINE_READY":
        raise AssertionError(f"unexpected pipeline status: {result.get('status')}")
    return {
        "status": result.get("status"),
        "discovery_status": result.get("discovery", {}).get("consensus", {}).get("status"),
        "regime_summary_present": "regime_summary" in result,
        "evidence_class": "seeded_synthetic",
    }


def _temporal_gnn() -> dict[str, Any]:
    from causal_risk.temporal_gnn import build_temporal_edges, train_temporal_risk_model

    features = [[0.1, 0.2], [0.2, 0.1], [0.4, 0.3], [0.6, 0.4]]
    target = [0.1, 0.2, 0.5, 0.7]
    edges = build_temporal_edges([0, 1, 0], [1, 2, 3], [1.0, 1.0, 2.0])
    result = train_temporal_risk_model(
        features, target, edges, hidden_features=8, heads=2, epochs=3, seed=3
    )
    if result.get("status") != "TGAT_RESEARCH_TRAINED":
        raise AssertionError(f"unexpected temporal GNN status: {result.get('status')}")
    if not np.isfinite(float(result.get("train_mae", np.nan))):
        raise AssertionError("temporal GNN produced non-finite train MAE")
    return {
        "status": result.get("status"),
        "train_mae": float(result["train_mae"]),
        "evaluation_scope": "smoke_only_no_market_claim",
    }


def _gflownet() -> dict[str, Any]:
    from causal_risk.gfnets import GFlowConfig, GFlowNetTailGenerator

    generator = GFlowNetTailGenerator(
        2, GFlowConfig(hidden_dim=16, epochs=3, seed=5, device="cpu")
    )
    trained = generator.train()
    if trained.get("status") != "GFLOWNET_RESEARCH_TRAINED":
        raise AssertionError(f"unexpected GFlowNet status: {trained.get('status')}")
    sampled = generator.sample({"rates": 75, "oil": 50}, draws=8, seed=6)
    if sampled.get("status") != "GFLOWNET_SAMPLES_READY":
        raise AssertionError(f"unexpected sample status: {sampled.get('status')}")
    if len(sampled.get("scenarios", [])) != 8:
        raise AssertionError("expected exactly 8 scenarios")
    return {
        "training_status": trained.get("status"),
        "sampling_status": sampled.get("status"),
        "scenario_count": len(sampled["scenarios"]),
        "evaluation_scope": "synthetic_research_prototype",
    }


def _tail_sampler() -> dict[str, Any]:
    from causal_risk.tail_scenarios import generate_tail_scenarios

    shock = {"rates": 75, "oil": 50}
    kwargs = {
        "draws": 32,
        "seed": 12,
        "correlation": [[1.0, 0.65], [0.65, 1.0]],
        "distribution": "student_t_copula",
        "degrees_of_freedom": 5,
    }
    first = generate_tail_scenarios(shock, **kwargs)
    second = generate_tail_scenarios(shock, **kwargs)
    if first != second:
        raise AssertionError("tail sampler is not reproducible for a fixed seed")
    if first.get("distribution") != "student_t_copula":
        raise AssertionError("requested dependence distribution was not selected")
    return {
        "status": "PASS",
        "distribution": first.get("distribution"),
        "dependence_model": first.get("dependence_model"),
        "draws": len(first.get("scenarios", [])),
        "fixed_seed_reproducible": True,
    }


def main() -> int:
    checks = [
        _record("risk_calibration_chronological_holdout", _calibration),
        _record("causal_research_pipeline", _causal_pipeline),
        _record("temporal_gnn_training_smoke", _temporal_gnn),
        _record("gflownet_train_and_sample_smoke", _gflownet),
        _record("student_t_copula_reproducibility", _tail_sampler),
    ]
    passed = sum(item["status"] == "PASS" for item in checks)
    report = {
        "report_type": "FINAI_ADVANCED_CAUSAL_STACK_SMOKE",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "python": platform.python_version(),
        "numpy": np.__version__,
        "seeded_synthetic_data_only": True,
        "causal_identification_established": False,
        "market_prediction_validated": False,
        "production_eligible": False,
        "summary": {"passed": passed, "failed": len(checks) - passed, "total": len(checks)},
        "checks": checks,
    }
    print(json.dumps(report, indent=2, sort_keys=True, default=str))
    return 0 if passed == len(checks) else 1


if __name__ == "__main__":
    raise SystemExit(main())
