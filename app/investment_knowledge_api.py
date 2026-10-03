from typing import Any
from fastapi import APIRouter, Query
from knowledge.investment_scope import investment_scope

router = APIRouter(prefix="/api/v1/investments", tags=["investment-knowledge"])

@router.get("/scope")
def scope() -> dict[str, Any]:
    return investment_scope()

@router.get("/global-markets")
def global_markets(region: str | None = Query(default=None)) -> list[dict[str, str]]:
    rows = investment_scope()["global_market_registry"]
    if not region:
        return rows
    needle = region.lower()
    return [row for row in rows if needle in row["country"].lower() or needle in row["code"].lower() or needle in row["market"].lower()]
