from datetime import datetime, timezone

from market_data.base import MarketDataProvider
from market_data.models import MarketBar, MarketQuote


class FakeMarketProvider(MarketDataProvider):
    provider_id = "fake"

    def get_quote(self, symbol, asset_type, exchange=None):
        return MarketQuote(
            symbol=symbol,
            asset_type=asset_type,
            exchange=exchange,
            price=100.0,
            open=98.0,
            high=102.0,
            low=97.0,
            close=100.0,
            volume=100000.0,
            currency="INR",
            timestamp=datetime.now(timezone.utc),
            source=self.provider_id,
        )

    def get_history(self, symbol, asset_type, start, end, exchange=None):
        return [
            MarketBar(
                symbol=symbol,
                timestamp=start,
                open=98.0,
                high=102.0,
                low=97.0,
                close=100.0,
                volume=100000.0,
                source=self.provider_id,
            )
        ]


def test_market_quote_schema():
    provider = FakeMarketProvider()

    quote = provider.get_quote(
        symbol="TEST",
        asset_type="stock",
        exchange="NSE",
    )

    assert quote.symbol == "TEST"
    assert quote.asset_type == "stock"
    assert quote.exchange == "NSE"
    assert quote.price == 100.0
    assert quote.source == "fake"


def test_market_history_schema():
    provider = FakeMarketProvider()

    start = datetime(
        2026,
        1,
        1,
        tzinfo=timezone.utc,
    )

    end = datetime(
        2026,
        1,
        2,
        tzinfo=timezone.utc,
    )

    history = provider.get_history(
        symbol="TEST",
        asset_type="stock",
        start=start,
        end=end,
        exchange="NSE",
    )

    assert len(history) == 1
    assert history[0].symbol == "TEST"
    assert history[0].open == 98.0
    assert history[0].close == 100.0
    assert history[0].source == "fake"
