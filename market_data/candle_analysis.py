"""Candle-by-candle market analysis for equities, indices and crypto-like instruments."""

from __future__ import annotations

from dataclasses import asdict
from datetime import datetime
from statistics import mean
from typing import Any, Dict, List

from market_data.models import MarketBar


def _pct(value: float, base: float) -> float:
    return (value / base * 100.0) if base else 0.0


def _direction(open_value: float, close_value: float) -> str:
    if close_value > open_value:
        return "bullish"
    if close_value < open_value:
        return "bearish"
    return "neutral"


def analyze_candles(bars: List[MarketBar], max_candles: int = 2000) -> Dict[str, Any]:
    """Explain each available candle without claiming causal certainty."""
    if not bars:
        return {
            "count": 0,
            "candles": [],
            "summary": {},
            "method": "OHLCV pattern analysis",
        }

    selected = bars[-max(1, min(int(max_candles), 5000)):]
    closes = [float(bar.close) for bar in selected]
    volumes = [float(bar.volume or 0.0) for bar in selected]
    avg_volume = mean(volumes) if volumes else 0.0

    output = []
    for index, bar in enumerate(selected):
        previous = selected[index - 1] if index else None
        body = abs(float(bar.close) - float(bar.open))
        total_range = max(0.0, float(bar.high) - float(bar.low))
        upper_wick = max(0.0, float(bar.high) - max(float(bar.open), float(bar.close)))
        lower_wick = max(0.0, min(float(bar.open), float(bar.close)) - float(bar.low))
        body_pct = _pct(body, total_range)
        upper_pct = _pct(upper_wick, total_range)
        lower_pct = _pct(lower_wick, total_range)

        close_change_pct = (
            ((float(bar.close) / float(previous.close)) - 1.0) * 100.0
            if previous and previous.close
            else None
        )
        gap_pct = (
            ((float(bar.open) / float(previous.close)) - 1.0) * 100.0
            if previous and previous.close
            else None
        )
        volume_ratio = (
            float(bar.volume or 0.0) / avg_volume
            if avg_volume and bar.volume is not None
            else None
        )

        if body_pct < 10 and upper_pct > 35 and lower_pct > 35:
            pattern = "doji / indecision"
        elif body_pct > 70 and lower_pct < 15 and upper_pct < 15:
            pattern = "strong full-body candle"
        elif lower_pct > 45 and upper_pct < 20:
            pattern = "long lower-wick rejection"
        elif upper_pct > 45 and lower_pct < 20:
            pattern = "long upper-wick rejection"
        elif body_pct >= 55:
            pattern = "strong directional candle"
        else:
            pattern = "mixed-range candle"

        drivers = []
        if volume_ratio is not None and volume_ratio >= 1.8:
            drivers.append("unusually high volume")
        if close_change_pct is not None and abs(close_change_pct) >= 2:
            drivers.append("large price move relative to prior candle")
        if gap_pct is not None and abs(gap_pct) >= 1:
            drivers.append("material gap from prior close")
        if lower_pct >= 40:
            drivers.append("lower-price rejection")
        if upper_pct >= 40:
            drivers.append("upper-price rejection")

        explanation = (
            f"{pattern}; {direction_label := _direction(float(bar.open), float(bar.close))} close "
            f"with body {body_pct:.1f}% of range"
        )
        if drivers:
            explanation += ". Possible market-reading cues: " + ", ".join(drivers) + "."
        else:
            explanation += ". No dominant mechanical candle cue."

        output.append({
            "timestamp": bar.timestamp.isoformat() if isinstance(bar.timestamp, datetime) else str(bar.timestamp),
            "open": float(bar.open),
            "high": float(bar.high),
            "low": float(bar.low),
            "close": float(bar.close),
            "volume": float(bar.volume) if bar.volume is not None else None,
            "direction": _direction(float(bar.open), float(bar.close)),
            "body_percent_of_range": round(body_pct, 3),
            "upper_wick_percent_of_range": round(upper_pct, 3),
            "lower_wick_percent_of_range": round(lower_pct, 3),
            "candle_range": round(total_range, 8),
            "close_change_percent": round(close_change_pct, 4) if close_change_pct is not None else None,
            "gap_percent": round(gap_pct, 4) if gap_pct is not None else None,
            "volume_ratio_to_window_average": round(volume_ratio, 3) if volume_ratio is not None else None,
            "pattern": pattern,
            "possible_cues": drivers,
            "explanation": explanation,
        })

    bullish = sum(1 for item in output if item["direction"] == "bullish")
    bearish = sum(1 for item in output if item["direction"] == "bearish")
    return {
        "count": len(output),
        "candles": output,
        "summary": {
            "bullish_candles": bullish,
            "bearish_candles": bearish,
            "neutral_candles": len(output) - bullish - bearish,
            "latest_close": output[-1]["close"],
            "window_change_percent": (
                ((output[-1]["close"] / output[0]["close"]) - 1.0) * 100.0
                if output[0]["close"]
                else None
            ),
        },
        "method": "OHLCV candle anatomy and relative-volume heuristics",
        "causality_note": "Candle patterns describe observed price/volume behaviour. Possible reasons are hypotheses until corroborated by news, filings, macro or other evidence.",
    }
