from datetime import datetime

from market_data.models import MarketBar, MarketQuote
from market_data.service import MarketDataService
from orchestrator.market_data_dispatcher import MarketDataDispatcher


class FakeProvider:
    provider_id = "test"

    def get_quote(self, symbol, asset_type, exchange=None):
        return MarketQuote(
            symbol=symbol,
            asset_type=asset_type,
            exchange=exchange,
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

    def get_history(
        self,
        symbol,
        asset_type,
        start,
        end,
        exchange=None,
    ):
        return [
            MarketBar(
                symbol=symbol,
                timestamp=datetime(2026, 9, 29),
                open=100.0,
                high=105.0,
                low=95.0,
                close=102.0,
                volume=1000.0,
                source="test",
            ),
            MarketBar(
                symbol=symbol,
                timestamp=datetime(2026, 9, 30),
                open=102.0,
                high=110.0,
                low=101.0,
                close=108.0,
                volume=1200.0,
                source="test",
            ),
        ]


def make_dispatcher():
    service = MarketDataService(
        providers={"test": FakeProvider()},
        default_provider="test",
    )

    return MarketDataDispatcher(service)


def test_quote_dispatch():
    dispatcher = make_dispatcher()

    result = dispatcher.quote(
        "nifty 50",
        provider_id="test",
    )

    assert result["operation"] == "MARKET_QUOTE"
    assert result["instrument"]["instrument_id"] == "NSE:NIFTY50"
    assert result["result"]["price"] == 25000.0
    assert result["result"]["source"] == "test"


def test_history_dispatch():
    dispatcher = make_dispatcher()

    result = dispatcher.history(
        "nifty",
        start=datetime(2026, 9, 1),
        end=datetime(2026, 10, 1),
        provider_id="test",
    )

    assert result["operation"] == "MARKET_HISTORY"
    assert result["count"] == 2
    assert result["result"][1]["close"] == 108.0


def test_analytics_dispatch():
    dispatcher = make_dispatcher()

    result = dispatcher.analytics(
        "nifty",
        start=datetime(2026, 9, 1),
        end=datetime(2026, 10, 1),
        provider_id="test",
    )

    assert result["operation"] == "MARKET_ANALYTICS"
    assert result["data_points"] == 2
    assert result["result"]["latest_close"] == 108.0


def test_unknown_instrument():
    dispatcher = make_dispatcher()

    try:
        dispatcher.quote(
            "not a real instrument",
            provider_id="test",
        )
    except ValueError as exc:
        assert "Unknown financial instrument" in str(exc)
    else:
        raise AssertionError(
            "Unknown instrument should raise ValueError."
        )


def test_reversed_history_range():
    dispatcher = make_dispatcher()

    try:
        dispatcher.history(
            "nifty",
            start=datetime(2026, 10, 1),
            end=datetime(2026, 9, 1),
            provider_id="test",
        )
    except ValueError as exc:
        assert "must not be after" in str(exc)
    else:
        raise AssertionError(
            "Reversed range should raise ValueError."
        )
