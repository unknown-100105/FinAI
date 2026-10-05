from typing import Any, Dict, Optional
from fastapi import APIRouter, Query
from llm.model_registry import MODEL_REGISTRY, enabled_models, models_for_capability, model_configured
from llm.model_router import ModelRouter

router = APIRouter(prefix="/api/v1/models", tags=["models"])


@router.get("")
def models(capability: Optional[str] = Query(default=None)) -> Dict[str, Any]:
    normalized_capability = (
        capability.strip()
        if isinstance(capability, str) and capability.strip()
        else None
    )
    specs = (
        models_for_capability(normalized_capability)
        if normalized_capability
        else list(MODEL_REGISTRY.values())
    )
    enabled = {spec.model_id for spec in enabled_models()}
    return {
        "models": [
            {
                "model_id": spec.model_id,
                "model_name": spec.model_name,
                "role": spec.role,
                "provider": spec.provider,
                "capabilities": list(spec.capabilities),
                "enabled": spec.model_id in enabled,
                "configured": model_configured(spec),
                "quality_tier": spec.quality_tier,
                "latency_tier": spec.latency_tier,
                "cost_tier": spec.cost_tier,
                "routing_priority": spec.routing_priority,
                "configuration_note": (
                    "Enabled by environment configuration."
                    if spec.model_id in enabled
                    else "Registered but not enabled in the current environment."
                ),
            }
            for spec in specs
        ],
    }


@router.post("/route")
def route_preview(payload: Dict[str, Any]) -> Dict[str, Any]:
    capability = str(payload.get("capability", "response_generation")).strip()
    risk_level = str(payload.get("risk_level", "low")).strip().lower()
    language = str(payload.get("language", "English")).strip()
    model_id = payload.get("model_id")
    network_mode = str(payload.get("network_mode", "online")).strip().lower()
    data_sensitivity = str(
        payload.get("data_sensitivity", "standard")
    ).strip().lower()
    allowed_providers = payload.get("allowed_providers")
    if allowed_providers is not None and not isinstance(allowed_providers, list):
        raise ValueError("allowed_providers must be a list when supplied")

    router = ModelRouter()
    route = router.route(
        capability=capability,
        risk_level=risk_level,
        language=language,
        explicit_model=str(model_id) if model_id else None,
        network_mode=network_mode,
        data_sensitivity=data_sensitivity,
        allowed_providers=[
            str(item) for item in (allowed_providers or [])
        ],
    )
    return route.to_dict()
