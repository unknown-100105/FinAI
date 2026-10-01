from dataclasses import dataclass
from typing import Dict, Optional, Tuple


@dataclass(frozen=True)
class Instrument:
    """Canonical identity of a financial market instrument."""

    instrument_id: str
    display_name: str
    asset_type: str
    exchange: Optional[str]
    currency: Optional[str]
    aliases: Tuple[str, ...]
    provider_symbols: Dict[str, str]


INSTRUMENTS = (
    Instrument(
        instrument_id="NSE:NIFTY50",
        display_name="NIFTY 50",
        asset_type="index",
        exchange="NSE",
        currency="INR",
        aliases=(
            "nifty",
            "nifty 50",
            "nifty50",
        ),
        provider_symbols={},
    ),
    Instrument(
        instrument_id="BSE:SENSEX",
        display_name="SENSEX",
        asset_type="index",
        exchange="BSE",
        currency="INR",
        aliases=(
            "sensex",
            "bse sensex",
        ),
        provider_symbols={},
    ),
    Instrument(
        instrument_id="FX:USDINR",
        display_name="USD/INR",
        asset_type="forex",
        exchange=None,
        currency="INR",
        aliases=(
            "usd inr",
            "usd/inr",
            "usd to inr",
            "dollar inr",
            "dollar to rupee",
            "dollar rupee",
        ),
        provider_symbols={},
    ),
    Instrument(
        instrument_id="FX:EURINR",
        display_name="EUR/INR",
        asset_type="forex",
        exchange=None,
        currency="INR",
        aliases=(
            "eur inr",
            "eur/inr",
            "eur to inr",
        ),
        provider_symbols={},
    ),
    Instrument(
        instrument_id="CRYPTO:BTC",
        display_name="Bitcoin",
        asset_type="crypto",
        exchange=None,
        currency="USD",
        aliases=(
            "bitcoin",
            "btc",
        ),
        provider_symbols={},
    ),
    Instrument(
        instrument_id="CRYPTO:ETH",
        display_name="Ethereum",
        asset_type="crypto",
        exchange=None,
        currency="USD",
        aliases=(
            "ethereum",
            "eth",
        ),
        provider_symbols={},
    ),
    Instrument(
        instrument_id="COMMODITY:GOLD",
        display_name="Gold",
        asset_type="commodity",
        exchange=None,
        currency="INR",
        aliases=(
            "gold",
            "gold price",
        ),
        provider_symbols={},
    ),
    Instrument(
        instrument_id="COMMODITY:SILVER",
        display_name="Silver",
        asset_type="commodity",
        exchange=None,
        currency="INR",
        aliases=(
            "silver",
            "silver price",
        ),
        provider_symbols={},
    ),
)


def all_instruments() -> Tuple[Instrument, ...]:
    return INSTRUMENTS
