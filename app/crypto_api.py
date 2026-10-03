from typing import Any, Dict, List

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from crypto.arbitrage import estimate_arbitrage
from crypto.scanner import scan_cross_exchange_arbitrage
from crypto.universe import all_exchange_tickers, market_universe, scan_all_pairs, supported_connectors, registered_vda_services
from crypto.mining import btc_mining_snapshot


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


@router.get("/connectors")
def crypto_connectors() -> Dict[str, Any]:
    return {
        "connectors": supported_connectors(),
        "registered_vda_services": registered_vda_services(),
        "registered_count": len(registered_vda_services()),
        "note": "FIU-IND reporting-entity status is an AML/PMLA registration snapshot, not a government endorsement or securities licence.",
    }


@router.get("/markets")
def crypto_markets(
    exchange: str = "binance",
    quote: str | None = None,
    search: str | None = None,
    limit: int = 1000,
    offset: int = 0,
) -> Dict[str, Any]:
    try:
        return market_universe(
            exchange_id=exchange,
            quote=quote,
            search=search,
            limit=limit,
            offset=offset,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"Crypto market universe unavailable: {exc}") from exc


class AllPairsScanRequest(BaseModel):
    exchanges: List[str] = Field(default_factory=lambda: ["binance", "bybit", "kucoin", "coinbase"], min_length=2, max_length=8)
    quote: str = Field(default="USDT", min_length=2, max_length=10)
    capital_quote: float = Field(default=1000.0, gt=0)
    buy_fee_percent: float = Field(default=0.1, ge=0)
    sell_fee_percent: float = Field(default=0.1, ge=0)
    buy_slippage_percent: float = Field(default=0.05, ge=0)
    sell_slippage_percent: float = Field(default=0.05, ge=0)
    transfer_cost_quote: float = Field(default=0.0, ge=0)
    tax_rate_percent: float = Field(default=0.0, ge=0)
    top_n: int = Field(default=25, ge=1, le=100)


@router.post("/arbitrage/scan-all")
def arbitrage_scan_all(request: AllPairsScanRequest) -> Dict[str, Any]:
    try:
        return scan_all_pairs(**request.model_dump())
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"All-pairs scan failed: {exc}") from exc


@router.get("/tickers")
def crypto_tickers(
    exchange: str = "binance",
    quote: str | None = "USDT",
    search: str | None = None,
    limit: int = 500,
    offset: int = 0,
) -> Dict[str, Any]:
    try:
        items = all_exchange_tickers(exchange, quote=quote)
        s = (search or "").strip().upper()
        if s:
            items = [item for item in items if s in item["symbol"].upper()]
        start = max(0, int(offset))
        end = start + max(1, min(int(limit), 2000))
        return {
            "exchange": exchange,
            "quote": quote,
            "count": len(items),
            "offset": start,
            "limit": end - start,
            "tickers": items[start:end],
            "snapshot_at": __import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat(),
        }
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"Crypto tickers unavailable: {exc}") from exc


class MiningRequest(BaseModel):
    hashrate_ths: float = Field(default=200.0, gt=0)
    power_watts: float = Field(default=3500.0, gt=0)
    electricity_usd_kwh: float = Field(default=0.10, ge=0)


@router.post("/mining/btc")
def mining_btc(request: MiningRequest) -> Dict[str, Any]:
    try:
        return btc_mining_snapshot(**request.model_dump())
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"Live mining data unavailable: {exc}") from exc
