from typing import Any, Dict, Optional
from fastapi import APIRouter, Query
from llm.model_registry import MODEL_REGISTRY, enabled_models, models_for_capability, model_configured
from llm.model_router import ModelRouter
from llm.resource_orchestrator import detect_hardware, assess_local_model

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
                "min_ram_gb": spec.min_ram_gb,
                "preferred_vram_gb": spec.preferred_vram_gb,
                "gpu_required": spec.gpu_required,
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


@router.get("/resources")
def resources() -> Dict[str, Any]:
    hardware = detect_hardware()
    local_models = []
    for spec in enabled_models():
        if spec.provider != "local":
            continue
        decision = assess_local_model(
            required_ram_gb=spec.min_ram_gb,
            required_vram_gb=spec.preferred_vram_gb,
            gpu_required=spec.gpu_required,
            snapshot=hardware,
        )
        local_models.append({
            "model_id": spec.model_id,
            "model_name": spec.model_name,
            "resource": decision.to_dict(),
        })
    return {
        "hardware": hardware.to_dict(),
        "local_models": local_models,
        "planning_note": (
            "Resource values are routing metadata and current machine observations; "
            "they are not a benchmark of actual model memory consumption."
        ),
    }
