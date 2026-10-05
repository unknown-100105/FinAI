from dataclasses import dataclass
import os
from typing import Optional

from llm.model_registry import enabled_models, get_model_spec, ModelSpec
from llm.resource_orchestrator import assess_local_model, detect_hardware, HardwareSnapshot


@dataclass(frozen=True)
class ModelRoute:
    capability: str
    selected_model: str
    provider: str
    reason: str
    fallback_chain: list[str]
    risk_level: str
    policy: str
    network_mode: str
    data_sensitivity: str
    allowed_providers: tuple[str, ...]
    constraints_applied: tuple[str, ...]
    execution_mode: str
    resource_fit: bool
    resource_reason: str
    hardware: dict

    def to_dict(self) -> dict:
        return {
            "capability": self.capability,
            "selected_model": self.selected_model,
            "provider": self.provider,
            "reason": self.reason,
            "fallback_chain": list(self.fallback_chain),
            "risk_level": self.risk_level,
            "policy": self.policy,
            "network_mode": self.network_mode,
            "data_sensitivity": self.data_sensitivity,
            "allowed_providers": list(self.allowed_providers),
            "constraints_applied": list(self.constraints_applied),
            "execution_mode": self.execution_mode,
            "resource_fit": self.resource_fit,
            "resource_reason": self.resource_reason,
            "hardware": self.hardware,
        }


def provider_for(spec: ModelSpec) -> str:
    if getattr(spec, "provider", ""):
        return spec.provider
    if spec.model_id.startswith("openai-"):
        return "openai"
    if spec.model_id.startswith("gemini-"):
        return "gemini"
    if spec.model_id.startswith("openrouter-"):
        return "openrouter"
    if spec.model_id.startswith("rllm-"):
        return "local"
    return "local"


def _normalise_mode(value: str, allowed: set[str], default: str) -> str:
    normalized = str(value or default).strip().lower()
    return normalized if normalized in allowed else default


def _provider_from_model_id(model_id: str) -> str:
    return provider_for(get_model_spec(model_id))


def _resource_assessment(spec: ModelSpec, hardware: HardwareSnapshot):
    if provider_for(spec) != "local":
        return None
    return assess_local_model(
        required_ram_gb=getattr(spec, "min_ram_gb", 0.0),
        required_vram_gb=getattr(spec, "preferred_vram_gb", 0.0),
        gpu_required=getattr(spec, "gpu_required", False),
        snapshot=hardware,
    )


