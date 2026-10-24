from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import Mock

import pytest
from fastapi.testclient import TestClient

import app.main as main_module
from app.main import app
from app import market_api
from market_data.instruments import Instrument
from market_data.models import MarketQuote


client = TestClient(app)


def test_market_provider_discovery_lists_only_registered_providers(monkeypatch):
    fake_service = SimpleNamespace(
        default_provider="yfinance",
        providers={"yfinance": object(), "longbridge": object()},
    )
    monkeypatch.setattr(market_api, "_get_service", lambda: fake_service)

    response = client.get("/api/v1/market/providers")

    assert response.status_code == 200
    body = response.json()
    assert body["default_provider"] == "yfinance"
    assert [item["provider_id"] for item in body["providers"]] == ["longbridge", "yfinance"]
    assert all(item["configured"] is True for item in body["providers"])


def test_quote_routes_explicit_provider_to_market_service(monkeypatch):
    instrument = Instrument(
        instrument_id="NASDAQ:AAPL",
        display_name="AAPL",
        asset_type="equity",
        exchange="NASDAQ",
        currency="USD",
        aliases=("aapl",),
        provider_symbols={},
    )
    fake_quote = MarketQuote(
        symbol="AAPL",
        asset_type="equity",
        exchange="NASDAQ",
        price=100.0,
        open=99.0,
        high=101.0,
        low=98.0,
        close=99.5,
        volume=1000,
        currency="USD",
        timestamp=datetime(2026, 1, 2, tzinfo=timezone.utc),
        source="longbridge",
    )
    fake_service = SimpleNamespace(quote=Mock(return_value=fake_quote))
    monkeypatch.setattr(market_api, "_resolve_instrument_or_search", lambda _: instrument)
    monkeypatch.setattr(market_api, "_get_service", lambda: fake_service)

    response = client.get("/api/v1/market/quote?instrument=AAPL&provider=longbridge")

    assert response.status_code == 200
    assert response.json()["quote"]["source"] == "longbridge"
    assert fake_service.quote.call_args.kwargs["provider_id"] == "longbridge"


def test_longbridge_rejects_known_indian_exchange_instruments(monkeypatch):
    monkeypatch.setattr(
        market_api,
        "_resolve_instrument_or_search",
        lambda _: Instrument(
            instrument_id="NSE:TCS",
            display_name="TCS",
            asset_type="equity",
            exchange="NSE",
            currency="INR",
            aliases=("tcs",),
            provider_symbols={},
        ),
    )
    service = SimpleNamespace(quote=Mock(side_effect=AssertionError("provider should not be invoked")))
    monkeypatch.setattr(market_api, "_get_service", lambda: service)

    response = client.get("/api/v1/market/quote?instrument=TCS&provider=longbridge")

    assert response.status_code == 422
    assert "NSE/BSE" in response.json()["detail"]
    service.quote.assert_not_called()


def test_longbridge_provider_is_registered_only_when_credentials_exist(monkeypatch):
    monkeypatch.setattr(main_module, "_market_data_service", None)
    monkeypatch.delenv("LONGBRIDGE_APP_KEY", raising=False)
    monkeypatch.delenv("LONGBRIDGE_APP_SECRET", raising=False)
    monkeypatch.delenv("LONGBRIDGE_ACCESS_TOKEN", raising=False)

    without_credentials = main_module.get_market_data_service()
    assert "yfinance" in without_credentials.providers
    assert "longbridge" not in without_credentials.providers

    monkeypatch.setattr(main_module, "_market_data_service", None)
    monkeypatch.setenv("LONGBRIDGE_APP_KEY", "test-app-key")
    monkeypatch.setenv("LONGBRIDGE_APP_SECRET", "test-app-secret")
    monkeypatch.setenv("LONGBRIDGE_ACCESS_TOKEN", "test-access-token")

    with_credentials = main_module.get_market_data_service()
    assert "yfinance" in with_credentials.providers
    assert "longbridge" in with_credentials.providers
    # Provider construction is lazy: registration must not initialize SDK/network.
