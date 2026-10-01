from dataclasses import dataclass
from typing import Tuple


OP_QUOTE = "QUOTE"
OP_HISTORY = "HISTORY"
OP_ANALYTICS = "ANALYTICS"


@dataclass(frozen=True)
class MarketOperationPlan:
    operations: Tuple[str, ...]
    reason: str


ANALYTICS_TERMS = (
    "volatility",
    "rsi",
    "moving average",
    "moving averages",
    "sma",
    "ema",
    "drawdown",
    "return",
    "returns",
    "performance",
)

HISTORY_TERMS = (
    "history",
    "historical",
    "past",
    "previous",
    "last",
    "over the last",
    "for the last",
    "price history",
)


def plan_market_operations(text: str) -> MarketOperationPlan:
    normalized = " ".join(
        str(text).strip().lower().split()
    )

    if not normalized:
        return MarketOperationPlan(
            operations=(OP_QUOTE,),
            reason="empty_or_default_quote",
        )

    wants_analytics = any(
        term in normalized
        for term in ANALYTICS_TERMS
    )

    wants_history = any(
        term in normalized
        for term in HISTORY_TERMS
    )

    if wants_analytics and wants_history:
        return MarketOperationPlan(
            operations=(OP_HISTORY, OP_ANALYTICS),
            reason="history_and_analytics",
        )

    if wants_analytics:
        return MarketOperationPlan(
            operations=(OP_ANALYTICS,),
            reason="analytics_request",
        )

    if wants_history:
        return MarketOperationPlan(
            operations=(OP_HISTORY,),
            reason="history_request",
        )

    return MarketOperationPlan(
        operations=(OP_QUOTE,),
        reason="quote_request",
    )
