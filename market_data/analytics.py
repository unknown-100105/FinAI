from dataclasses import dataclass
from math import sqrt
from statistics import mean, stdev
from typing import List, Optional

from .models import MarketBar


@dataclass(frozen=True)
class MarketAnalytics:
    symbol: str
    observations: int
    latest_close: Optional[float]
    cumulative_return: Optional[float]
    annualized_volatility: Optional[float]
    maximum_drawdown: Optional[float]
    sma_20: Optional[float]
    sma_50: Optional[float]
    ema_20: Optional[float]
    rsi_14: Optional[float]


def _closes(bars: List[MarketBar]) -> List[float]:
    return [
        float(bar.close)
        for bar in bars
        if bar.close is not None
    ]


def _sma(values: List[float], period: int) -> Optional[float]:
    if len(values) < period:
        return None

    return mean(values[-period:])


def _ema(values: List[float], period: int) -> Optional[float]:
    if len(values) < period:
        return None

    multiplier = 2.0 / (period + 1)
    ema = mean(values[:period])

    for value in values[period:]:
        ema = (
            (value - ema) * multiplier
        ) + ema

    return ema


def _returns(values: List[float]) -> List[float]:
    if len(values) < 2:
        return []

    result = []

    for previous, current in zip(values, values[1:]):
        if previous == 0:
            continue

        result.append((current / previous) - 1.0)

    return result


def _volatility(values: List[float], periods_per_year: float = 252.0) -> Optional[float]:
    returns = _returns(values)

    if len(returns) < 2:
        return None

    return stdev(returns) * sqrt(max(1.0, periods_per_year))


def _maximum_drawdown(values: List[float]) -> Optional[float]:
    if not values:
        return None

    peak = values[0]
    maximum_drawdown = 0.0

    for value in values:
        if value > peak:
            peak = value

        if peak == 0:
            continue

        drawdown = (value / peak) - 1.0

        if drawdown < maximum_drawdown:
            maximum_drawdown = drawdown

    return maximum_drawdown


def _rsi(values: List[float], period: int = 14) -> Optional[float]:
    if len(values) <= period:
        return None

    changes = [
        current - previous
        for previous, current in zip(values, values[1:])
    ]

    gains = [max(change, 0.0) for change in changes]
    losses = [max(-change, 0.0) for change in changes]

    average_gain = mean(gains[:period])
    average_loss = mean(losses[:period])

    for gain, loss in zip(
        gains[period:],
        losses[period:],
    ):
        average_gain = (
            (average_gain * (period - 1)) + gain
        ) / period

        average_loss = (
            (average_loss * (period - 1)) + loss
        ) / period

    if average_loss == 0:
        return 100.0

    relative_strength = average_gain / average_loss

    return 100.0 - (
        100.0 / (1.0 + relative_strength)
    )


def calculate_market_analytics(
    bars: List[MarketBar],
    interval: str = "1d",
) -> MarketAnalytics:
    annualization_periods = {
        "1m": 252 * 6.25 * 60,
        "2m": 252 * 6.25 * 30,
        "5m": 252 * 6.25 * 12,
        "15m": 252 * 25,
        "30m": 252 * 12.5,
        "60m": 252 * 6.25,
        "1h": 252 * 6.25,
        "1d": 252,
        "5d": 52,
        "1wk": 52,
        "1mo": 12,
        "3mo": 4,
    }
    periods_per_year = annualization_periods.get(interval, 252.0)
    if not bars:
        return MarketAnalytics(
            symbol="",
            observations=0,
            latest_close=None,
            cumulative_return=None,
            annualized_volatility=None,
            maximum_drawdown=None,
            sma_20=None,
            sma_50=None,
            ema_20=None,
            rsi_14=None,
        )

    values = _closes(bars)

    if not values:
        return MarketAnalytics(
            symbol=bars[-1].symbol,
            observations=0,
            latest_close=None,
            cumulative_return=None,
            annualized_volatility=None,
            maximum_drawdown=None,
            sma_20=None,
            sma_50=None,
            ema_20=None,
            rsi_14=None,
        )

    cumulative_return = None

    if len(values) >= 2 and values[0] != 0:
        cumulative_return = (
            values[-1] / values[0]
        ) - 1.0

    return MarketAnalytics(
        symbol=bars[-1].symbol,
        observations=len(values),
        latest_close=values[-1],
        cumulative_return=cumulative_return,
        annualized_volatility=_volatility(values, periods_per_year),
        maximum_drawdown=_maximum_drawdown(values),
        sma_20=_sma(values, 20),
        sma_50=_sma(values, 50),
        ema_20=_ema(values, 20),
        rsi_14=_rsi(values, 14),
    )
