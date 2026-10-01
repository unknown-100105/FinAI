from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Holding:
    symbol: str
    quantity: float
    price: float
    asset_class: str
    sector: str | None = None

    @property
    def market_value(self) -> float:
        return self.quantity * self.price


@dataclass(frozen=True)
class Portfolio:
    holdings: tuple[Holding, ...]

    @property
    def total_value(self) -> float:
        return sum(h.market_value for h in self.holdings)