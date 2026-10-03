from market_data.discovery import normalize_search_result


def test_normalize_equity_search_result():
    result = normalize_search_result(
        {
            "symbol": "AAPL",
            "shortname": "Apple Inc.",
            "quoteType": "EQUITY",
            "exchange": "NMS",
            "currency": "USD",
        }
    )

    assert result["symbol"] == "AAPL"
    assert result["asset_type"] == "equity"
    assert result["exchange"] == "NMS"


def test_normalize_crypto_search_result():
    result = normalize_search_result(
        {
            "symbol": "BTC-USD",
            "longname": "Bitcoin USD",
            "quoteType": "CRYPTOCURRENCY",
            "currency": "USD",
        }
    )

    assert result["asset_type"] == "cryptocurrency"


def test_normalize_ignores_missing_symbol():
    assert normalize_search_result({"longname": "Unknown"}) is None
