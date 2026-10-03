from typing import Any
from fastapi import APIRouter
from app.main import APP_VERSION

router = APIRouter(prefix="/api/v1/system", tags=["system"])

@router.get("/status")
def status() -> dict[str, Any]:
    return {
        "status": "ok",
        "app_version": APP_VERSION,
        "api_prefixes": [
            "/api/v1/market",
            "/api/v1/market/analyst",
            "/api/v1/crypto",
            "/api/v1/investments",
            "/api/v1/compliance",
            "/api/v1/knowledge",
            "/api/v1/resources",
            "/api/v1/models",
        ],
    }
