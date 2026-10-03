from typing import Any, Dict, Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from compliance_catalog import capital_gain_worksheet, find_items, list_items, metadata

router = APIRouter(prefix="/api/v1/compliance", tags=["tax-compliance"])

class CapitalGainRequest(BaseModel):
    buy_value: float = Field(ge=0)
    sell_value: float = Field(ge=0)
    transfer_costs: float = Field(default=0, ge=0)
    improvement_cost: float = Field(default=0, ge=0)

@router.get("/catalog")
def catalog(category: Optional[str] = Query(default=None)) -> Dict[str, Any]:
    return {"meta": metadata(), "items": list_items(category)}

@router.get("/search")
def search(query: str = Query(..., min_length=1)) -> Dict[str, Any]:
    return {"query": query, "results": find_items(query)}

@router.post("/capital-gains/worksheet")
def capital_gains(request: CapitalGainRequest) -> Dict[str, Any]:
    try:
        return {"status": "CALCULATED", "result": capital_gain_worksheet(**request.model_dump())}
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
