from typing import Any, Dict, Optional
from fastapi import APIRouter, Query
from knowledge.investment_eligibility import list_investment_routes, search_investment_routes

router = APIRouter(prefix="/api/v1/knowledge", tags=["knowledge"])

# Keep the existing regulation endpoints and add investor-route endpoints here.

@router.get("/investment-routes")
def investment_routes(category: Optional[str] = Query(default=None)) -> Dict[str, Any]:
    items = list_investment_routes(category)
    return {"count": len(items), "items": items}

@router.get("/investment-routes/search")
def investment_routes_search(query: str = Query(..., min_length=1)) -> Dict[str, Any]:
    return {"query": query, "results": search_investment_routes(query)}
