"""Build aligned market-return matrices for causal discovery research."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Mapping

import numpy as np
import pandas as pd

from market_data.service import MarketDataService
from market_data.instruments import Instrument
from market_data.resolver import InstrumentResolver


DEFAULT_CAUSAL_PROXIES = {
    "rates": "^TNX",
    "usd": "USD/INR",
    "oil": "BZ=F",
    "supply": "^BDI",
    "credit": "HYG",
}


def build_market_return_dataset(
    service: MarketDataService,
    resolver: InstrumentResolver,
    proxies: Mapping[str, str],
    *,
    days: int = 730,
    interval: str = "1d",
) -> Dict[str, Any]:
    """Fetch proxy histories and return an aligned percentage-return matrix.

    Proxy labels are research variables, not claims that a market series is a
    direct measurement of the underlying economic construct.
    """
    if days < 90 or days > 3650:
        raise ValueError("days must be between 90 and 3650")
    if len(proxies) < 2:
        raise ValueError("at least two causal proxies are required")

    end = datetime.now(timezone.utc)
    start = end - timedelta(days=days)
    series: Dict[str, pd.Series] = {}
    metadata: Dict[str, Any] = {}
    errors: Dict[str, str] = {}

    for node_id, query in proxies.items():
        node = str(node_id).strip()
        if not node:
            raise ValueError("proxy node ids must not be empty")
        try:
            item: Instrument = resolver.resolve(query)
            if item is None:
                from market_data.discovery import search_instruments
                import re
                if not re.fullmatch(r"[A-Za-z0-9.^/_=-]{1,40}", str(query).strip()):
                    raise ValueError(f"unknown market proxy: {query}")
                matches = search_instruments(str(query).strip(), count=5)
                if not matches:
                    raise ValueError(f"unknown market proxy: {query}")
                top = matches[0]
                item = Instrument(
                    instrument_id=f"YF:{top['symbol']}",
                    display_name=top["symbol"],
                    asset_type=top["asset_type"],
                    exchange=top["exchange"],
                    currency=top["currency"],
                    aliases=(str(top["symbol"]).lower(),),
                    provider_symbols={"yfinance": top["symbol"]},
                )

            bars = service.history(
                symbol=item.display_name,
                asset_type=item.asset_type,
                exchange=item.exchange,
                start=start,
                end=end,
                provider_id="yfinance",
                interval=interval,
            )
            if len(bars) < 20:
                raise ValueError(f"insufficient history for {query}: {len(bars)} bars")

            frame = pd.DataFrame(
                {
                    "date": [
                        pd.Timestamp(bar.timestamp).tz_convert(None).normalize()
                        if pd.Timestamp(bar.timestamp).tzinfo is not None
                        else pd.Timestamp(bar.timestamp).normalize()
                        for bar in bars
                    ],
                    "close": [float(bar.close) for bar in bars],
                }
            ).drop_duplicates("date").set_index("date").sort_index()
            returns = frame["close"].pct_change()
            series[node] = returns
            metadata[node] = {
                "query": query,
                "resolved_symbol": item.display_name,
                "asset_type": item.asset_type,
                "exchange": item.exchange,
                "currency": item.currency,
                "bar_count": len(bars),
                "research_note": "Proxy series; economic interpretation requires calibration.",
            }
        except Exception as exc:
            errors[node] = str(exc)

    if len(series) < 2:
        raise ValueError("fewer than two causal proxies returned usable history")

    matrix = pd.concat(series, axis=1).dropna()
    if len(matrix) < 20:
        raise ValueError(f"fewer than 20 aligned return observations: {len(matrix)}")

    values = np.asarray(matrix, dtype=float)
    empirical_correlation = np.corrcoef(values, rowvar=False)
    if np.ndim(empirical_correlation) == 0:
        empirical_correlation = np.asarray([[1.0]])
    return {
        "status": "MARKET_DATASET_READY",
        "interval": interval,
        "lookback_days": days,
        "node_ids": list(matrix.columns),
        "observations": int(len(matrix)),
        "date_range": {
            "start": matrix.index[0].date().isoformat(),
            "end": matrix.index[-1].date().isoformat(),
        },
        "series": metadata,
        "errors": errors,
        "returns": values.tolist(),
        "empirical_correlation": [
            [round(float(value), 6) for value in row]
            for row in np.atleast_2d(empirical_correlation)
        ],
        "data_quality": {
            "aligned_observations": int(len(matrix)),
            "complete_case_fraction": round(
                float(len(matrix) / max(len(pd.concat(series, axis=1)), 1)), 4
            ),
        },
    }
