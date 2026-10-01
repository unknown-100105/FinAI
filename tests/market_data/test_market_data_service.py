from datetime import datetime, timezone

import pytest

from market_data.base import MarketDataProvider
from market_data.models import MarketBar, MarketQuote
from market_data.service import MarketDataService


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


def test_service_registers_provider_and_gets_quote():
    provider = FakeMarketProvider()
    service = MarketDataService()

    service.register_provider(provider)

    result = service.quote(
        symbol="TEST",
        asset_type="stock",
        exchange="NSE",
    )

    assert result.symbol == "TEST"
    assert result.price == 100.0
    assert result.source == "fake"


def test_service_gets_history():
    provider = FakeMarketProvider()
    service = MarketDataService(
        providers={"fake": provider},
        default_provider="fake",
    )

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

    result = service.history(
        symbol="TEST",
        asset_type="stock",
        start=start,
        end=end,
        exchange="NSE",
    )

    assert len(result) == 1
    assert result[0].close == 100.0


def test_unknown_provider_fails():
    service = MarketDataService()

    with pytest.raises(
        ValueError,
        match="No market-data provider",
    ):
        service.quote(
            symbol="TEST",
            asset_type="stock",
        )


def test_unknown_explicit_provider_fails():
    service = MarketDataService(
        providers={"fake": FakeMarketProvider()},
        default_provider="fake",
    )

    with pytest.raises(
        ValueError,
        match="not registered",
    ):
        service.quote(
            symbol="TEST",
            asset_type="stock",
            provider_id="missing",
        )


def test_invalid_history_range_fails():
    service = MarketDataService(
        providers={"fake": FakeMarketProvider()},
        default_provider="fake",
    )

    start = datetime(
        2026,
        1,
        2,
        tzinfo=timezone.utc,
    )

    end = datetime(
        2026,
        1,
        1,
        tzinfo=timezone.utc,
    )

    with pytest.raises(
        ValueError,
        match="start must not be after",
    ):
        service.history(
            symbol="TEST",
            asset_type="stock",
            start=start,
            end=end,
        )
