from dataclasses import asdict
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, HTTPException, Query

from market_data.analytics import calculate_market_analytics
from market_data.resolver import InstrumentResolver
from market_data.instruments import Instrument


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



def _resolve_instrument_or_search(instrument: str):
    try:
        return _resolver.resolve_or_raise(instrument)
    except ValueError:
        from market_data.discovery import search_instruments

        matches = search_instruments(instrument, count=5)
        if not matches:
            raise HTTPException(
                status_code=404,
                detail=f"Unknown financial instrument: {instrument}",
            )

        top = matches[0]
        symbol = top["symbol"]
        return Instrument(
            instrument_id=f"YF:{symbol}",
            display_name=symbol,
            asset_type=top["asset_type"],
            exchange=top["exchange"],
            currency=top["currency"],
            aliases=(symbol.lower(), str(top["name"]).lower()),
            provider_symbols={"yfinance": symbol},
        )



@router.get("/search")
def search(
    query: str = Query(..., min_length=1),
    count: int = Query(default=20, ge=1, le=50),
):
    from market_data.discovery import search_instruments

    try:
        results = search_instruments(query=query, count=count)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    return {
        "query": query.strip(),
        "count": len(results),
        "source": "yfinance",
        "results": results,
    }


@router.get("/quote")
def quote(
    instrument: str = Query(
        ...,
        min_length=1,
        description="Instrument name, alias, or supported market identifier.",
    ),
):
    item = _resolve_instrument_or_search(instrument)

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
    interval: str = Query(
        default="1d",
        pattern="^(1m|2m|5m|15m|30m|60m|90m|1h|1d|5d|1wk|1mo|3mo)$",
        description="OHLCV interval supported by the configured market-data provider.",
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
            interval=interval,
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


@router.get("/news")
def news(
    query: str = Query(
        ...,
        min_length=1,
        description="Company, ticker, sector, or financial-news search query.",
    ),
    count: int = Query(
        default=10,
        ge=1,
        le=25,
    ),
):
    from market_data.news import fetch_news

    try:
        articles = fetch_news(
            query=query,
            count=count,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=422,
            detail=str(exc),
        ) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail=str(exc),
        ) from exc

    return {
        "query": query.strip(),
        "count": len(articles),
        "source": "yfinance",
        "articles": articles,
    }


@router.get("/overview")
def overview():
    from market_data.overview import build_market_overview

    try:
        result = build_market_overview(
            market_data_service=_get_service(),
            resolver=_resolver,
            provider_id="yfinance",
        )
    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Market overview retrieval failed: {exc}",
        ) from exc

    return result
