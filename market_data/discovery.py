from typing import Any, Dict, List, Optional

import yfinance as yf


_QUOTE_TYPE_MAP = {
    "EQUITY": "equity",
    "ETF": "etf",
    "MUTUALFUND": "mutual_fund",
    "INDEX": "index",
    "FUTURE": "future",
    "CURRENCY": "currency",
    "CRYPTOCURRENCY": "cryptocurrency",
}


def normalize_search_result(item: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    if not isinstance(item, dict):
        return None

    symbol = item.get("symbol")
    if not symbol:
        return None

    quote_type = str(
        item.get("quoteType") or item.get("typeDisp") or ""
    ).upper()

    return {
        "symbol": str(symbol),
        "name": str(
            item.get("longname")
            or item.get("shortname")
            or item.get("name")
            or symbol
        ).strip(),
        "asset_type": _QUOTE_TYPE_MAP.get(
            quote_type,
            quote_type.lower() or "unknown",
        ),
        "quote_type": quote_type or None,
        "exchange": item.get("exchange"),
        "exchange_full_name": item.get("fullExchangeName"),
        "currency": item.get("currency"),
        "score": item.get("score"),
        "provider": "yfinance",
    }


def search_instruments(
    query: str,
    count: int = 20,
) -> List[Dict[str, Any]]:
    normalized = str(query).strip()
    if not normalized:
        raise ValueError("Instrument search query must not be empty.")

    count = max(1, min(int(count), 50))

    try:
        result = yf.Search(
            normalized,
            max_results=count,
            news_count=0,
            include_cb=False,
            enable_fuzzy_query=True,
        )
        quotes = result.quotes or []
    except Exception as exc:
        raise RuntimeError(
            f"Financial instrument search failed for '{normalized}': {exc}"
        ) from exc

    matches = []
    for item in quotes:
        normalized_item = normalize_search_result(item)
        if normalized_item is not None:
            matches.append(normalized_item)
        if len(matches) >= count:
            break

    return matches
