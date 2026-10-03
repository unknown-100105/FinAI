from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from investment_catalog import (
    bond_plan,
    catalog_metadata,
    fd_plan,
    list_mutual_fund_categories,
    list_products,
    sip_plan,
    small_savings_projection,
)

router = APIRouter(prefix="/api/v1/investments", tags=["investments"])


class SipRequest(BaseModel):
    monthly_investment: float = Field(gt=0)
    annual_return_percent: float = Field(default=12.0, ge=-99, le=100)
    years: float = Field(default=10.0, gt=0, le=60)
    annual_step_up_percent: float = Field(default=0.0, ge=0, le=100)
    annual_inflation_percent: float = Field(default=0.0, ge=0, le=30)
    target_corpus: Optional[float] = Field(default=None, gt=0)


class FdRequest(BaseModel):
    principal: float = Field(gt=0)
    annual_rate_percent: float = Field(default=7.0, ge=0, le=30)
    years: float = Field(default=5.0, gt=0, le=60)
    compounding_per_year: int = Field(default=4, ge=1, le=12)


class BondRequest(BaseModel):
    face_value: float = Field(default=100000.0, gt=0)
    coupon_rate_percent: float = Field(default=7.0, ge=0, le=100)
    yield_percent: float = Field(default=7.0, ge=-99, le=100)
    years_to_maturity: float = Field(default=5.0, gt=0, le=100)
    coupon_frequency: int = Field(default=2, ge=1, le=12)


class SmallSavingsRequest(BaseModel):
    product_id: str = Field(min_length=1, max_length=64)
    principal: float = Field(gt=0)
    years: Optional[float] = Field(default=None, gt=0, le=60)


@router.get("/catalog")
def catalog() -> Dict[str, Any]:
    return {
        "meta": catalog_metadata(),
        "small_savings": list_products(),
        "mutual_fund_categories": list_mutual_fund_categories(),
    }


@router.get("/products")
def products(category: Optional[str] = None) -> Dict[str, Any]:
    return {"meta": catalog_metadata(), "products": list_products(category)}


@router.post("/sip/plan")
def sip_plan_endpoint(request: SipRequest) -> Dict[str, Any]:
    try:
        return {"status": "CALCULATED", "result": sip_plan(**request.model_dump())}
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.post("/fd/plan")
def fd_plan_endpoint(request: FdRequest) -> Dict[str, Any]:
    try:
        return {"status": "CALCULATED", "result": fd_plan(**request.model_dump())}
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.post("/bond/price")
def bond_plan_endpoint(request: BondRequest) -> Dict[str, Any]:
    try:
        return {"status": "CALCULATED", "result": bond_plan(**request.model_dump())}
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.post("/small-savings/project")
def small_savings_endpoint(request: SmallSavingsRequest) -> Dict[str, Any]:
    try:
        return {"status": "CALCULATED", "result": small_savings_projection(**request.model_dump())}
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
