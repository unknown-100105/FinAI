"""Order-book and microstructure feature adapter for the multimodal graph."""
from __future__ import annotations

from typing import Any, Mapping, Sequence

import numpy as np


def summarize_order_book(snapshot: Mapping[str, Any]) -> dict[str, Any]:
    """Convert a normalized order-book snapshot into finite research features."""
    bids = snapshot.get("bids", [])
    asks = snapshot.get("asks", [])
    if not bids or not asks:
        raise ValueError("order book requires non-empty bids and asks")

    def clean(levels: Sequence[Sequence[float]]) -> np.ndarray:
        values = np.asarray(levels, dtype=float)
        if values.ndim != 2 or values.shape[1] < 2:
            raise ValueError("order-book levels must be [price, quantity]")
        values = values[:, :2]
        if not np.isfinite(values).all():
            raise ValueError("order-book levels must be finite")
        if np.any(values[:, 0] <= 0) or np.any(values[:, 1] < 0):
            raise ValueError("prices must be positive and quantities non-negative")
        return values

    bid = clean(bids)
    ask = clean(asks)
    best_bid = float(np.max(bid[:, 0]))
    best_ask = float(np.min(ask[:, 0]))
    if best_ask < best_bid:
        raise ValueError("best ask cannot be below best bid")

    mid = (best_bid + best_ask) / 2.0
    spread = (best_ask - best_bid) / max(mid, 1e-12)
    bid_depth = float(np.sum(bid[:, 1]))
    ask_depth = float(np.sum(ask[:, 1]))
    imbalance = (bid_depth - ask_depth) / max(bid_depth + ask_depth, 1e-12)
    return {
        "status": "MICROSTRUCTURE_FEATURES_READY",
        "mid_price": round(mid, 8),
        "relative_spread": round(spread, 8),
        "bid_depth": round(bid_depth, 8),
        "ask_depth": round(ask_depth, 8),
        "order_book_imbalance": round(imbalance, 8),
        "semantics": "Descriptive order-book features for multimodal research; they are not trade recommendations or causal effects.",
    }
