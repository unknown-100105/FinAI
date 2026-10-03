from dataclasses import asdict, dataclass
from typing import Any, Dict, List, Optional


@dataclass(frozen=True)
class ArbitrageEstimate:
    asset: str
    buy_venue: str
    sell_venue: str
    capital_quote: float
    buy_price: float
    sell_price: float
    quantity: float
    gross_spread_quote: float
    buy_fee_quote: float
    sell_fee_quote: float
    slippage_cost_quote: float
    transfer_cost_quote: float
    fx_cost_quote: float
    tax_cost_quote: float
    net_profit_quote: float
    net_return_percent: float
    break_even_sell_price: float
    profitable_after_costs: bool
    execution_warning: str


def _pct(value: float) -> float:
    return max(0.0, float(value)) / 100.0


def estimate_arbitrage(
    *,
    asset: str,
    buy_venue: str,
    sell_venue: str,
    capital_quote: float,
    buy_price: float,
    sell_price: float,
    buy_fee_percent: float = 0.0,
    sell_fee_percent: float = 0.0,
    buy_slippage_percent: float = 0.0,
    sell_slippage_percent: float = 0.0,
    transfer_cost_quote: float = 0.0,
    fx_cost_percent: float = 0.0,
    tax_rate_percent: float = 0.0,
    max_quantity: Optional[float] = None,
) -> Dict[str, Any]:
    """Estimate cross-venue crypto arbitrage without placing any orders."""

    values = {
        "capital_quote": capital_quote,
        "buy_price": buy_price,
        "sell_price": sell_price,
        "transfer_cost_quote": transfer_cost_quote,
    }

    for name, value in values.items():
        if float(value) < 0:
            raise ValueError(f"{name} must not be negative.")

    if capital_quote <= 0 or buy_price <= 0 or sell_price <= 0:
        raise ValueError("capital_quote, buy_price and sell_price must be positive.")

    if buy_price > 1e18 or sell_price > 1e18:
        raise ValueError("Price is outside supported range.")

    buy_fee = _pct(buy_fee_percent)
    sell_fee = _pct(sell_fee_percent)
    buy_slippage = _pct(buy_slippage_percent)
    sell_slippage = _pct(sell_slippage_percent)
    fx_rate = _pct(fx_cost_percent)
    tax_rate = _pct(tax_rate_percent)

    effective_buy_unit = buy_price * (1.0 + buy_slippage)
    cost_per_unit = effective_buy_unit * (1.0 + buy_fee)

    quantity = capital_quote / cost_per_unit

    if max_quantity is not None:
        if max_quantity <= 0:
            raise ValueError("max_quantity must be positive when provided.")
        quantity = min(quantity, float(max_quantity))

    buy_notional = quantity * effective_buy_unit
    buy_fee_quote = buy_notional * buy_fee

    effective_sell_unit = sell_price * max(0.0, 1.0 - sell_slippage)
    sell_notional = quantity * effective_sell_unit
    sell_fee_quote = sell_notional * sell_fee

    slippage_cost_quote = quantity * (
        buy_price * buy_slippage
        + sell_price * sell_slippage
    )

    gross_proceeds = sell_notional - sell_fee_quote
    transfer_cost = float(transfer_cost_quote)
    fx_cost_quote = max(0.0, gross_proceeds) * fx_rate

    pre_tax_profit = (
        gross_proceeds
        - buy_notional
        - buy_fee_quote
        - transfer_cost
        - fx_cost_quote
    )

    tax_cost_quote = max(0.0, pre_tax_profit) * tax_rate
    net_profit = pre_tax_profit - tax_cost_quote

    net_return_percent = (
        (net_profit / capital_quote) * 100.0
        if capital_quote
        else 0.0
    )

    denominator = quantity * max(0.0, 1.0 - sell_slippage) * max(
        1e-12, 1.0 - sell_fee
    )

    fixed_cost = (
        buy_notional
        + buy_fee_quote
        + transfer_cost
        + fx_cost_quote
        + tax_cost_quote
    )

    break_even_sell_price = (
        fixed_cost / denominator
        if denominator > 0
        else float("inf")
    )

    warning = (
        "Simulation only: prices are snapshots, order-book depth, "
        "latency, transfer time, withdrawal limits, network congestion, "
        "venue outages, taxes and execution risk can eliminate an apparent spread."
    )

    return asdict(
        ArbitrageEstimate(
            asset=asset,
            buy_venue=buy_venue,
            sell_venue=sell_venue,
            capital_quote=float(capital_quote),
            buy_price=float(buy_price),
            sell_price=float(sell_price),
            quantity=float(quantity),
            gross_spread_quote=float(
                quantity * (sell_price - buy_price)
            ),
            buy_fee_quote=float(buy_fee_quote),
            sell_fee_quote=float(sell_fee_quote),
            slippage_cost_quote=float(slippage_cost_quote),
            transfer_cost_quote=transfer_cost,
            fx_cost_quote=float(fx_cost_quote),
            tax_cost_quote=float(tax_cost_quote),
            net_profit_quote=float(net_profit),
            net_return_percent=float(net_return_percent),
            break_even_sell_price=float(break_even_sell_price),
            profitable_after_costs=bool(net_profit > 0),
            execution_warning=warning,
        )
    )


def rank_opportunities(
    opportunities: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """Sort already-computed simulations by net profit percentage."""
    return sorted(
        opportunities,
        key=lambda item: float(item.get("net_return_percent", 0.0)),
        reverse=True,
    )
