from datetime import datetime
from fastapi.testclient import TestClient

from app.main import app
from market_data.models import MarketQuote


def make_fake_quote():
    return MarketQuote(
        symbol="NIFTY 50",
        asset_type="index",
        exchange="NSE",
        price=25000.0,
        open=24900.0,
        high=25100.0,
        low=24800.0,
        close=25000.0,
        volume=1000000.0,
        currency="INR",
        timestamp=datetime(2026, 9, 30),
        source="test",
    )

class FakeService:
    default_provider = "test"
    providers = {"test": object()}

    def quote(self, **kwargs):
        return make_fake_quote()

    def history(self, **kwargs):
        return []


def test_market_quote_endpoint(monkeypatch):
    monkeypatch.setattr(
        "app.main.get_market_data_service",
        lambda: FakeService(),
    )

    client = TestClient(app)

    response = client.get(
        "/api/v1/market/quote",
        params={"instrument": "nifty 50"},
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["instrument"]["instrument_id"] == "NSE:NIFTY50"
    assert payload["instrument"]["display_name"] == "NIFTY 50"
    assert payload["quote"]["price"] == 25000.0
    assert payload["quote"]["source"] == "test"


def test_unknown_instrument():
    client = TestClient(app)

    response = client.get(
        "/api/v1/market/quote",
        params={"instrument": "unknown instrument"},
    )

    assert response.status_code == 404


def test_history_reversed_dates():
    client = TestClient(app)

    response = client.get(
        "/api/v1/market/history",
        params={
            "instrument": "nifty",
            "start": "2026-10-01T00:00:00",
            "end": "2026-09-01T00:00:00",
        },
    )

    assert response.status_code == 422

