import pytest

from market_data.instruments import all_instruments
from market_data.resolver import InstrumentResolver


def test_instrument_catalog_is_not_empty():
    instruments = all_instruments()

    assert len(instruments) >= 8


def test_nifty_aliases_resolve_to_same_instrument():
    resolver = InstrumentResolver()

    first = resolver.resolve("NIFTY")
    second = resolver.resolve("nifty 50")
    third = resolver.resolve("nifty50")

    assert first is not None
    assert first.instrument_id == "NSE:NIFTY50"
    assert second.instrument_id == first.instrument_id
    assert third.instrument_id == first.instrument_id


def test_usd_inr_aliases_resolve():
    resolver = InstrumentResolver()

    for query in (
        "USD INR",
        "USD/INR",
        "USD to INR",
        "Dollar Rupee",
    ):
        result = resolver.resolve(query)

        assert result is not None
        assert result.instrument_id == "FX:USDINR"
        assert result.asset_type == "forex"


def test_crypto_resolution():
    resolver = InstrumentResolver()

    bitcoin = resolver.resolve("Bitcoin")
    btc = resolver.resolve("BTC")

    assert bitcoin is not None
    assert btc is not None
    assert bitcoin.instrument_id == "CRYPTO:BTC"
    assert btc.instrument_id == "CRYPTO:BTC"


def test_commodity_resolution():
    resolver = InstrumentResolver()

    gold = resolver.resolve("gold")
    silver = resolver.resolve("silver")

    assert gold is not None
    assert silver is not None
    assert gold.instrument_id == "COMMODITY:GOLD"
    assert silver.instrument_id == "COMMODITY:SILVER"


def test_unknown_instrument_returns_none():
    resolver = InstrumentResolver()

    result = resolver.resolve(
        "Some Random Company That Does Not Exist"
    )

    assert result is None


def test_unknown_instrument_can_raise():
    resolver = InstrumentResolver()

    with pytest.raises(
        ValueError,
        match="Unknown financial instrument",
    ):
        resolver.resolve_or_raise(
            "Some Random Company That Does Not Exist"
        )
