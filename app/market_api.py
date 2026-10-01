from dataclasses import asdict
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, HTTPException, Query

from market_data.analytics import calculate_market_analytics
from market_data.resolver import InstrumentResolver


router = APIRouter(
    prefix="/api/v1/market",
    tags=["market-data"],
)

_resolver = InstrumentResolver()


def _get_service():
    """
    Resolve the shared MarketDataService lazily.

    Importing inside the function avoids a circular import between
    app.main and this router module.
    """
    from app.main import get_market_data_service

    return get_market_data_service()


def _resolve_instrument(instrument: str):
    try:
        return _resolver.resolve_or_raise(instrument)
    except ValueError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc


@router.get("/quote")
def quote(
    instrument: str = Query(
        ...,
        min_length=1,
        description="Instrument name, alias, or supported market identifier.",
    ),
):
    item = _resolve_instrument(instrument)

    try:
        result = _get_service().quote(
            symbol=item.display_name,
            asset_type=item.asset_type,
            exchange=item.exchange,
            provider_id="yfinance",
        )
    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Market quote retrieval failed: {exc}",
        ) from exc

    return {
        "instrument": {
            "instrument_id": item.instrument_id,
            "display_name": item.display_name,
            "asset_type": item.asset_type,
            "exchange": item.exchange,
            "currency": item.currency,
        },
        "quote": asdict(result),
    }


@router.get("/history")
def history(
    instrument: str = Query(
        ...,
        min_length=1,
    ),
    start: datetime = Query(
        ...,
        description="Start datetime in ISO-8601 format.",
    ),
    end: datetime = Query(
        ...,
        description="End datetime in ISO-8601 format.",
    ),
):
    if start > end:
        raise HTTPException(
            status_code=422,
            detail="start must not be after end.",
        )

    item = _resolve_instrument(instrument)

    try:
        bars = _get_service().history(
            symbol=item.display_name,
            asset_type=item.asset_type,
            exchange=item.exchange,
            start=start,
            end=end,
            provider_id="yfinance",
        )
    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Market history retrieval failed: {exc}",
        ) from exc

    return {
        "instrument": {
            "instrument_id": item.instrument_id,
            "display_name": item.display_name,
            "asset_type": item.asset_type,
            "exchange": item.exchange,
            "currency": item.currency,
        },
        "range": {
            "start": start,
            "end": end,
        },
        "count": len(bars),
        "bars": [asdict(bar) for bar in bars],
    }


@router.get("/analytics")
def analytics(
    instrument: str = Query(
        ...,
        min_length=1,
    ),
    start: datetime = Query(
        ...,
    ),
    end: datetime = Query(
        ...,
    ),
):
    if start > end:
        raise HTTPException(
            status_code=422,
            detail="start must not be after end.",
        )

    item = _resolve_instrument(instrument)

    try:
        bars = _get_service().history(
            symbol=item.display_name,
            asset_type=item.asset_type,
            exchange=item.exchange,
            start=start,
            end=end,
            provider_id="yfinance",
        )
    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Market history retrieval failed: {exc}",
        ) from exc

    calculated = calculate_market_analytics(bars)

    return {
        "instrument": {
            "instrument_id": item.instrument_id,
            "display_name": item.display_name,
            "asset_type": item.asset_type,
            "exchange": item.exchange,
            "currency": item.currency,
        },
        "range": {
            "start": start,
            "end": end,
        },
        "analytics": asdict(calculated),
        "data_points": len(bars),
    }
