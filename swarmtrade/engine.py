"""Deterministic logical-agent consensus and risk sizing for SwarmTrade.

This module deliberately produces a simulation plan only. It never submits orders,
connects to a broker, or claims that a simulated fill occurred.
"""
from __future__ import annotations

import math
from collections import Counter
from typing import Any, Mapping

MAX_LOGICAL_AGENTS = 500
ROLE_WEIGHTS: dict[str, dict[str, float]] = {
    "momentum": {"trend": 0.35, "momentum": 0.55, "sentiment": 0.10},
    "trend": {"trend": 0.60, "breakout": 0.25, "sentiment": 0.15},
    "mean_reversion": {"mean_reversion": 0.45, "trend": -0.25, "momentum": -0.30},
    "breakout": {"breakout": 0.50, "momentum": 0.30, "trend": 0.20},
    "sentiment": {"sentiment": 0.65, "trend": 0.20, "mean_reversion": 0.15},
}
SIGNAL_NAMES = frozenset({"trend", "momentum", "mean_reversion", "breakout", "sentiment"})


def _finite_number(value: Any, name: str, *, minimum: float | None = None,
                   maximum: float | None = None) -> float:
    if isinstance(value, bool):
        raise ValueError(f"{name} must be a finite number")
    try:
        result = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{name} must be a finite number") from exc
    if not math.isfinite(result):
        raise ValueError(f"{name} must be a finite number")
    if minimum is not None and result < minimum:
        raise ValueError(f"{name} must be at least {minimum}")
    if maximum is not None and result > maximum:
        raise ValueError(f"{name} must be at most {maximum}")
    return result


def _reject(reason: str, *, agent_count: int, votes: Mapping[str, int] | None = None,
            consensus_score: float = 0.0, direction: str = "flat") -> dict[str, Any]:
    return {
        "status": "REJECTED" if reason != "No directional consensus" else "NO_SIGNAL",
        "decision": "DO_NOT_TRADE",
        "direction": direction,
        "reason": reason,
        "agent_count": agent_count,
        "logical_agents_only": True,
        "consensus_score": round(consensus_score, 6),
        "votes": dict(votes or {"long": 0, "short": 0, "flat": agent_count}),
        "risk": None,
        "sizing": None,
        "execution": {"mode": "simulation_only", "order_submitted": False, "fill_claimed": False},
    }


