from datetime import datetime, timezone
from typing import List, Optional

import pandas as pd
import yfinance as yf

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
                progress=False,
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
    ) -> List[MarketBar]:
        if start > end:
            raise ValueError(
                "History start must not be after history end."
            )

        yahoo_symbol = self._resolve_symbol(
            symbol=symbol,
            asset_type=asset_type,
            exchange=exchange,
        )

        ticker = yf.Ticker(yahoo_symbol)

        try:
            history = ticker.history(
                start=start,
                end=end,
                interval="1d",
                auto_adjust=False,
                actions=False,
                progress=False,
            )
        except Exception as exc:
            raise RuntimeError(
                f"yfinance history request failed for "
                f"'{yahoo_symbol}': {exc}"
            ) from exc

        if history is None or history.empty:
            return []

        bars: List[MarketBar] = []

        for timestamp, row in history.iterrows():
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
