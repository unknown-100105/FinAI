from abc import ABC, abstractmethod
from datetime import datetime
from typing import List, Optional

from .models import MarketBar, MarketQuote


class MarketDataProvider(ABC):
    """Common interface for current and historical market data."""

    provider_id: str = "unknown"

    @abstractmethod
    def get_quote(
        self,
        symbol: str,
        asset_type: str,
        exchange: Optional[str] = None,
    ) -> MarketQuote:
        raise NotImplementedError

    @abstractmethod
    def get_history(
        self,
        symbol: str,
        asset_type: str,
        start: datetime,
        end: datetime,
        exchange: Optional[str] = None,
    ) -> List[MarketBar]:
        raise NotImplementedError
