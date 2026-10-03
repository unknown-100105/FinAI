from datetime import datetime
from typing import Any
from fastapi import APIRouter, HTTPException, Query
from market_data.analyst import analyze_candles
from app.market_api import _get_service, _resolve_instrument_or_search
from market_data.news import fetch_news

router = APIRouter(prefix="/api/v1/market", tags=["market-analysis"])

@router.get("/analyst")
def analyst(
    instrument: str = Query(..., min_length=1),
    start: datetime = Query(...),
    end: datetime = Query(...),
    interval: str = Query(default="15m", pattern="^(1m|2m|5m|15m|30m|60m|90m|1h|1d|5d|1wk|1mo|3mo)$"),
    news_count: int = Query(default=8, ge=0, le=15),
) -> dict[str, Any]:
    if start > end:
        raise HTTPException(status_code=422, detail="start must not be after end.")
    item = _resolve_instrument_or_search(instrument)
    try:
        bars = _get_service().history(
            symbol=item.display_name, asset_type=item.asset_type, exchange=item.exchange,
            start=start, end=end, provider_id="yfinance", interval=interval,
        )
        articles = [dict(article) for article in fetch_news(query=item.display_name, count=news_count)]
        return {
            "instrument": {
                "instrument_id": item.instrument_id, "display_name": item.display_name,
                "asset_type": item.asset_type, "exchange": item.exchange, "currency": item.currency,
            },
            "range": {"start": start, "end": end},
            "interval": interval,
            "analysis": analyze_candles(bars, articles),
            "news": articles,
            "source": "yfinance + FinAI candle analytics",
            "causality_note": "News items are contextual evidence candidates; they do not prove that a particular headline caused a particular candle.",
        }
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Market analysis failed: {exc}") from exc
