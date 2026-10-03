"""Candle-by-candle market analyst.

Describes observed OHLCV structure and links current news as possible drivers
to investigate. A candle by itself cannot prove causality.
"""
from __future__ import annotations
from statistics import median
from typing import Any, Dict, List
from market_data.models import MarketBar

def analyze_candles(bars: List[MarketBar], news: List[Dict[str, Any]] | None = None) -> Dict[str, Any]:
    if not bars:
        return {"count": 0, "candles": [], "summary": "No candles available."}
    volumes = [float(bar.volume or 0) for bar in bars]
    positive_volumes = [v for v in volumes if v > 0]
    typical_volume = median(positive_volumes) if positive_volumes else 0.0
    output = []
    for index, bar in enumerate(bars):
        o,h,l,c = map(float, (bar.open, bar.high, bar.low, bar.close))
        rng = max(h-l,0.0)
        body = abs(c-o)
        upper = max(h-max(o,c),0.0)
        lower = max(min(o,c)-l,0.0)
        body_pct = body/rng*100 if rng else 0.0
        upper_pct = upper/rng*100 if rng else 0.0
        lower_pct = lower/rng*100 if rng else 0.0
        ret = (c/float(bars[index-1].close)-1)*100 if index and float(bars[index-1].close) else None
        rel_vol = float(bar.volume or 0)/typical_volume if typical_volume else None
        direction = "bullish" if c > o else "bearish" if c < o else "doji"
        observed = []
        if body_pct < 20: observed.append("small body / indecision")
        if upper_pct > 35: observed.append("large upper wick / rejection near high")
        if lower_pct > 35: observed.append("large lower wick / rejection near low")
        if body_pct > 65: observed.append("strong " + direction + " body")
        if rel_vol is not None and rel_vol >= 1.8: observed.append("unusually high volume")
        if ret is not None and abs(ret) >= 2: observed.append("large close-to-close move")
        trend = "flat"
        if index >= 4:
            first = float(bars[index-4].close)
            trend = "rising" if c > first else "falling" if c < first else "flat"
        drivers = (
            ["positive company/index news", "broader risk-on demand", "buying pressure or short covering"]
            if direction == "bullish" else
            ["negative company/index news", "broader risk-off demand", "selling pressure or profit taking"]
            if direction == "bearish" else
            ["balanced buying and selling pressure"]
        )
        if rel_vol is not None and rel_vol >= 1.8:
            drivers.append("event-driven activity is worth checking because volume is elevated")
        output.append({
            "index": index,
            "timestamp": bar.timestamp.isoformat() if hasattr(bar.timestamp,"isoformat") else str(bar.timestamp),
            "open": round(o,8), "high": round(h,8), "low": round(l,8), "close": round(c,8),
            "volume": float(bar.volume or 0),
            "direction": direction,
            "return_percent": None if ret is None else round(ret,4),
            "range_percent": round(rng/o*100,4) if o else None,
            "body_percent_of_range": round(body_pct,2),
            "upper_wick_percent_of_range": round(upper_pct,2),
            "lower_wick_percent_of_range": round(lower_pct,2),
            "relative_volume": None if rel_vol is None else round(rel_vol,2),
            "trend_last_5": trend,
            "observed_features": observed,
            "possible_drivers_to_investigate": drivers,
            "news_candidates": news[:5] if news else [],
            "causality_note": "Possible drivers are hypotheses to investigate; candle anatomy alone does not establish cause.",
        })
    return {
        "count": len(output),
        "candles": output,
        "summary": {
            "first_timestamp": output[0]["timestamp"],
            "last_timestamp": output[-1]["timestamp"],
            "net_return_percent": round((output[-1]["close"]/output[0]["close"]*100)-100,4) if output[0]["close"] else None,
        },
    }
