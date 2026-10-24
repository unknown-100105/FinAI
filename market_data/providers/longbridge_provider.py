"""Longbridge implementation of FinAI's provider-independent market-data API."""

from __future__ import annotations

from datetime import date, datetime, timezone
from typing import Any, List, Optional

from finance_engine.data_sources.longbridge import LongbridgeClient
from finance_engine.data_sources.normalize import to_number
from market_data.base import MarketDataProvider
from market_data.models import MarketBar, MarketQuote


def _timestamp(value: Any) -> Optional[datetime]:
    if value is None or value == "":
        return None
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
    if isinstance(value, date):
        return datetime(value.year, value.month, value.day, tzinfo=timezone.utc)
    if isinstance(value, (int, float)) or (
        isinstance(value, str) and value.strip().isdigit()
    ):
        try:
            return datetime.fromtimestamp(float(value), tz=timezone.utc)
        except (OverflowError, OSError, ValueError):
            return None
    text = str(value).strip()
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        return None
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)


def _sdk_symbol(symbol: str, exchange: Optional[str]) -> str:
    value = str(symbol).strip().upper()
    if not value:
        raise ValueError("Market symbol must not be empty.")
    if "." in value or not exchange:
        return value
    suffix = {
        "US": "US", "NASDAQ": "US", "NYSE": "US",
        "HK": "HK", "HKEX": "HK",
        "SH": "SH", "SSE": "SH",
        "SZ": "SZ", "SZSE": "SZ",
        "SG": "SG", "SGX": "SG",
    }.get(str(exchange).strip().upper())
    return f"{value}.{suffix}" if suffix else value


class LongbridgeMarketDataProvider(MarketDataProvider):
    """Read-only quote and OHLCV history provider powered by Longbridge OpenAPI."""

    provider_id = "longbridge"

    def __init__(self, client: Optional[LongbridgeClient] = None) -> None:
        self.client = client or LongbridgeClient()

    def get_quote(
        self,
        symbol: str,
        asset_type: str,
        exchange: Optional[str] = None,
    ) -> MarketQuote:
        sdk_symbol = _sdk_symbol(symbol, exchange)
        row = self.client.get_quote(sdk_symbol)
        return MarketQuote(
            symbol=symbol,
            asset_type=asset_type,
            exchange=exchange,
            price=to_number(row.get("last_done")),
            open=to_number(row.get("open")),
            high=to_number(row.get("high")),
            low=to_number(row.get("low")),
            close=to_number(row.get("prev_close_price", row.get("prev_close"))),
            volume=to_number(row.get("volume")),
            currency=(
                str(row.get("currency")).upper()
                if row.get("currency") else None
            ),
            timestamp=_timestamp(row.get("timestamp")),
            source=self.provider_id,
        )

    def get_history(
        self,
        symbol: str,
        asset_type: str,
        start: datetime,
        end: datetime,
        exchange: Optional[str] = None,
        interval: str = "1d",
    ) -> List[MarketBar]:
        if start > end:
            raise ValueError("History start must not be after end.")
        sdk_symbol = _sdk_symbol(symbol, exchange)
        rows = self.client.get_history(sdk_symbol, start, end, interval)
        bars: List[MarketBar] = []
        for row in rows:
            timestamp = _timestamp(row.get("timestamp"))
            open_value = to_number(row.get("open"))
            high_value = to_number(row.get("high"))
            low_value = to_number(row.get("low"))
            close_value = to_number(row.get("close"))
            if timestamp is None or any(
                value is None
                for value in (open_value, high_value, low_value, close_value)
            ):
                continue
            bars.append(MarketBar(
                symbol=symbol,
                timestamp=timestamp,
                open=open_value,
                high=high_value,
                low=low_value,
                close=close_value,
                volume=to_number(row.get("volume")),
                source=self.provider_id,
            ))
        return bars
