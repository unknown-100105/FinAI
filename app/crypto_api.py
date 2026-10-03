from typing import Any, Dict, List

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from crypto.arbitrage import estimate_arbitrage
from crypto.scanner import scan_cross_exchange_arbitrage


router = APIRouter(
    prefix="/api/v1/crypto",
    tags=["crypto"],
)


class ArbitrageEstimateRequest(BaseModel):
    asset: str = Field(default="BTC/USDT", min_length=1, max_length=64)
    buy_venue: str = Field(default="venue-a", min_length=1, max_length=64)
    sell_venue: str = Field(default="venue-b", min_length=1, max_length=64)
    capital_quote: float = Field(default=1000.0, gt=0)
    buy_price: float = Field(gt=0)
    sell_price: float = Field(gt=0)
    buy_fee_percent: float = Field(default=0.0, ge=0)
    sell_fee_percent: float = Field(default=0.0, ge=0)
    buy_slippage_percent: float = Field(default=0.0, ge=0)
    sell_slippage_percent: float = Field(default=0.0, ge=0)
    transfer_cost_quote: float = Field(default=0.0, ge=0)
    fx_cost_percent: float = Field(default=0.0, ge=0)
    tax_rate_percent: float = Field(default=0.0, ge=0)
    max_quantity: float | None = Field(default=None, gt=0)


class ArbitrageScanRequest(BaseModel):
    symbol: str = Field(default="BTC/USDT", min_length=1, max_length=64)
    exchanges: List[str] = Field(
        default_factory=lambda: ["binance", "bybit", "okx", "kucoin"],
        min_length=2,
        max_length=12,
    )
    capital_quote: float = Field(default=1000.0, gt=0)
    buy_fee_percent: float = Field(default=0.1, ge=0)
    sell_fee_percent: float = Field(default=0.1, ge=0)
    buy_slippage_percent: float = Field(default=0.05, ge=0)
    sell_slippage_percent: float = Field(default=0.05, ge=0)
    transfer_cost_quote: float = Field(default=0.0, ge=0)
    fx_cost_percent: float = Field(default=0.0, ge=0)
    tax_rate_percent: float = Field(default=0.0, ge=0)


@router.post("/arbitrage/estimate")
def arbitrage_estimate(request: ArbitrageEstimateRequest) -> Dict[str, Any]:
    try:
        return estimate_arbitrage(**request.model_dump())
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.post("/arbitrage/scan")
def arbitrage_scan(request: ArbitrageScanRequest) -> Dict[str, Any]:
    try:
        return scan_cross_exchange_arbitrage(**request.model_dump())
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Cross-exchange scan failed: {exc}",
        ) from exc
