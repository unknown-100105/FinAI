from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List

from .arbitrage import estimate_arbitrage, rank_opportunities


def _load_ccxt():
    try:
        import ccxt
    except ImportError as exc:
        raise RuntimeError(
            "CCXT is not installed. Install the optional crypto exchange "
            "adapter with 'pip install ccxt'."
        ) from exc
    return ccxt


def fetch_orderbook_snapshot(
    exchange_id: str,
    symbol: str,
    limit: int = 20,
) -> Dict[str, Any]:
    ccxt = _load_ccxt()
    exchange_class = getattr(ccxt, exchange_id, None)

    if exchange_class is None:
        raise ValueError(f"Unsupported CCXT exchange: {exchange_id}")

    exchange = exchange_class({"enableRateLimit": True})
    book = exchange.fetch_order_book(symbol, limit=limit)

    if not book.get("asks") or not book.get("bids"):
        raise RuntimeError(
            f"No two-sided order book returned by {exchange_id} for {symbol}."
        )

    return {
        "exchange": exchange_id,
        "symbol": symbol,
        "best_bid": float(book["bids"][0][0]),
        "best_bid_amount": float(book["bids"][0][1]),
        "best_ask": float(book["asks"][0][0]),
        "best_ask_amount": float(book["asks"][0][1]),
        "timestamp": book.get("timestamp"),
        "fetched_at": datetime.now(timezone.utc).isoformat(),
    }


def scan_cross_exchange_arbitrage(
    *,
    symbol: str = "BTC/USDT",
    exchanges: Iterable[str] = ("binance", "bybit", "okx", "kucoin"),
    capital_quote: float = 1000.0,
    buy_fee_percent: float = 0.1,
    sell_fee_percent: float = 0.1,
    buy_slippage_percent: float = 0.05,
    sell_slippage_percent: float = 0.05,
    transfer_cost_quote: float = 0.0,
    fx_cost_percent: float = 0.0,
    tax_rate_percent: float = 0.0,
) -> Dict[str, Any]:
    snapshots = []

    for exchange_id in dict.fromkeys(
        str(item).strip().lower()
        for item in exchanges
        if str(item).strip()
    ):
        try:
            snapshots.append(
                fetch_orderbook_snapshot(
                    exchange_id=exchange_id,
                    symbol=symbol,
                )
            )
        except Exception as exc:
            snapshots.append(
                {
                    "exchange": exchange_id,
                    "symbol": symbol,
                    "error": str(exc),
                }
            )

    valid = [item for item in snapshots if "error" not in item]
    opportunities = []

    for buy in valid:
        for sell in valid:
            if buy["exchange"] == sell["exchange"]:
                continue

            max_quantity = min(
                buy["best_ask_amount"],
                sell["best_bid_amount"],
            )

            if max_quantity <= 0:
                continue

            result = estimate_arbitrage(
                asset=symbol,
                buy_venue=buy["exchange"],
                sell_venue=sell["exchange"],
                capital_quote=capital_quote,
                buy_price=buy["best_ask"],
                sell_price=sell["best_bid"],
                buy_fee_percent=buy_fee_percent,
                sell_fee_percent=sell_fee_percent,
                buy_slippage_percent=buy_slippage_percent,
                sell_slippage_percent=sell_slippage_percent,
                transfer_cost_quote=transfer_cost_quote,
                fx_cost_percent=fx_cost_percent,
                tax_rate_percent=tax_rate_percent,
                max_quantity=max_quantity,
            )

            opportunities.append(result)

    ranked = rank_opportunities(opportunities)

    return {
        "symbol": symbol,
        "capital_quote": capital_quote,
        "snapshots": snapshots,
        "opportunities": ranked,
        "note": (
            "This scan compares public order-book snapshots. It is not an "
            "execution engine and does not account for private account "
            "limits, custody availability, transfer settlement, or atomic "
            "execution across venues."
        ),
    }
