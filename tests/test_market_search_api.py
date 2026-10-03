from unittest.mock import patch

from fastapi.testclient import TestClient

from app.main import app


def test_market_search_endpoint():
    fake_results = [
        {
            "symbol": "ABC.NS",
            "name": "Example Corp",
            "asset_type": "equity",
            "quote_type": "EQUITY",
            "exchange": "NSE",
            "exchange_full_name": "NSE",
            "currency": "INR",
            "score": 10,
            "provider": "yfinance",
        }
    ]

    with patch(
        "market_data.discovery.search_instruments",
        return_value=fake_results,
    ):
        response = TestClient(app).get(
            "/api/v1/market/search?query=Example"
        )

    assert response.status_code == 200
    assert response.json()["results"][0]["symbol"] == "ABC.NS"
