from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Dict


DEFAULT_MARKET_WATCH = (
    "NIFTY 50",
    "SENSEX",
    "TCS",
    "INFY",
    "RELIANCE",
    "HDFCBANK",
    "ICICIBANK",
    "SBIN",
    "ITC",
    "LT",
)


def build_market_overview(
    market_data_service,
    resolver,
    provider_id: str = "yfinance",
) -> Dict[str, Any]:
    items = []

    def load(query: str):
        item = resolver.resolve_or_raise(query)
        quote = market_data_service.quote(
            symbol=item.display_name,
            asset_type=item.asset_type,
            exchange=item.exchange,
            provider_id=provider_id,
        )

        price = quote.price
        open_value = quote.open
        change = None
        change_percent = None

        if price is not None and open_value not in (None, 0):
            change = price - open_value
            change_percent = change / open_value

        return {
            "instrument": {
                "instrument_id": item.instrument_id,
                "display_name": item.display_name,
                "asset_type": item.asset_type,
                "exchange": item.exchange,
                "currency": item.currency,
            },
            "price": price,
            "open": open_value,
            "high": quote.high,
            "low": quote.low,
            "close": quote.close,
            "volume": quote.volume,
            "change": change,
            "change_percent": change_percent,
            "timestamp": quote.timestamp,
            "source": quote.source,
        }

    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = {
            executor.submit(load, query): query
            for query in DEFAULT_MARKET_WATCH
        }

        for future in as_completed(futures):
            query = futures[future]
            try:
                items.append(future.result())
            except Exception as exc:
                items.append({
                    "instrument": {"display_name": query},
                    "error": str(exc),
                })

    items.sort(
        key=lambda item: str(
            item.get("instrument", {}).get("display_name", "")
        )
    )

    valid = [
        item
        for item in items
        if item.get("change_percent") is not None
    ]

    gainers = sorted(
        valid,
        key=lambda item: item["change_percent"],
        reverse=True,
    )[:5]

    losers = sorted(
        valid,
        key=lambda item: item["change_percent"],
    )[:5]

    return {
        "source": provider_id,
        "instruments": items,
        "gainers": gainers,
        "losers": losers,
    }
