from typing import Any, Dict, Optional
from fastapi import APIRouter, Query
from knowledge.india_finance_regulation import list_regulations, search_regulations

router = APIRouter(prefix="/api/v1/knowledge", tags=["knowledge"])


@router.get("/regulations")
def regulations(category: Optional[str] = Query(default=None)) -> Dict[str, Any]:
    return {"count": len(list_regulations(category)), "items": list_regulations(category)}


@router.get("/search")
def search(query: str = Query(..., min_length=1)) -> Dict[str, Any]:
    return {"query": query, "results": search_regulations(query)}
