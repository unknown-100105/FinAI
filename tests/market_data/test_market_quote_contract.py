from datetime import datetime

from orchestrator.hybrid_engine import FinAIHybridEngine


class FakeBaseEngine:
    def process(self, **kwargs):
        return {
            "router": {
                "intent": "UNKNOWN",
                "decision": "UNKNOWN",
            },
            "status": "UNKNOWN",
        }


class FakeInstrument:
    aliases = ("nifty", "nifty 50", "nifty50")
    display_name = "NIFTY 50"
    instrument_id = "NSE:NIFTY50"


class FakeResolver:
    instruments = (FakeInstrument(),)


class FakeDispatcher:
    def __init__(self):
        self.resolver = FakeResolver()

    def quote(self, instrument, provider_id="yfinance"):
        return {
            "operation": "MARKET_QUOTE",
            "instrument": {
                "instrument_id": "NSE:NIFTY50",
            },
            "result": {
                "observed_price": 25000.0,
                "latest_session_close": None,
                "timestamp": datetime(2026, 10, 1),
                "source": "test",
                "data_status": "partial",
            },
        }


def test_quote_has_no_historical_range():
    engine = FinAIHybridEngine()
    engine.base_engine = FakeBaseEngine()
    engine.market_data = FakeDispatcher()

    result = engine.process(
        "What is NIFTY 50 today?",
        generate_response=False,
    )

    market = result["market_data"]

    assert market["operations"] == ["QUOTE"]
    assert "range" not in market
    assert "date_range_reason" not in market

    quote = market["results"][0]["result"]

    assert quote["observed_price"] == 25000.0
    assert quote["latest_session_close"] is None
    assert quote["data_status"] == "partial"
