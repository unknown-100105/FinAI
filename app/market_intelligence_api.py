from datetime import datetime,timedelta,timezone
from typing import Any
from fastapi import APIRouter,HTTPException,Query
from market_data.global_investments import eligibility as get_eligibility,global_catalog
from market_data.prediction import run_model_arena
from app.market_api import _get_service,_resolve_instrument_or_search

router=APIRouter(prefix="/api/v1/intelligence",tags=["market-intelligence"])

@router.get("/prediction")
def prediction(instrument:str=Query(...,min_length=1),horizon:int=Query(5,ge=1,le=60),days:int=Query(730,ge=90,le=3650),interval:str=Query("1d",pattern="^(1d|1wk|1mo)$"))->dict[str,Any]:
    item=_resolve_instrument_or_search(instrument); end=datetime.now(timezone.utc); start=end-timedelta(days=days)
    try:
        bars=_get_service().history(symbol=item.display_name,asset_type=item.asset_type,exchange=item.exchange,start=start,end=end,provider_id="yfinance",interval=interval)
        result=run_model_arena(bars,horizon=horizon)
    except Exception as exc: raise HTTPException(status_code=502,detail=f"Prediction engine failed: {exc}") from exc
    return {"instrument":{"display_name":item.display_name,"asset_type":item.asset_type,"exchange":item.exchange,"currency":item.currency},"range":{"start":start,"end":end},**result}

@router.get("/global-assets")
def global_assets()->dict[str,Any]: return global_catalog()

@router.get("/eligibility")
def eligibility(country_code:str=Query(...,min_length=2,max_length=2),asset_class:str=Query("government_bond",min_length=2,max_length=64))->dict[str,Any]:
    try:return get_eligibility(country_code,asset_class)
    except ValueError as exc:raise HTTPException(status_code=404,detail=str(exc)) from exc
