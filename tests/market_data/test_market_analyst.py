from datetime import datetime, timedelta

from market_data.analyst import analyze_candles, build_scenario
from market_data.models import MarketBar


def make_bars(count=25):
    start = datetime(2026, 1, 1)
    bars = []
    for index in range(count):
        close = 100.0 + index
        bars.append(
            MarketBar(
                symbol="TEST",
                timestamp=start + timedelta(days=index),
                open=close - 0.5,
                high=close + 1.0,
                low=close - 1.5,
                close=close,
                volume=1000.0,
                source="test",
            )
        )
    return bars


def test_analyze_candles_builds_forward_scenarios_without_missing_previous_argument():
    result = analyze_candles(make_bars())

    assert result["count"] == 25
    assert result["candles"]
    assert result["scenario"]["previous_candle_available"] is True
    assert result["scenario"]["scenarios"]
    assert "forecast_note" in result["scenario"]


def test_build_scenario_accepts_previous_and_optional_trend_references():
    current = {
        "close": 125.0,
        "direction": "bullish",
        "trend_last_5": "rising",
    }
    previous = {"close": 124.0}

    result = build_scenario(current, previous, sma20=120.0, sma50=118.0)

    assert result["previous_candle_available"] is True
    assert result["scenarios"]
