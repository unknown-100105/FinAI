from datetime import datetime, timedelta

import pytest

from market_data.analytics import calculate_market_analytics
from market_data.models import MarketBar


def make_bars(values):
    start = datetime(2026, 1, 1)

    return [
        MarketBar(
            symbol="TEST",
            timestamp=start + timedelta(days=index),
            open=value,
            high=value,
            low=value,
            close=value,
            volume=1000.0,
            source="test",
        )
        for index, value in enumerate(values)
    ]


def test_empty_bars():
    result = calculate_market_analytics([])

    assert result.observations == 0
    assert result.latest_close is None
    assert result.cumulative_return is None


def test_cumulative_return():
    bars = make_bars([100.0, 110.0])

    result = calculate_market_analytics(bars)

    assert result.cumulative_return == pytest.approx(0.10)


def test_latest_close():
    bars = make_bars([100.0, 105.0, 112.0])

    result = calculate_market_analytics(bars)

    assert result.latest_close == 112.0
    assert result.observations == 3


def test_maximum_drawdown():
    bars = make_bars(
        [100.0, 120.0, 90.0, 110.0]
    )

    result = calculate_market_analytics(bars)

    assert result.maximum_drawdown == -0.25


def test_sma_20():
    values = [float(index) for index in range(1, 21)]
    bars = make_bars(values)

    result = calculate_market_analytics(bars)

    assert result.sma_20 == 10.5


def test_ema_20_requires_20_observations():
    bars = make_bars(
        [float(index) for index in range(1, 20)]
    )

    result = calculate_market_analytics(bars)

    assert result.ema_20 is None


def test_rsi_uptrend():
    bars = make_bars(
        [float(100 + index) for index in range(20)]
    )

    result = calculate_market_analytics(bars)

    assert result.rsi_14 == 100.0


def test_volatility_requires_multiple_returns():
    bars = make_bars([100.0, 101.0])

    result = calculate_market_analytics(bars)

    assert result.annualized_volatility is None


