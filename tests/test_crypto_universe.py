from crypto import universe

def test_supported_connector_registry_is_fiu_snapshot():
    connectors = universe.supported_connectors()
    ids = {item["exchange_id"] for item in connectors}
    assert {"binance", "bybit", "kucoin"} <= ids
    assert all(item["regulatory_status"] == "FIU-IND reporting-entity snapshot" for item in connectors)


def test_scan_all_pairs_ranks_by_net_return(monkeypatch):
    monkeypatch.setattr(
        universe,
        "all_exchange_tickers",
        lambda exchange, quote=None: [
            {"symbol": "BTC/USDT", "bid": 99 if exchange == "buy" else 100, "ask": 100 if exchange == "buy" else 101,
             "last": 100, "bid_volume": 10, "ask_volume": 10, "base_volume": 0, "quote_volume": 0, "timestamp": None}
        ],
    )
    monkeypatch.setitem(universe.PUBLIC_CONNECTOR_MAP, "buy", "Test Buy")
    monkeypatch.setitem(universe.PUBLIC_CONNECTOR_MAP, "sell", "Test Sell")

    result = universe.scan_all_pairs(
        exchanges=("buy", "sell"),
        quote="USDT",
        capital_quote=1000,
        top_n=5,
    )

    assert result["opportunity_count"] == 1
    assert result["opportunities"][0]["asset"] == "BTC/USDT"
