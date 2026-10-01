from __future__ import annotations

from collections import defaultdict

from .models import Portfolio


def holding_weights(portfolio: Portfolio) -> dict[str, float]:
    total = portfolio.total_value

    if total <= 0:
        return {h.symbol: 0.0 for h in portfolio.holdings}

    return {
        h.symbol: h.market_value / total
        for h in portfolio.holdings
    }


def asset_allocation(portfolio: Portfolio) -> dict[str, float]:
    total = portfolio.total_value

    if total <= 0:
        return {}

    values: dict[str, float] = defaultdict(float)

    for holding in portfolio.holdings:
        values[holding.asset_class] += holding.market_value

    return {
        asset_class: value / total
        for asset_class, value in values.items()
    }


def sector_exposure(portfolio: Portfolio) -> dict[str, float]:
    total = portfolio.total_value

    if total <= 0:
        return {}

    values: dict[str, float] = defaultdict(float)

    for holding in portfolio.holdings:
        sector = holding.sector or "Unclassified"
        values[sector] += holding.market_value

    return {
        sector: value / total
        for sector, value in values.items()
    }


def concentration_hhi(portfolio: Portfolio) -> float:
    """
    Herfindahl-Hirschman Index based on holding weights.

    Returns:
        0.0 for an empty/zero-value portfolio.
        1.0 if one holding represents 100% of the portfolio.
    """
    weights = holding_weights(portfolio)

    return sum(weight * weight for weight in weights.values())


def top_holding_weight(portfolio: Portfolio) -> float:
    weights = holding_weights(portfolio)

    if not weights:
        return 0.0

    return max(weights.values())