from unittest.mock import patch

from fastapi.testclient import TestClient

from app.main import app


def test_crypto_arbitrage_estimate_endpoint():
    client = TestClient(app)

    response = client.post(
        "/api/v1/crypto/arbitrage/estimate",
        json={
            "asset": "BTC/USDT",
            "buy_venue": "a",
            "sell_venue": "b",
            "capital_quote": 1000,
            "buy_price": 100,
            "sell_price": 102,
            "buy_fee_percent": 0.1,
            "sell_fee_percent": 0.1,
            "transfer_cost_quote": 1,
        },
    )

    assert response.status_code == 200
    assert "net_profit_quote" in response.json()


def test_crypto_arbitrage_scan_endpoint():
    fake_a = {
        "exchange": "a",
        "symbol": "BTC/USDT",
        "best_bid": 101.0,
        "best_bid_amount": 5.0,
        "best_ask": 102.0,
        "best_ask_amount": 5.0,
        "timestamp": 1,
        "fetched_at": "2026-10-03T00:00:00+00:00",
    }
    fake_b = {**fake_a, "exchange": "b", "best_bid": 104.0, "best_ask": 103.0}

    with patch(
        "crypto.scanner.fetch_orderbook_snapshot",
        side_effect=[fake_a, fake_b],
    ):
        client = TestClient(app)
        response = client.post(
            "/api/v1/crypto/arbitrage/scan",
            json={
                "symbol": "BTC/USDT",
                "exchanges": ["a", "b"],
                "capital_quote": 1000,
            },
        )

    assert response.status_code == 200
    assert len(response.json()["opportunities"]) == 2
