from datetime import datetime

from orchestrator.hybrid_engine import FinAIHybridEngine
from orchestrator.market_date_parser import MarketDateRange


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


class FakeInstrument:
    aliases = ("nifty", "nifty 50", "nifty50")
    display_name = "NIFTY 50"
    instrument_id = "NSE:NIFTY50"


class FakeResolver:
    instruments = (FakeInstrument(),)


class FakeMarketDispatcher:
    def __init__(self):
        self.resolver = FakeResolver()
        self.history_calls = []
        self.analytics_calls = []
        self.quote_calls = []

    def quote(self, instrument, provider_id="yfinance"):
        self.quote_calls.append(
            {
                "instrument": instrument,
                "provider_id": provider_id,
            }
        )

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
                "price": 25000.0,
                "source": "test",
            },
        }

    def history(
        self,
        instrument,
        start,
        end,
        provider_id="yfinance",
    ):
        self.history_calls.append(
            {
                "instrument": instrument,
                "start": start,
                "end": end,
                "provider_id": provider_id,
            }
        )

        return {
            "operation": "MARKET_HISTORY",
            "instrument": {
                "instrument_id": "NSE:NIFTY50",
            },
            "count": 2,
            "result": [],
        }

    def analytics(
        self,
        instrument,
        start,
        end,
        provider_id="yfinance",
    ):
        self.analytics_calls.append(
            {
                "instrument": instrument,
                "start": start,
                "end": end,
                "provider_id": provider_id,
            }
        )

        return {
            "operation": "MARKET_ANALYTICS",
            "instrument": {
                "instrument_id": "NSE:NIFTY50",
            },
            "data_points": 2,
            "result": {
                "latest_close": 25000.0,
            },
        }


def make_engine():
    engine = FinAIHybridEngine()
    engine.base_engine = FakeBaseEngine()
    engine.market_data = FakeMarketDispatcher()
    return engine


def test_last_7_days_range_reaches_history_dispatcher(monkeypatch):
    fixed_range = MarketDateRange(
        start=datetime(2026, 9, 25, 12, 0, 0),
        end=datetime(2026, 10, 2, 12, 0, 0),
        reason="7_days",
    )

    monkeypatch.setattr(
        "orchestrator.hybrid_engine.parse_market_date_range",
        lambda text: fixed_range,
    )

    engine = make_engine()

    result = engine.process(
        user_text="Show NIFTY 50 for the last 7 days",
        generate_response=False,
    )

    assert result["status"] == "MARKET_DATA_RETRIEVED"
    assert result["market_data"]["operations"] == ["HISTORY"]

    call = engine.market_data.history_calls[0]

    assert call["instrument"] == "NIFTY 50"
    assert call["start"] == fixed_range.start
    assert call["end"] == fixed_range.end


def test_last_6_months_range_reaches_analytics_dispatcher(monkeypatch):
    fixed_range = MarketDateRange(
        start=datetime(2026, 4, 2, 12, 0, 0),
        end=datetime(2026, 10, 2, 12, 0, 0),
        reason="6_months",
    )

    monkeypatch.setattr(
        "orchestrator.hybrid_engine.parse_market_date_range",
        lambda text: fixed_range,
    )

    engine = make_engine()

    result = engine.process(
        user_text="Calculate NIFTY 50 volatility for the last 6 months",
        generate_response=False,
    )

    assert result["status"] == "MARKET_DATA_RETRIEVED"
    assert result["market_data"]["operations"] == ["ANALYTICS"]

    call = engine.market_data.analytics_calls[0]

    assert call["instrument"] == "NIFTY 50"
    assert call["start"] == fixed_range.start
    assert call["end"] == fixed_range.end


def test_history_and_analytics_receive_same_range(monkeypatch):
    fixed_range = MarketDateRange(
        start=datetime(2026, 1, 1),
        end=datetime(2026, 10, 2),
        reason="explicit_date_range",
    )

    monkeypatch.setattr(
        "orchestrator.hybrid_engine.parse_market_date_range",
        lambda text: fixed_range,
    )

    engine = make_engine()

    result = engine.process(
        user_text=(
            "Show NIFTY 50 history from 2026-01-01 "
            "to 2026-10-02 and calculate return"
        ),
        generate_response=False,
    )

    assert result["status"] == "MARKET_DATA_RETRIEVED"
    assert result["market_data"]["operations"] == [
        "HISTORY",
        "ANALYTICS",
    ]

    history_call = engine.market_data.history_calls[0]
    analytics_call = engine.market_data.analytics_calls[0]

    assert history_call["start"] == fixed_range.start
    assert history_call["end"] == fixed_range.end

    assert analytics_call["start"] == fixed_range.start
    assert analytics_call["end"] == fixed_range.end
