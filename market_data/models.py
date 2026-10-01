from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass(frozen=True)
class MarketQuote:
    symbol: str
    asset_type: str
    exchange: Optional[str]
    price: Optional[float]
    open: Optional[float]
    high: Optional[float]
    low: Optional[float]
    close: Optional[float]
    volume: Optional[float]
    currency: Optional[str]
    timestamp: Optional[datetime]
    source: str


@dataclass(frozen=True)
class MarketBar:
    symbol: str
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: Optional[float]
    source: str
