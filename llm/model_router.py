from dataclasses import dataclass
import os
from typing import Optional

from llm.model_registry import enabled_models, get_model_spec, ModelSpec


@dataclass(frozen=True)
class ModelRoute:
    capability: str
    selected_model: str
    provider: str
    reason: str
    fallback_chain: tuple[str, ...]
    risk_level: str
    policy: str

    def to_dict(self) -> dict:
        return {
            "capability": self.capability,
            "selected_model": self.selected_model,
            "provider": self.provider,
            "reason": self.reason,
            "fallback_chain": list(self.fallback_chain),
            "risk_level": self.risk_level,
            "policy": self.policy,
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
            score += max(1, 40 - self.preference.index(spec.model_id) * 5)

        score -= rank * 0.01
        return score

    def _candidates(self, capability: str) -> list[ModelSpec]:
        return [
            spec
            for spec in enabled_models()
            if capability in spec.capabilities
        ]

    def fallback_chain(
        self,
        selected_model: str,
        capability: str,
        risk_level: str = "low",
    ) -> list[str]:
        candidates = self._candidates(capability)
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
    ) -> ModelRoute:
        candidates = self._candidates(capability)
        if explicit_model is not None:
            selected = explicit_model.strip().lower()
            get_model_spec(selected)
            if selected not in {spec.model_id for spec in candidates}:
                raise ValueError(
                    f"Model '{selected}' does not support capability '{capability}'."
                )
            return ModelRoute(
                capability=capability,
                selected_model=selected,
                provider=provider_for(get_model_spec(selected)),
                reason="explicit_model_selection",
                fallback_chain=(selected,),
                risk_level=risk_level,
                policy="explicit",
            )

        if not candidates:
            raise RuntimeError(
                f"No enabled model supports capability '{capability}'."
            )

        ranked = sorted(
            enumerate(candidates),
            key=lambda item: (
                -self._score(item[1], risk_level, item[0]),
                getattr(item[1], "routing_priority", 100),
                item[1].model_id,
            ),
        )
        selected = ranked[0][1]
        chain = self.fallback_chain(selected.model_id, capability, risk_level)
        return ModelRoute(
            capability=capability,
            selected_model=selected.model_id,
            provider=provider_for(selected),
            reason=(
                "risk_aware_policy_heuristic"
                if str(risk_level).lower() in {"high", "critical"}
                else "capability_and_resource_policy_heuristic"
            ),
            fallback_chain=tuple(chain),
            risk_level=risk_level,
            policy="heuristic",
        )
