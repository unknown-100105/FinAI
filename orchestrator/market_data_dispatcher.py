from datetime import datetime
from typing import Any, Dict

from market_data.analytics import calculate_market_analytics
from market_data.resolver import InstrumentResolver
from market_data.service import MarketDataService


class MarketDataDispatcher:
    """
    Executes read-only market-data operations through the
    provider-independent MarketDataService.
    """

    def __init__(
        self,
        market_data_service: MarketDataService,
        resolver: InstrumentResolver | None = None,
    ):
        self.market_data = market_data_service
        self.resolver = resolver or InstrumentResolver()

    def _resolve(self, instrument: str):
        return self.resolver.resolve_or_raise(instrument)

    @staticmethod
    def _instrument_payload(item) -> Dict[str, Any]:
        return {
            "instrument_id": item.instrument_id,
            "display_name": item.display_name,
            "asset_type": item.asset_type,
            "exchange": item.exchange,
            "currency": item.currency,
        }

    def quote(
        self,
        instrument: str,
        provider_id: str = "yfinance",
    ) -> Dict[str, Any]:
        item = self._resolve(instrument)

        quote = self.market_data.quote(
            symbol=item.display_name,
            asset_type=item.asset_type,
            exchange=item.exchange,
            provider_id=provider_id,
        )

        return {
            "operation": "MARKET_QUOTE",
            "instrument": self._instrument_payload(item),
            "result": {
                "symbol": quote.symbol,
                "price": quote.price,
                "open": quote.open,
                "high": quote.high,
                "low": quote.low,
                "close": quote.close,
                "volume": quote.volume,
                "currency": quote.currency,
                "timestamp": quote.timestamp,
                "source": quote.source,
            },
        }

    def history(
        self,
        instrument: str,
        start: datetime,
        end: datetime,
        provider_id: str = "yfinance",
    ) -> Dict[str, Any]:
        if start > end:
            raise ValueError(
                "History start must not be after history end."
            )

        item = self._resolve(instrument)

        bars = self.market_data.history(
            symbol=item.display_name,
            asset_type=item.asset_type,
            exchange=item.exchange,
            start=start,
            end=end,
            provider_id=provider_id,
        )

        return {
            "operation": "MARKET_HISTORY",
            "instrument": self._instrument_payload(item),
            "range": {
                "start": start,
                "end": end,
            },
            "count": len(bars),
            "result": [
                {
                    "symbol": bar.symbol,
                    "timestamp": bar.timestamp,
                    "open": bar.open,
                    "high": bar.high,
                    "low": bar.low,
                    "close": bar.close,
                    "volume": bar.volume,
                    "source": bar.source,
                }
                for bar in bars
            ],
        }

    def analytics(
        self,
        instrument: str,
        start: datetime,
        end: datetime,
        provider_id: str = "yfinance",
    ) -> Dict[str, Any]:
        if start > end:
            raise ValueError(
                "Analytics start must not be after end."
            )

        item = self._resolve(instrument)

        bars = self.market_data.history(
            symbol=item.display_name,
            asset_type=item.asset_type,
            exchange=item.exchange,
            start=start,
            end=end,
            provider_id=provider_id,
        )

        calculated = calculate_market_analytics(bars)

        return {
            "operation": "MARKET_ANALYTICS",
            "instrument": self._instrument_payload(item),
            "range": {
                "start": start,
                "end": end,
            },
            "data_points": len(bars),
            "result": {
                "symbol": calculated.symbol,
                "observations": calculated.observations,
                "latest_close": calculated.latest_close,
                "cumulative_return": calculated.cumulative_return,
                "annualized_volatility": calculated.annualized_volatility,
                "maximum_drawdown": calculated.maximum_drawdown,
                "sma_20": calculated.sma_20,
                "sma_50": calculated.sma_50,
                "ema_20": calculated.ema_20,
                "rsi_14": calculated.rsi_14,
            },
        }
