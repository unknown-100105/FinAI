from orchestrator.hybrid_engine import FinAIHybridEngine


class FakeBaseEngine:
    def process(self, **kwargs):
        return {
            "router": {
                "intent": "UNKNOWN",
                "decision": "UNKNOWN",
                "confidence": 0.0,
                "margin": 0.0,
            },
            "status": "UNKNOWN",
            "stage": "router",
            "message": "base result",
            "response": "base result",
        }


class FakeMarketDispatcher:
    def __init__(self):
        self.resolver = FakeResolver()

    def quote(self, instrument, provider_id="yfinance"):
        return {
            "operation": "MARKET_QUOTE",
            "instrument": {
                "instrument_id": "NSE:NIFTY50",
                "display_name": "NIFTY 50",
                "asset_type": "index",
                "exchange": "NSE",
                "currency": "INR",
            },
            "result": {
                "observed_price": 25000.0,
                "latest_session_close": 25000.0,
                "data_status": "complete",
                "source": "test",
            },
        }


class FakeResolver:
    class FakeInstrument:
        aliases = ("nifty", "nifty 50", "nifty50")
        display_name = "NIFTY 50"
        instrument_id = "NSE:NIFTY50"

    instruments = (FakeInstrument(),)


def test_market_data_execution():
    engine = FinAIHybridEngine()
    engine.base_engine = FakeBaseEngine()
    engine.market_data = FakeMarketDispatcher()

    result = engine.process(
        user_text="What is NIFTY 50 today?",
        generate_response=False,
    )

    assert result["stage"] == "market_data"
    assert result["status"] == "MARKET_DATA_RETRIEVED"
    assert result["router"]["domain"] == "MARKET_DATA"
    assert result["router"]["intent"] == "MARKET_DATA_QUERY"
    assert result["router"]["decision"] == "ROUTE"
    assert result["execution_plan"]["capability"] == "market_data"
    assert result["market_data"]["operations"] == ["QUOTE"]
    assert result["market_data"]["results"][0]["operation"] == "MARKET_QUOTE"
    assert result["market_data"]["results"][0]["result"]["observed_price"] == 25000.0



