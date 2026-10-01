from datetime import datetime

import pandas as pd
import pytest

from market_data.providers.yfinance_provider import YFinanceProvider


def test_provider_id():
    provider = YFinanceProvider()

    assert provider.provider_id == "yfinance"


def test_resolve_nifty():
    provider = YFinanceProvider()

    assert provider._resolve_symbol(
        "NIFTY50",
        "INDEX",
        "NSE",
    ) == "^NSEI"


def test_resolve_nse_equity():
    provider = YFinanceProvider()

    assert provider._resolve_symbol(
        "RELIANCE",
        "EQUITY",
        "NSE",
    ) == "RELIANCE.NS"


def test_resolve_bse_equity():
    provider = YFinanceProvider()

    assert provider._resolve_symbol(
        "RELIANCE",
        "EQUITY",
        "BSE",
    ) == "RELIANCE.BO"


def test_resolve_forex():
    provider = YFinanceProvider()

    assert provider._resolve_symbol(
        "USDINR",
        "FX",
    ) == "USDINR=X"


def test_resolve_crypto():
    provider = YFinanceProvider()

    assert provider._resolve_symbol(
        "BTC",
        "CRYPTO",
    ) == "BTC-USD"


def test_quote_from_mocked_history(monkeypatch):
    provider = YFinanceProvider()

    history = pd.DataFrame(
        {
            "Open": [100.0],
            "High": [110.0],
            "Low": [95.0],
            "Close": [108.0],
            "Volume": [500000.0],
        },
        index=pd.DatetimeIndex(
            [datetime(2026, 9, 30)]
        ),
    )

    class FakeTicker:
        def __init__(self, symbol):
            self.symbol = symbol

        def history(self, **kwargs):
            return history

        @property
        def fast_info(self):
            return {
                "lastPrice": 109.0,
                "currency": "INR",
            }

    monkeypatch.setattr(
        "market_data.providers.yfinance_provider.yf.Ticker",
        FakeTicker,
    )

    quote = provider.get_quote(
        symbol="RELIANCE",
        asset_type="EQUITY",
        exchange="NSE",
    )

    assert quote.symbol == "RELIANCE"
    assert quote.price == 109.0
    assert quote.open == 100.0
    assert quote.high == 110.0
    assert quote.low == 95.0
    assert quote.close == 108.0
    assert quote.volume == 500000.0
    assert quote.currency == "INR"
    assert quote.source == "yfinance"


def test_history_from_mocked_data(monkeypatch):
    provider = YFinanceProvider()

    history = pd.DataFrame(
        {
            "Open": [100.0, 110.0],
            "High": [105.0, 115.0],
            "Low": [95.0, 108.0],
            "Close": [102.0, 112.0],
            "Volume": [1000.0, 2000.0],
        },
        index=pd.DatetimeIndex(
            [
                datetime(2026, 9, 29),
                datetime(2026, 9, 30),
            ]
        ),
    )

    class FakeTicker:
        def __init__(self, symbol):
            self.symbol = symbol

        def history(self, **kwargs):
            return history

    monkeypatch.setattr(
        "market_data.providers.yfinance_provider.yf.Ticker",
        FakeTicker,
    )

    bars = provider.get_history(
        symbol="RELIANCE",
        asset_type="EQUITY",
        exchange="NSE",
        start=datetime(2026, 9, 1),
        end=datetime(2026, 10, 1),
    )

    assert len(bars) == 2
    assert bars[0].open == 100.0
    assert bars[1].close == 112.0
    assert bars[1].volume == 2000.0
    assert bars[0].source == "yfinance"


def test_history_rejects_reversed_dates():
    provider = YFinanceProvider()

    with pytest.raises(ValueError):
        provider.get_history(
            symbol="RELIANCE",
            asset_type="EQUITY",
            exchange="NSE",
            start=datetime(2026, 10, 1),
            end=datetime(2026, 9, 1),
        )
