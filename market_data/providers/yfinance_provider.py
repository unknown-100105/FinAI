from datetime import datetime, timezone
from typing import List, Optional

import pandas as pd
import yfinance as yf

from policy.network_mode import assert_external_network_allowed

from ..base import MarketDataProvider
from ..models import MarketBar, MarketQuote


class YFinanceProvider(MarketDataProvider):
    """
    Yahoo Finance-backed market-data provider.

    This adapter is intentionally isolated behind MarketDataProvider so the
    rest of FinAI does not depend directly on yfinance.
    """

    provider_id = "yfinance"

    _SPECIAL_SYMBOLS = {
        "NIFTY": "^NSEI",
        "NIFTY50": "^NSEI",
        "NIFTY 50": "^NSEI",
        "SENSEX": "^BSESN",
        "USDINR": "USDINR=X",
        "USD/INR": "USDINR=X",
        "EURINR": "EURINR=X",
        "EUR/INR": "EURINR=X",
        "GOLD": "GC=F",
        "SILVER": "SI=F",
        "BTC": "BTC-USD",
        "ETH": "ETH-USD",
    }

    def __init__(self, timeout: int = 10):
        self.timeout = int(timeout)

    def _resolve_symbol(
        self,
        symbol: str,
        asset_type: str,
        exchange: Optional[str] = None,
    ) -> str:
        raw = str(symbol).strip()

        if not raw:
            raise ValueError("Market symbol must not be empty.")

        normalized = raw.upper().replace("-", " ").strip()

        if normalized in self._SPECIAL_SYMBOLS:
            return self._SPECIAL_SYMBOLS[normalized]

        asset = str(asset_type).strip().upper()
        exch = (
            str(exchange).strip().upper()
            if exchange is not None
            else ""
        )

        # Convert common Indian equity identifiers to Yahoo symbols.
        if asset in {"EQUITY", "STOCK", "ETF"}:
            if exch == "NSE" and not raw.upper().endswith(".NS"):
                return f"{raw}.NS"

            if exch == "BSE" and not raw.upper().endswith(".BO"):
                return f"{raw}.BO"

        return raw

    @staticmethod
    def _clean_number(value) -> Optional[float]:
        if value is None:
            return None

        try:
            number = float(value)

            if pd.isna(number):
                return None

            return number
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _clean_timestamp(value) -> Optional[datetime]:
        if value is None:
            return None

        timestamp = pd.Timestamp(value)

        if timestamp.tzinfo is None:
            return timestamp.to_pydatetime().replace(
                tzinfo=timezone.utc
            )

        return timestamp.to_pydatetime()

    @staticmethod
    def _last_valid_row(history: pd.DataFrame):
        if history is None or history.empty:
            return None

        frame = history.dropna(
            subset=["Open", "High", "Low", "Close"],
            how="all",
        )

        if frame.empty:
            return None

        return frame.iloc[-1]

    def get_quote(
        self,
        symbol: str,
        asset_type: str,
        exchange: Optional[str] = None,
    ) -> MarketQuote:
        assert_external_network_allowed("yfinance quote")
        yahoo_symbol = self._resolve_symbol(
            symbol=symbol,
            asset_type=asset_type,
            exchange=exchange,
        )

        ticker = yf.Ticker(yahoo_symbol)

        try:
            history = ticker.history(
                period="5d",
                interval="1d",
                auto_adjust=False,
                actions=False,
                timeout=self.timeout,
            )
        except Exception as exc:
            raise RuntimeError(
                f"yfinance quote request failed for "
                f"'{yahoo_symbol}': {exc}"
            ) from exc

        row = self._last_valid_row(history)

        if row is None:
            raise RuntimeError(
                f"No market quote data returned for "
                f"'{yahoo_symbol}'."
            )

        price = self._clean_number(row.get("Close"))

        # fast_info is optional because some instruments/metadata responses
        # may not expose every field.
        currency = None

        try:
            fast_info = ticker.fast_info
            currency = fast_info.get("currency")
            latest_price = fast_info.get("lastPrice")

            if latest_price is not None:
                price = self._clean_number(latest_price)
        except Exception:
            pass

        return MarketQuote(
            symbol=symbol,
            asset_type=asset_type,
            exchange=exchange,
            price=price,
            open=self._clean_number(row.get("Open")),
            high=self._clean_number(row.get("High")),
            low=self._clean_number(row.get("Low")),
            close=self._clean_number(row.get("Close")),
            volume=self._clean_number(row.get("Volume")),
            currency=(
                str(currency).upper()
                if currency is not None
                else None
            ),
            timestamp=self._clean_timestamp(history.index[-1]),
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
            raise ValueError(
                "History start must not be after history end."
            )

        assert_external_network_allowed("yfinance history")
        yahoo_symbol = self._resolve_symbol(
            symbol=symbol,
            asset_type=asset_type,
            exchange=exchange,
        )

        ticker = yf.Ticker(yahoo_symbol)

        allowed_intervals = {
            "1m", "2m", "5m", "15m", "30m", "60m",
            "90m", "1h", "1d", "5d", "1wk", "1mo", "3mo",
        }

        if interval not in allowed_intervals:
            raise ValueError(
                f"Unsupported history interval: {interval}"
            )

        if interval == "1d":
            request_interval = "1d"
        else:
            request_interval = interval

        # Yahoo Finance imposes shorter retention windows on intraday
        # intervals. Fetch a safe provider window, then clip locally.
        # For a closed exchange, a "1D" stock chart should still be useful:
        # it falls back to the most recent available session instead of
        # rendering an empty chart.
        intraday = interval in {
            "1m", "2m", "5m", "15m", "30m", "60m", "90m", "1h"
        }
        provider_period = None

        if intraday:
            provider_period = "7d" if interval in {"1m", "2m", "5m"} else "60d"

        try:
            if provider_period is not None:
                history = ticker.history(
                    period=provider_period,
                    interval=request_interval,
                    auto_adjust=False,
                    actions=False,
                    timeout=self.timeout,
                )
            else:
                history = ticker.history(
                    start=start,
                    end=end,
                    interval=request_interval,
                    auto_adjust=False,
                    actions=False,
                    timeout=self.timeout,
                )
        except Exception as exc:
            raise RuntimeError(
                f"yfinance history request failed for "
                f"'{yahoo_symbol}': {exc}"
            ) from exc

        if history is None or history.empty:
            return []

        # Provider timestamps can be timezone-aware. Normalize comparison
        # bounds to the same timezone before clipping.
        frame = history.copy()
        try:
            index = pd.DatetimeIndex(frame.index)
            if index.tz is not None:
                start_bound = pd.Timestamp(start)
                end_bound = pd.Timestamp(end)
                if start_bound.tzinfo is None:
                    start_bound = start_bound.tz_localize(index.tz)
                else:
                    start_bound = start_bound.tz_convert(index.tz)
                if end_bound.tzinfo is None:
                    end_bound = end_bound.tz_localize(index.tz)
                else:
                    end_bound = end_bound.tz_convert(index.tz)
                frame = frame[(index >= start_bound) & (index <= end_bound)]
            else:
                start_bound = pd.Timestamp(start).tz_localize(None)
                end_bound = pd.Timestamp(end).tz_localize(None)
                frame = frame[
                    (pd.DatetimeIndex(frame.index) >= start_bound)
                    & (pd.DatetimeIndex(frame.index) <= end_bound)
                ]
        except Exception:
            # Keep the provider frame when timestamp clipping cannot be
            # normalized; the conversion layer below remains defensive.
            pass

        # For a 1D intraday stock chart, a weekend/holiday should show
        # the latest complete trading session rather than an empty/partial
        # chart. Crypto stays continuous and is kept as a rolling time window.
        if intraday and asset_type.upper() in {"EQUITY", "STOCK", "ETF", "INDEX"}:
            try:
                provider_frame = history.dropna(
                    subset=["Open", "High", "Low", "Close"],
                    how="all",
                )
                if not provider_frame.empty and (end - start).total_seconds() <= 36 * 3600:
                    latest_session_date = provider_frame.index[-1].date()
                    frame = provider_frame[
                        pd.DatetimeIndex(provider_frame.index).date
                        == latest_session_date
                    ]
            except Exception:
                pass

        # If the exact clipping window had no data, fall back to the latest
        # available stock session so a closed market remains chartable.
        if frame.empty and intraday and asset_type.upper() in {"EQUITY", "STOCK", "ETF", "INDEX"}:
            try:
                provider_frame = history.dropna(
                    subset=["Open", "High", "Low", "Close"],
                    how="all",
                )
                if not provider_frame.empty:
                    latest_session_date = provider_frame.index[-1].date()
                    frame = provider_frame[
                        pd.DatetimeIndex(provider_frame.index).date
                        == latest_session_date
                    ]
            except Exception:
                frame = history

        if frame.empty:
            return []

        bars: List[MarketBar] = []

        for timestamp, row in frame.iterrows():
            open_value = self._clean_number(row.get("Open"))
            high_value = self._clean_number(row.get("High"))
            low_value = self._clean_number(row.get("Low"))
            close_value = self._clean_number(row.get("Close"))

            if any(
                value is None
                for value in (
                    open_value,
                    high_value,
                    low_value,
                    close_value,
                )
            ):
                continue

            bars.append(
                MarketBar(
                    symbol=symbol,
                    timestamp=self._clean_timestamp(timestamp),
                    open=open_value,
                    high=high_value,
                    low=low_value,
                    close=close_value,
                    volume=self._clean_number(
                        row.get("Volume")
                    ),
                    source=self.provider_id,
                )
            )

        return bars
