from __future__ import annotations

import math
from statistics import mean, stdev

from .models import Portfolio


def annualized_volatility(
    returns: list[float],
    periods_per_year: int = 252,
) -> float:
    if len(returns) < 2:
        return 0.0

    daily_std = stdev(returns)

    return daily_std * math.sqrt(periods_per_year)


def maximum_drawdown(equity_curve: list[float]) -> float:
    if not equity_curve:
        return 0.0

    peak = equity_curve[0]
    max_drawdown = 0.0

    for value in equity_curve:
        if value > peak:
            peak = value

        if peak > 0:
            drawdown = (peak - value) / peak
            max_drawdown = max(max_drawdown, drawdown)

    return max_drawdown


def sharpe_ratio(
    returns: list[float],
    risk_free_rate_per_period: float = 0.0,
    periods_per_year: int = 252,
) -> float:
    if len(returns) < 2:
        return 0.0

    excess_returns = [
        value - risk_free_rate_per_period
        for value in returns
    ]

    avg = mean(excess_returns)
    volatility = stdev(excess_returns)

    if volatility == 0:
        return 0.0

    return (
        avg / volatility
    ) * math.sqrt(periods_per_year)


def portfolio_concentration_score(portfolio: Portfolio) -> float:
    """
    Converts HHI into a 0-100 concentration score.
    Higher means more concentrated.
    """
    total = portfolio.total_value

    if total <= 0:
        return 0.0

    weights = [
        holding.market_value / total
        for holding in portfolio.holdings
    ]

    hhi = sum(weight * weight for weight in weights)

    return min(100.0, hhi * 100.0)


def top_holding_concentration_score(portfolio: Portfolio) -> float:
    total = portfolio.total_value

    if total <= 0:
        return 0.0

    top = max(
        (holding.market_value for holding in portfolio.holdings),
        default=0.0,
    )

    return min(100.0, (top / total) * 100.0)