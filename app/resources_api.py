from typing import Any, Dict, Optional
from fastapi import APIRouter, Query
from knowledge.official_resources import list_resources, search_resources

router = APIRouter(prefix="/api/v1/resources", tags=["resources"])

@router.get("")
def resources(category: Optional[str] = Query(default=None)) -> Dict[str, Any]:
    items = list_resources(category)
    return {"count": len(items), "items": items}

@router.get("/search")
def search(query: str = Query(..., min_length=1)) -> Dict[str, Any]:
    return {"query": query, "results": search_resources(query)}
