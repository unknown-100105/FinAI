from typing import Any, Dict, Optional
from fastapi import APIRouter, Query
from llm.model_registry import MODEL_REGISTRY, enabled_models, models_for_capability

router = APIRouter(prefix="/api/v1/models", tags=["models"])

@router.get("")
def models(capability: Optional[str] = Query(default=None)) -> Dict[str, Any]:
    specs = models_for_capability(capability) if capability else list(MODEL_REGISTRY.values())
    enabled = {spec.model_id for spec in enabled_models()}
    return {
        "models": [
            {
                "model_id": spec.model_id,
                "model_name": spec.model_name,
                "role": spec.role,
                "capabilities": list(spec.capabilities),
                "enabled": spec.model_id in enabled,
                "configuration_note": (
                    "Enabled by environment configuration."
                    if spec.model_id in enabled else
                    "Registered but not enabled in the current environment."
                ),
            }
            for spec in specs
        ],
    }
