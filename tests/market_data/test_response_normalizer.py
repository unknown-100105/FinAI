from market_data.response_normalizer import (
    normalize_market_result,
)


def test_quote_normalization():
    source = {
        "operations": ["QUOTE"],
        "planning_reason": "quote_request",
        "results": [
            {
                "operation": "MARKET_QUOTE",
                "instrument": {
                    "instrument_id": "NSE:NIFTY50",
                    "display_name": "NIFTY 50",
                    "asset_type": "index",
                    "exchange": "NSE",
                    "currency": "INR",
                },
                "result": {
                    "observed_price": 22421.95,
                    "latest_session_close": None,
                    "source": "yfinance",
                    "timestamp": "2026-10-01T00:00:00+05:30",
                    "data_status": "partial",
                },
            }
        ],
    }

    result = normalize_market_result(source)

    assert result["operations"] == ["QUOTE"]
    assert result["instrument"]["instrument_id"] == "NSE:NIFTY50"
    assert result["data"][0]["result"]["observed_price"] == 22421.95
    assert result["data"][0]["result"]["latest_session_close"] is None
    assert result["source"] == "yfinance"
    assert result["timestamp"] == "2026-10-01T00:00:00+05:30"


def test_historical_range_is_preserved():
    source = {
        "operations": ["HISTORY"],
        "planning_reason": "history_request",
        "date_range_reason": "7_days",
        "range": {
            "start": "2026-09-25T00:00:00",
            "end": "2026-10-02T00:00:00",
        },
        "results": [],
    }

    result = normalize_market_result(source)

    assert result["date_range_reason"] == "7_days"
    assert result["range"]["start"] == "2026-09-25T00:00:00"


def test_missing_values_are_not_invented():
    source = {
        "operations": ["QUOTE"],
        "results": [
            {
                "operation": "MARKET_QUOTE",
                "instrument": {
                    "instrument_id": "NSE:NIFTY50",
                    "display_name": "NIFTY 50",
                },
                "result": {
                    "observed_price": 22421.95,
                    "latest_session_close": None,
                    "high": None,
                    "low": None,
                    "source": "yfinance",
                    "timestamp": None,
                },
            }
        ],
    }

    result = normalize_market_result(source)

    quote = result["data"][0]["result"]

    assert quote["observed_price"] == 22421.95
    assert quote["latest_session_close"] is None
    assert quote["high"] is None
    assert quote["low"] is None


def test_analytics_result_is_preserved():
    source = {
        "operations": ["ANALYTICS"],
        "results": [
            {
                "operation": "MARKET_ANALYTICS",
                "instrument": {
                    "instrument_id": "NSE:NIFTY50",
                    "display_name": "NIFTY 50",
                },
                "result": {
                    "latest_close": 22620.45,
                    "cumulative_return": -0.004,
                    "annualized_volatility": 0.127,
                    "maximum_drawdown": -0.087,
                    "rsi_14": 25.28,
                    "source": "yfinance",
                    "timestamp": "2026-10-02T00:00:00+05:30",
                },
            }
        ],
    }

    result = normalize_market_result(source)

    analytics = result["data"][0]["result"]

    assert analytics["latest_close"] == 22620.45
    assert analytics["rsi_14"] == 25.28
    assert analytics["annualized_volatility"] == 0.127