def build_swarm_plan(request: Mapping[str, Any]) -> dict[str, Any]:
    """Return a repeatable agent consensus and risk-gated trade sizing proposal.

    Scores are directional features supplied by the caller, not a trained signal model.
    A 500-agent run is 500 logical votes on one process, not 500 concurrent workers.
    All prices, contract multipliers, margin assumptions, and fees must be provided or
    reviewed by the caller for the actual instrument and venue.
    """
    agent_count = int(request.get("agent_count", MAX_LOGICAL_AGENTS))
    if agent_count < 1 or agent_count > MAX_LOGICAL_AGENTS:
        raise ValueError(f"agent_count must be between 1 and {MAX_LOGICAL_AGENTS}")

    asset_class = str(request.get("asset_class", "equity")).strip().lower()
    if asset_class not in {"equity", "option", "future", "crypto", "forex"}:
        raise ValueError("asset_class must be equity, option, future, crypto, or forex")

    signals_raw = request.get("signals") or {}
    if not isinstance(signals_raw, Mapping):
        raise ValueError("signals must be an object")
    unknown_signals = set(signals_raw) - SIGNAL_NAMES
    if unknown_signals:
        raise ValueError(f"unsupported signal names: {', '.join(sorted(unknown_signals))}")
    signals = {name: _finite_number(signals_raw.get(name, 0), name, minimum=-1, maximum=1)
               for name in SIGNAL_NAMES}

    role_scores = {
        role: sum(signals[name] * weight for name, weight in weights.items())
        for role, weights in ROLE_WEIGHTS.items()
    }
    roles = tuple(ROLE_WEIGHTS)
    votes: Counter[str] = Counter()
    agent_scores: list[float] = []
    for index in range(agent_count):
        score = role_scores[roles[index % len(roles)]]
        agent_scores.append(score)
        votes["long" if score >= 0.10 else "short" if score <= -0.10 else "flat"] += 1
    for side in ("long", "short", "flat"):
        votes.setdefault(side, 0)

    consensus_score = sum(agent_scores) / agent_count
    dominant = "long" if votes["long"] > votes["short"] else "short" if votes["short"] > votes["long"] else "flat"
    directional_votes = max(votes["long"], votes["short"])
    confidence = directional_votes / agent_count
    if dominant == "flat" or abs(consensus_score) < 0.10 or confidence < 0.55:
        return _reject("No directional consensus", agent_count=agent_count, votes=votes,
                       consensus_score=consensus_score)

    requested_side = str(request.get("side", "auto")).strip().lower()
    if requested_side not in {"auto", "long", "short"}:
        raise ValueError("side must be auto, long, or short")
    if requested_side != "auto" and requested_side != dominant:
        return _reject("Requested side conflicts with logical-agent consensus",
                       agent_count=agent_count, votes=votes, consensus_score=consensus_score,
                       direction=dominant)

    symbol = str(request.get("symbol", "")).strip().upper()
    if not symbol:
        raise ValueError("symbol must not be empty")

    # Hard-coded ceilings are intentional: callers cannot configure the guardrails away.
    entry = _finite_number(request.get("entry_price"), "entry_price", minimum=1e-12)
    capital = _finite_number(request.get("capital"), "capital", minimum=1e-12)
    risk_pct = _finite_number(request.get("risk_pct", 0.5), "risk_pct", minimum=0.01, maximum=5.0)
    open_risk_pct = _finite_number(request.get("open_position_risk_pct", 0), "open_position_risk_pct", minimum=0, maximum=3.0)
    daily_loss_pct = _finite_number(request.get("current_daily_loss_pct", 0), "current_daily_loss_pct", minimum=0, maximum=20.0)
    max_daily_loss_pct = _finite_number(request.get("max_daily_loss_pct", 2.0), "max_daily_loss_pct", minimum=0.1, maximum=5.0)
    max_leverage = _finite_number(request.get("max_leverage", 1.0), "max_leverage", minimum=1.0, maximum=30.0)
    margin_rate = _finite_number(request.get("margin_rate", 1.0), "margin_rate", minimum=0.01, maximum=1.0)
    multiplier = _finite_number(request.get("multiplier", 1.0), "multiplier", minimum=1e-12)
    unit_step = _finite_number(request.get("unit_step", 1.0), "unit_step", minimum=1e-12)
    fee_bps = _finite_number(request.get("fee_bps", 5.0), "fee_bps", minimum=0, maximum=1000)
    slippage_bps = _finite_number(request.get("slippage_bps", 5.0), "slippage_bps", minimum=0, maximum=1000)
    stop_raw, target_raw = request.get("stop_price"), request.get("target_price")

    if daily_loss_pct >= max_daily_loss_pct:
        return _reject("Daily loss limit reached; entries are blocked", agent_count=agent_count,
                       votes=votes, consensus_score=consensus_score, direction=dominant)
    if stop_raw is None or target_raw is None:
        return _reject("A protective stop and profit target are required", agent_count=agent_count,
                       votes=votes, consensus_score=consensus_score, direction=dominant)
    stop = _finite_number(stop_raw, "stop_price", minimum=1e-12)
    target = _finite_number(target_raw, "target_price", minimum=1e-12)
    if dominant == "long" and not (stop < entry < target):
        return _reject("Long trade requires stop_price < entry_price < target_price",
                       agent_count=agent_count, votes=votes, consensus_score=consensus_score, direction=dominant)
    if dominant == "short" and not (target < entry < stop):
        return _reject("Short trade requires target_price < entry_price < stop_price",
                       agent_count=agent_count, votes=votes, consensus_score=consensus_score, direction=dominant)

    max_loss_raw = request.get("max_loss_per_unit")
    stop_risk_per_unit = abs(entry - stop) * multiplier
    margin_per_unit_override: float | None = None
    risk_model_details: dict[str, float | str] = {"model": "price_distance_times_multiplier"}

    if asset_class == "option":
        if max_loss_raw is None:
            return _reject("Options require a caller-supplied max_loss_per_unit per contract",
                           agent_count=agent_count, votes=votes, consensus_score=consensus_score, direction=dominant)
        max_loss = _finite_number(max_loss_raw, "max_loss_per_unit", minimum=1e-12)
        gross_risk_per_unit = max(stop_risk_per_unit, max_loss)
        risk_model_details = {"model": "conservative_option_max_loss", "max_loss_per_unit": max_loss}
    elif asset_class == "future":
        if any(request.get(name) is None for name in ("tick_size", "tick_value", "margin_per_unit")):
            return _reject("Futures require venue-verified tick_size, tick_value, and margin_per_unit",
                           agent_count=agent_count, votes=votes, consensus_score=consensus_score, direction=dominant)
        tick_size = _finite_number(request.get("tick_size"), "tick_size", minimum=1e-12)
        tick_value = _finite_number(request.get("tick_value"), "tick_value", minimum=1e-12)
        margin_per_unit_override = _finite_number(request.get("margin_per_unit"), "margin_per_unit", minimum=1e-12)
        gross_risk_per_unit = (abs(entry - stop) / tick_size) * tick_value
        risk_model_details = {"model": "futures_tick_value", "tick_size": tick_size,
                              "tick_value": tick_value, "margin_per_unit": margin_per_unit_override}
    elif asset_class == "forex":
        if any(request.get(name) is None for name in ("pip_size", "pip_value_per_unit", "margin_per_unit")):
            return _reject("Forex requires account-currency-verified pip_size, pip_value_per_unit, and margin_per_unit",
                           agent_count=agent_count, votes=votes, consensus_score=consensus_score, direction=dominant)
        pip_size = _finite_number(request.get("pip_size"), "pip_size", minimum=1e-12)
        pip_value = _finite_number(request.get("pip_value_per_unit"), "pip_value_per_unit", minimum=1e-12)
        margin_per_unit_override = _finite_number(request.get("margin_per_unit"), "margin_per_unit", minimum=1e-12)
        gross_risk_per_unit = (abs(entry - stop) / pip_size) * pip_value
        risk_model_details = {"model": "forex_pip_value", "pip_size": pip_size,
                              "pip_value_per_unit": pip_value, "margin_per_unit": margin_per_unit_override}
    else:
        gross_risk_per_unit = stop_risk_per_unit

    round_trip_cost_per_unit = entry * multiplier * (2 * (fee_bps + slippage_bps) / 10_000)
    risk_per_unit = gross_risk_per_unit + round_trip_cost_per_unit
    notional_per_unit = entry * multiplier
    if risk_per_unit <= 0 or not math.isfinite(risk_per_unit):
        return _reject("Computed risk per unit is invalid", agent_count=agent_count,
                       votes=votes, consensus_score=consensus_score, direction=dominant)

    # Maximum 1% risk per new trade and 3% combined open-position risk, irrespective
    # of caller input. Daily loss headroom is an additional independent constraint.
    risk_headroom_pct = max(0.0, 3.0 - open_risk_pct)
    daily_headroom_pct = max(0.0, max_daily_loss_pct - daily_loss_pct)
    effective_risk_pct = min(risk_pct, 1.0, risk_headroom_pct, daily_headroom_pct)
    risk_budget = capital * effective_risk_pct / 100.0
    if risk_budget <= 0:
        return _reject("No portfolio or daily-loss risk budget remains", agent_count=agent_count,
                       votes=votes, consensus_score=consensus_score, direction=dominant)

    risk_limited_units = risk_budget / risk_per_unit
    margin_required_per_unit = margin_per_unit_override if margin_per_unit_override is not None else notional_per_unit * margin_rate
    margin_limited_units = capital / margin_required_per_unit
    leverage_limited_units = (capital * max_leverage) / notional_per_unit
    raw_units = min(risk_limited_units, margin_limited_units, leverage_limited_units)
    quantity = math.floor((raw_units + 1e-12) / unit_step) * unit_step
    if quantity < unit_step:
        return _reject("Risk and margin limits permit less than one configured unit",
                       agent_count=agent_count, votes=votes, consensus_score=consensus_score, direction=dominant)

    gross_reward_per_unit = abs(target - entry) * multiplier
    net_reward_per_unit = gross_reward_per_unit - round_trip_cost_per_unit
    reward_risk = net_reward_per_unit / risk_per_unit if risk_per_unit > 0 else 0.0
    min_reward_risk = _finite_number(request.get("min_reward_risk", 1.0), "min_reward_risk", minimum=0.5, maximum=5.0)
    if reward_risk < min_reward_risk:
        return _reject("Net reward-to-risk is below the configured minimum",
                       agent_count=agent_count, votes=votes, consensus_score=consensus_score, direction=dominant)

    estimated_risk = quantity * risk_per_unit
    estimated_notional = quantity * notional_per_unit
    effective_leverage = estimated_notional / capital
    return {
        "status": "APPROVED_FOR_SIMULATION",
        "decision": "SIMULATE_ONLY",
        "symbol": symbol,
        "asset_class": asset_class,
        "direction": dominant,
        "reason": "Logical-agent consensus passed deterministic sizing and risk gates",
        "agent_count": agent_count,
        "logical_agents_only": True,
        "confidence": round(confidence, 6),
        "consensus_score": round(consensus_score, 6),
        "votes": {side: int(votes[side]) for side in ("long", "short", "flat")},
        "role_scores": {role: round(score, 6) for role, score in role_scores.items()},
        "risk": {
            "risk_budget": round(risk_budget, 8),
            "effective_risk_pct": round(effective_risk_pct, 6),
            "risk_per_unit_including_estimated_costs": round(risk_per_unit, 8),
            "estimated_total_risk": round(estimated_risk, 8),
            "estimated_notional": round(estimated_notional, 8),
            "effective_leverage": round(effective_leverage, 6),
            "margin_rate_assumption": margin_rate,
            "margin_required_per_unit_assumption": round(margin_required_per_unit, 8),
            "risk_model": risk_model_details,
            "fee_bps_per_side_assumption": fee_bps,
            "slippage_bps_per_side_assumption": slippage_bps,
            "reward_risk_ratio_after_costs": round(reward_risk, 6),
            "daily_loss_limit_pct": max_daily_loss_pct,
            "current_daily_loss_pct": daily_loss_pct,
            "open_position_risk_pct": open_risk_pct,
            "guardrails": {"max_single_trade_risk_pct": 1.0, "max_aggregate_open_risk_pct": 3.0,
                           "max_agent_count": MAX_LOGICAL_AGENTS},
        },
        "sizing": {"quantity": round(quantity, 10), "unit_step": unit_step,
                   "entry_price": entry, "stop_price": stop, "target_price": target,
                   "multiplier": multiplier},
        "execution": {"mode": "simulation_only", "order_submitted": False,
                      "fill_claimed": False, "broker_connected": False},
        "warnings": [
            "Signals are caller-supplied directional features, not model predictions.",
            "Sizing is only as accurate as the supplied multiplier, margin, fees, slippage and instrument rules.",
            "No broker, exchange, live order, or stateful paper account is connected by this endpoint.",
        ],
    }
