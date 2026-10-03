from datetime import datetime
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field
from fastapi import APIRouter, HTTPException, Query
from market_data.analyst import analyze_candles
from market_data.predictor import analyze_market_movement
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


class CandleExplainRequest(BaseModel):
    instrument: str = Field(min_length=1, max_length=64)
    candle: Dict[str, Any]
    context_news: list[Dict[str, Any]] = Field(default_factory=list, max_length=10)
    model_id: Optional[str] = None


@router.post("/analyst/explain")
def explain_candle(request: CandleExplainRequest) -> dict[str, Any]:
    """Generate a model explanation constrained to supplied observed candle data."""
    from llm.response_service import ResponseService

    prompt = (
        f"Explain this selected {request.instrument} candle using ONLY the supplied "
        "observed values. Distinguish facts from hypotheses. Discuss candle anatomy, "
        "volume, recent trend, and contextual news. Do not claim a news item caused "
        "the move unless the supplied evidence explicitly establishes causality. "
        "Do not make a guaranteed prediction. Return a compact analyst note."
    )
    verified = {
        "instrument": request.instrument,
        "selected_candle": request.candle,
        "context_news": request.context_news,
        "constraint": "Use supplied data only; hypotheses must be labelled.",
    }

    try:
        result = ResponseService().generate(
            user_text=prompt,
            intent="FINANCIAL_GUIDANCE",
            verified_result=verified,
            source="market_analyst",
            language="English",
            persona="neutral",
            max_new_tokens=384,
            model_id=request.model_id,
        )
        return {
            "status": result.get("status", "GENERATED"),
            "response": result.get("response", ""),
            "model_id": result.get("model_id"),
            "verification": result.get("verification"),
            "claim_verification": result.get("claim_verification"),
        }
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"Candle explanation unavailable: {exc}") from exc


@router.get("/analyst/models")
def analyst_models(
    instrument: str = Query(..., min_length=1),
    start: datetime = Query(...),
    end: datetime = Query(...),
    interval: str = Query(default="15m", pattern="^(1m|2m|5m|15m|30m|60m|90m|1h|1d|5d|1wk|1mo|3mo)$"),
) -> dict[str, Any]:
    if start > end:
        raise HTTPException(status_code=422, detail="start must not be after end.")
    item = _resolve_instrument_or_search(instrument)
    try:
        bars = _get_service().history(
            symbol=item.display_name, asset_type=item.asset_type, exchange=item.exchange,
            start=start, end=end, provider_id="yfinance", interval=interval,
        )
        return {
            "instrument": item.display_name,
            "interval": interval,
            "analysis": analyze_market_movement(bars),
            "source": "yfinance OHLCV + walk-forward model ensemble",
        }
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Market model analysis failed: {exc}") from exc
