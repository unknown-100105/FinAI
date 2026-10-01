from datetime import datetime
from typing import Dict, List, Optional

from .base import MarketDataProvider
from .models import MarketBar, MarketQuote


class MarketDataService:
    """Provider-independent market data service."""

    def __init__(
        self,
        providers: Optional[Dict[str, MarketDataProvider]] = None,
        default_provider: Optional[str] = None,
    ):
        self.providers: Dict[str, MarketDataProvider] = (
            dict(providers or {})
        )

        if default_provider is not None:
            self.default_provider = str(
                default_provider
            ).strip().lower()
        else:
            self.default_provider = (
                next(iter(self.providers), None)
            )

    def register_provider(
        self,
        provider: MarketDataProvider,
    ) -> None:
        provider_id = str(
            provider.provider_id
        ).strip().lower()

        if not provider_id:
            raise ValueError(
                "Provider must define a non-empty provider_id."
            )

        self.providers[provider_id] = provider

        if self.default_provider is None:
            self.default_provider = provider_id

    def get_provider(
        self,
        provider_id: Optional[str] = None,
    ) -> MarketDataProvider:
        selected = (
            str(provider_id).strip().lower()
            if provider_id is not None
            else self.default_provider
        )

        if not selected:
            raise ValueError(
                "No market-data provider is configured."
            )

        if selected not in self.providers:
            available = ", ".join(
                sorted(self.providers.keys())
            )

            raise ValueError(
                f"Market-data provider '{selected}' "
                f"is not registered. "
                f"Available: {available or 'none'}"
            )

        return self.providers[selected]

    def quote(
        self,
        symbol: str,
        asset_type: str,
        exchange: Optional[str] = None,
        provider_id: Optional[str] = None,
    ) -> MarketQuote:
        provider = self.get_provider(provider_id)

        return provider.get_quote(
            symbol=symbol,
            asset_type=asset_type,
            exchange=exchange,
        )

    def history(
        self,
        symbol: str,
        asset_type: str,
        start: datetime,
        end: datetime,
        exchange: Optional[str] = None,
        provider_id: Optional[str] = None,
    ) -> List[MarketBar]:
        if start > end:
            raise ValueError(
                "History start must not be after history end."
            )

        provider = self.get_provider(provider_id)

        return provider.get_history(
            symbol=symbol,
            asset_type=asset_type,
            start=start,
            end=end,
            exchange=exchange,
        )