class ModelRouter:
    """Deterministic policy router for multi-provider LLM execution.

    This is a policy heuristic, not a learned benchmark. Its job is to make
    provider/model selection explicit, reproducible, and auditable.
    """

    def __init__(self, preference: Optional[list[str]] = None):
        raw = (
            os.getenv("FINAI_LLM_PREFERENCE", "")
            if preference is None
            else ",".join(preference)
        )
        self.preference = [
            item.strip().lower() for item in raw.split(",") if item.strip()
        ]
        self.cost_sensitivity = os.getenv(
            "FINAI_LLM_COST_SENSITIVITY", "balanced"
        ).strip().lower()

    def _score(self, spec: ModelSpec, risk_level: str, rank: int) -> float:
        quality = getattr(spec, "quality_tier", 2)
        latency = getattr(spec, "latency_tier", 2)
        cost = getattr(spec, "cost_tier", 2)
        routing_priority = getattr(spec, "routing_priority", 100)

        score = float(routing_priority)
        if str(risk_level).lower() in {"high", "critical"}:
            score += quality * 18
            score -= latency * 2
        else:
            score += quality * 7
            score -= latency * 3

        if self.cost_sensitivity == "high":
            score -= cost * 8
        elif self.cost_sensitivity == "low":
            score += quality * 3

        if spec.model_id in self.preference:
            # Operator preference is a policy override for otherwise eligible
            # candidates; it still cannot select a model outside its capability.
            score += max(1, 200 - self.preference.index(spec.model_id) * 20)

        score -= rank * 0.01
        return score

    def _candidates(
        self,
        capability: str,
        network_mode: str,
        data_sensitivity: str,
        allowed_providers: set[str],
        hardware: HardwareSnapshot,
    ) -> tuple[list[ModelSpec], tuple[str, ...]]:
        candidates = [
            spec
            for spec in enabled_models()
            if capability in spec.capabilities
        ]
        constraints: list[str] = []

        resource_eligible: list[ModelSpec] = []
        for spec in candidates:
            assessment = _resource_assessment(spec, hardware)
            if assessment is None or assessment.resource_fit:
                resource_eligible.append(spec)
            else:
                constraints.append("local_resource_constraint")
        candidates = resource_eligible

        if allowed_providers:
            candidates = [
                spec for spec in candidates
                if provider_for(spec) in allowed_providers
            ]
            constraints.append("provider_allow_list")

        if network_mode == "offline":
            local_only = [spec for spec in candidates if provider_for(spec) == "local"]
            candidates = local_only
            constraints.append("offline_local_only")

        elif network_mode == "degraded":
            constraints.append("degraded_network_local_preference")

        if data_sensitivity == "restricted":
            local_only = [spec for spec in candidates if provider_for(spec) == "local"]
            candidates = local_only
            constraints.append("restricted_data_local_only")

        return candidates, tuple(dict.fromkeys(constraints))

    def fallback_chain(
        self,
        selected_model: str,
        capability: str,
        risk_level: str = "low",
        network_mode: str = "online",
        data_sensitivity: str = "standard",
        allowed_providers: Optional[set[str]] = None,
        hardware: Optional[HardwareSnapshot] = None,
    ) -> list[str]:
        hardware = hardware or detect_hardware()
        candidates, _ = self._candidates(
            capability,
            network_mode=network_mode,
            data_sensitivity=data_sensitivity,
            allowed_providers=allowed_providers or set(),
            hardware=hardware,
        )
        ordered = sorted(
            candidates,
            key=lambda spec: (
                -self._score(spec, risk_level, 0),
                getattr(spec, "routing_priority", 100),
                spec.model_id,
            ),
        )
        primary_provider = provider_for(get_model_spec(selected_model))
        different_provider = [
            spec.model_id
            for spec in ordered
            if spec.model_id != selected_model
            and provider_for(spec) != primary_provider
        ]
        same_provider = [
            spec.model_id
            for spec in ordered
            if spec.model_id != selected_model
            and provider_for(spec) == primary_provider
        ]
        return [selected_model, *different_provider, *same_provider]

    def route(
        self,
        capability: str,
        risk_level: str = "low",
        language: str = "English",
        explicit_model: str | None = None,
        network_mode: str = "online",
        data_sensitivity: str = "standard",
        allowed_providers: Optional[list[str]] = None,
        hardware: Optional[HardwareSnapshot] = None,
    ) -> ModelRoute:
        del language
        network_mode = _normalise_mode(
            network_mode,
            {"online", "degraded", "offline"},
            "online",
        )
        data_sensitivity = _normalise_mode(
            data_sensitivity,
            {"public", "standard", "financial", "restricted"},
            "standard",
        )
        hardware = hardware or detect_hardware()
        providers = {
            str(item).strip().lower()
            for item in (allowed_providers or [])
            if str(item).strip()
        }
        candidates, constraints_applied = self._candidates(
            capability,
            network_mode=network_mode,
            data_sensitivity=data_sensitivity,
            allowed_providers=providers,
            hardware=hardware,
        )
        if explicit_model is not None:
            selected = explicit_model.strip().lower()
            spec = get_model_spec(selected)
            if selected not in {item.model_id for item in candidates}:
                raise ValueError(
                    f"Model '{selected}' is not eligible for capability "
                    f"'{capability}' under the current execution constraints."
                )
            resource = _resource_assessment(spec, hardware)
            return ModelRoute(
                capability=capability,
                selected_model=selected,
                provider=provider_for(spec),
                reason="explicit_model_selection",
                fallback_chain=[selected],
                risk_level=risk_level,
                policy="explicit",
                network_mode=network_mode,
                data_sensitivity=data_sensitivity,
                allowed_providers=tuple(sorted(providers)),
                constraints_applied=constraints_applied,
                execution_mode=resource.execution_mode if resource else "cloud",
                resource_fit=resource.resource_fit if resource else True,
                resource_reason=(
                    resource.reason
                    if resource
                    else "cloud execution does not consume local model memory requirements"
                ),
                hardware=hardware.to_dict(),
            )

        if not candidates:
            raise RuntimeError(
                f"No enabled model supports capability '{capability}'."
            )

        ranked = sorted(
            enumerate(candidates),
            key=lambda item: (
                0 if (
                    network_mode == "degraded"
                    and provider_for(item[1]) == "local"
                ) else 1 if network_mode == "degraded" else 0,
                -self._score(item[1], risk_level, item[0]),
                getattr(item[1], "routing_priority", 100),
                item[1].model_id,
            ),
        )
        selected = ranked[0][1]
        chain = self.fallback_chain(
            selected.model_id,
            capability,
            risk_level,
            network_mode=network_mode,
            data_sensitivity=data_sensitivity,
            allowed_providers=providers,
            hardware=hardware,
        )
        return ModelRoute(
            capability=capability,
            selected_model=selected.model_id,
            provider=provider_for(selected),
            reason=(
                "offline_local_only"
                if network_mode == "offline"
                else "restricted_data_local_only"
                if data_sensitivity == "restricted"
                else "degraded_network_local_preference"
                if network_mode == "degraded"
                else "risk_aware_policy_heuristic"
                if str(risk_level).lower() in {"high", "critical"}
                else "capability_and_resource_policy_heuristic"
            ),
            fallback_chain=list(chain),
            risk_level=risk_level,
            policy="constrained_heuristic" if constraints_applied else "heuristic",
            network_mode=network_mode,
            data_sensitivity=data_sensitivity,
            allowed_providers=tuple(sorted(providers)),
            constraints_applied=constraints_applied,
            execution_mode=(
                _resource_assessment(selected, hardware).execution_mode
                if _resource_assessment(selected, hardware)
                else "cloud"
            ),
            resource_fit=(
                _resource_assessment(selected, hardware).resource_fit
                if _resource_assessment(selected, hardware)
                else True
            ),
            resource_reason=(
                _resource_assessment(selected, hardware).reason
                if _resource_assessment(selected, hardware)
                else "cloud execution does not consume local model memory requirements"
            ),
            hardware=hardware.to_dict(),
        )
