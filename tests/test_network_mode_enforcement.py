"""Offline-mode tests for the direct external market-data adapters."""

from datetime import datetime, timezone
from unittest.mock import patch

import pytest

from crypto import mining, scanner, universe
from market_data.discovery import search_instruments
from market_data.news import fetch_news
from market_data.providers.yfinance_provider import YFinanceProvider
from policy.network_mode import NetworkAccessDisabledError


def test_yfinance_quote_and_history_fail_before_provider_call(monkeypatch):
    monkeypatch.setenv("FINAI_NETWORK_MODE", "offline")
    with patch("market_data.providers.yfinance_provider.yf.Ticker") as ticker:
        provider = YFinanceProvider()
        with pytest.raises(NetworkAccessDisabledError, match="offline mode"):
            provider.get_quote("AAPL", "equity")
        with pytest.raises(NetworkAccessDisabledError, match="offline mode"):
            provider.get_history(
                "AAPL",
                "equity",
                datetime(2026, 1, 1, tzinfo=timezone.utc),
                datetime(2026, 1, 2, tzinfo=timezone.utc),
            )
        ticker.assert_not_called()


def test_yfinance_search_and_news_fail_before_provider_call(monkeypatch):
    monkeypatch.setenv("FINAI_NETWORK_MODE", "offline")
    with patch("market_data.discovery.yf.Search") as discovery_search:
        with pytest.raises(NetworkAccessDisabledError, match="offline mode"):
            search_instruments("NIFTY")
        discovery_search.assert_not_called()
    with patch("market_data.news.yf.Search") as news_search:
        with pytest.raises(NetworkAccessDisabledError, match="offline mode"):
            fetch_news("RBI")
        news_search.assert_not_called()


def test_ccxt_orderbook_scans_fail_before_loading_exchange_client(monkeypatch):
    monkeypatch.setenv("FINAI_NETWORK_MODE", "offline")
    with patch("crypto.scanner._load_ccxt", side_effect=AssertionError("must not load")) as loader:
        with pytest.raises(NetworkAccessDisabledError, match="offline mode"):
            scanner.fetch_orderbook_snapshot("binance", "BTC/USDT")
        loader.assert_not_called()


def test_ccxt_universe_blocks_live_calls_but_allows_a_cached_market_list(monkeypatch):
    monkeypatch.setenv("FINAI_NETWORK_MODE", "offline")
    universe._CACHE.clear()
    with patch("crypto.universe._ccxt", side_effect=AssertionError("must not connect")) as ccxt:
        with pytest.raises(NetworkAccessDisabledError, match="offline mode"):
            universe.market_universe("binance")
        ccxt.assert_not_called()

    universe._cache_set(
        "markets:binance",
        [{"symbol": "BTC/USDT", "base": "BTC", "quote": "USDT", "type": "spot", "active": True}],
    )
    result = universe.market_universe("binance", quote="USDT")
    assert result["count"] == 1
    assert result["pairs"][0]["symbol"] == "BTC/USDT"
    universe._CACHE.clear()


def test_mining_snapshot_request_is_blocked_in_offline_mode(monkeypatch):
    monkeypatch.setenv("FINAI_NETWORK_MODE", "offline")
    with patch("crypto.mining.requests.get") as request:
        with pytest.raises(NetworkAccessDisabledError, match="offline mode"):
            mining._get("/prices")
        request.assert_not_called()


def test_invalid_network_mode_fails_closed(monkeypatch):
    monkeypatch.setenv("FINAI_NETWORK_MODE", "offlien")
    with pytest.raises(ValueError, match="FINAI_NETWORK_MODE"):
        search_instruments("NIFTY")
