"""Seeded safety benchmark for SwarmTrade's deterministic risk planner.

This is synthetic implementation testing only. It measures safety invariants and
repeatability, not prediction quality, alpha, profitability, or real-market fitness.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import random
import sys
from collections import Counter
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from swarmtrade.engine import MAX_LOGICAL_AGENTS, build_swarm_plan

SEED = 20261024
CASE_COUNT = 500


def _base_request(index: int, rng: random.Random) -> dict[str, Any]:
    direction = "long" if index % 2 == 0 else "short"
    sign = 1 if direction == "long" else -1
    asset_class = ("equity", "crypto", "option", "future", "forex")[(index + index // 10) % 5]
    if asset_class == "forex":
        entry, stop, target, capital, multiplier = (
            (1.1, 1.095, 1.12, 500_000.0, 100_000.0) if direction == "long"
            else (1.1, 1.105, 1.08, 500_000.0, 100_000.0)
        )
    else:
        entry, stop, target, capital, multiplier = (
            (100.0, 95.0, 112.0, 100_000.0, 50.0 if asset_class == "future" else 1.0)
            if direction == "long"
            else (100.0, 105.0, 88.0, 100_000.0, 50.0 if asset_class == "future" else 1.0)
        )
    jitter = rng.uniform(0.0, 0.05)
    request: dict[str, Any] = {
        "symbol": f"BENCH{index:04d}",
        "asset_class": asset_class,
        "side": "auto",
        "entry_price": entry,
        "stop_price": stop,
        "target_price": target,
        "capital": capital,
        "risk_pct": rng.choice((0.25, 0.5, 0.75, 2.0)),
        "open_position_risk_pct": rng.choice((0.0, 0.5, 1.0, 2.5)),
        "current_daily_loss_pct": rng.choice((0.0, 0.2, 0.8, 1.2)),
        "max_daily_loss_pct": 2.0,
        "max_leverage": 5.0,
        "margin_rate": 0.1,
        "multiplier": multiplier,
        "unit_step": 1.0,
        "fee_bps": 2.0,
        "slippage_bps": 2.0,
        "min_reward_risk": 1.0,
        "agent_count": MAX_LOGICAL_AGENTS,
        "signals": {
            "trend": sign * (0.8 - jitter),
            "momentum": sign * (0.75 - jitter),
            "mean_reversion": sign * 0.1,
            "breakout": sign * (0.9 - jitter),
            "sentiment": sign * 0.5,
        },
    }
    if asset_class == "option":
        request["max_loss_per_unit"] = 6.0
    if asset_class == "future":
        request.update({"tick_size": 0.25, "tick_value": 12.5, "margin_per_unit": 5_000.0})
    if asset_class == "forex":
        request.update({
            "pip_size": 0.0001,
            "pip_value_per_unit": 10.0,
            "margin_per_unit": 2_000.0,
        })
    return request


def _apply_control_case(request: dict[str, Any], control: int) -> bool:
    """Add a known fail-closed case; return whether blocking is mandatory."""
    if control == 5:
        request["current_daily_loss_pct"] = 2.0
        return True
    if control == 6:
        request["stop_price"] = None
        return True
    if control == 7:
        if request["side"] == "auto" and request["signals"]["trend"] >= 0:
            request["stop_price"] = request["entry_price"] + 1
        else:
            request["stop_price"] = request["entry_price"] - 1
        return True
    if control == 8:
        request["asset_class"] = "option"
        request.pop("max_loss_per_unit", None)
        return True
    if control == 9:
        request["side"] = "short" if request["signals"]["trend"] > 0 else "long"
        return True
    return False


def run_benchmark(case_count: int = CASE_COUNT) -> dict[str, Any]:
    if case_count < 1:
        raise ValueError("case_count must be at least 1")
    rng = random.Random(SEED)
    status_counts: Counter[str] = Counter()
    asset_counts: Counter[str] = Counter()
    approved_counts: Counter[str] = Counter()
    determinism_failures = 0
    guardrail_violations = 0
    expected_control_rejections_missed = 0
    passed_cases = 0
    samples: list[dict[str, Any]] = []

    for index in range(case_count):
        request = _base_request(index, rng)
        must_block = _apply_control_case(request, index % 10)
        asset_counts[request["asset_class"]] += 1
        first = build_swarm_plan(request)
        second = build_swarm_plan(request)
        repeatable = first == second
        if not repeatable:
            determinism_failures += 1

        status_counts[first["status"]] += 1
        if first["status"] == "APPROVED_FOR_SIMULATION":
            approved_counts[request["asset_class"]] += 1
        control_gate_missed = must_block and first["status"] == "APPROVED_FOR_SIMULATION"
        if control_gate_missed:
            expected_control_rejections_missed += 1

        safe = (
            first["execution"]["order_submitted"] is False
            and first["execution"]["fill_claimed"] is False
            and first["agent_count"] <= MAX_LOGICAL_AGENTS
        )
        if first["status"] == "APPROVED_FOR_SIMULATION":
            risk = first["risk"]
            safe = safe and risk["effective_risk_pct"] <= 1.0 + 1e-9
            safe = safe and request["open_position_risk_pct"] + risk["effective_risk_pct"] <= 3.0 + 1e-8
            safe = safe and risk["current_daily_loss_pct"] < risk["daily_loss_limit_pct"]
            safe = safe and risk["estimated_total_risk"] <= risk["risk_budget"] + 1e-7
            safe = safe and risk["effective_leverage"] <= request["max_leverage"] + 1e-8
            safe = safe and first["sizing"]["quantity"] > 0
        if not safe:
            guardrail_violations += 1
        case_passed = repeatable and safe and not control_gate_missed
        if case_passed:
            passed_cases += 1
        elif len(samples) < 10:
            samples.append({
                "case": index,
                "reason": "guardrail_violation" if not safe else "known_control_not_rejected" if control_gate_missed else "non_deterministic_result",
                "plan": first,
            })

    failures = case_count - passed_cases
    return {
        "benchmark": "finai_swarmtrade_deterministic_safety",
        "seed": SEED,
        "cases": case_count,
        "logical_agents_per_case": MAX_LOGICAL_AGENTS,
        "passed_cases": passed_cases,
        "status_counts": dict(sorted(status_counts.items())),
        "asset_class_counts": dict(sorted(asset_counts.items())),
        "approved_simulation_plans_by_asset_class": dict(sorted(approved_counts.items())),
        "determinism_failures": determinism_failures,
        "guardrail_violations": guardrail_violations,
        "expected_control_rejections_missed": expected_control_rejections_missed,
        "failure_count": failures,
        "failure_samples": samples,
        "research_boundary": (
            "Synthetic deterministic safety benchmark only; not evidence of forecasting accuracy, "
            "profitability, risk-model calibration, execution quality, or live-market validation."
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=None)
    parser.add_argument("--cases", type=int, default=CASE_COUNT)
    args = parser.parse_args()
    try:
        report = run_benchmark(args.cases)
    except ValueError as exc:
        parser.error(str(exc))
    serialized = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(serialized, encoding="utf-8")
    print(serialized, end="")
    return 0 if report["failure_count"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
