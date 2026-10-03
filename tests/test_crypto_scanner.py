from unittest.mock import patch


def test_scanner_uses_orderbook_best_bid_ask():
    from crypto.scanner import scan_cross_exchange_arbitrage

    fake = {
        "exchange": "a",
        "symbol": "BTC/USDT",
        "best_bid": 101.0,
        "best_bid_amount": 5.0,
        "best_ask": 102.0,
        "best_ask_amount": 5.0,
        "timestamp": 1,
        "fetched_at": "2026-10-03T00:00:00+00:00",
    }

    fake_b = {**fake, "exchange": "b", "best_bid": 104.0, "best_ask": 103.0}

    with patch("crypto.scanner.fetch_orderbook_snapshot", side_effect=[fake, fake_b]):
        result = scan_cross_exchange_arbitrage(
            exchanges=("a", "b"),
            capital_quote=1000,
        )

    assert len(result["opportunities"]) == 2
    assert result["opportunities"][0]["sell_venue"] == "b"
    assert result["opportunities"][0]["net_profit_quote"] > 0
