"""Task-aware model selection layered over FinAI's policy ModelRouter.

This module does not execute models or make financial decisions. It selects a
capability profile, then delegates eligibility, privacy, network, resource and
provider constraints to the existing ModelRouter.
"""
from dataclasses import dataclass
from typing import Any, Optional

from llm.model_router import ModelRoute, ModelRouter


@dataclass(frozen=True)
class TaskRoute:
    task_type: str
    capability: str
    selection_reason: str
    route: ModelRoute
    language: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "task_type": self.task_type,
            "capability": self.capability,
            "selection_reason": self.selection_reason,
            "language": self.language,
            "model_route": self.route.to_dict(),
        }


# Intent names are explicit, stable signals. Text heuristics are conservative
# supplements and never replace the application's intent router.
_REASONING_INTENTS = (
    "PORTFOLIO_RISK",
    "SYSTEMIC_RISK",
    "CAUSAL_RISK",
    "STRESS_TEST",
    "COUNTERFACTUAL",
    "FINANCIAL_RESEARCH",
    "MARKET_ANALYSIS",
)
_DOCUMENT_INTENTS = (
    "KYC_DOCUMENTS",
    "DOCUMENT_SUMMARY",
    "FINE_PRINT_SUMMARY",
    "CONTRACT_ANALYSIS",
)
_EXPLANATION_TERMS = (
    "explain",
    "summarize",
    "summary",
    "in simple terms",
    "what does this mean",
)
_REASONING_TERMS = (
    "counterfactual",
    "stress test",
    "systemic risk",
    "portfolio risk",
    "scenario analysis",
    "compare scenarios",
    "research",
    "analyze",
    "analyse",
    "why did",
)


def classify_task(
    intent: str,
    user_text: str = "",
    source: str = "",
    base_capability: Optional[str] = None,
) -> tuple[str, str, str]:
    """Return (task_type, preferred capability, reason) deterministically."""
    normalized_intent = str(intent or "").strip().upper()
    text = str(user_text or "").casefold()
    normalized_source = str(source or "").strip().casefold()

    if normalized_intent.startswith(_REASONING_INTENTS):
        return (
            "complex_financial_reasoning",
            "financial_reasoning",
            "matched_reasoning_intent",
        )

    if normalized_source == "retrieval_evidence" or normalized_intent.startswith(
        _DOCUMENT_INTENTS
    ):
        return (
            "evidence_grounded_document_qa",
            "tool_assisted_qa",
            "retrieval_or_document_task",
        )

    if any(term in text for term in _REASONING_TERMS):
        return (
            "complex_financial_reasoning",
            "financial_reasoning",
            "matched_reasoning_query",
        )

    if any(term in text for term in _EXPLANATION_TERMS):
        return (
            "financial_explanation",
            "financial_explanation",
            "explanation_or_summary_request",
        )

    if base_capability == "financial_qa":
        return (
            "financial_question_answering",
            "financial_qa",
            "financial_qa_intent",
        )

    return (
        "general_response",
        base_capability or "response_generation",
        "default_response_task",
    )


class TaskAwareModelRouter:
    """Select a task capability, then use ModelRouter for policy-safe routing.

    Language is preserved in the trace but does not influence model ranking
    until per-language quality evidence is available in the model registry.
    """

    def __init__(self, model_router: Optional[ModelRouter] = None):
        self.model_router = model_router or ModelRouter()

    def route(
        self,
        *,
        intent: str,
        user_text: str = "",
        source: str = "",
        base_capability: Optional[str] = None,
        risk_level: str = "low",
        language: str = "English",
        explicit_model: Optional[str] = None,
        network_mode: str = "online",
        data_sensitivity: str = "standard",
        allowed_providers: Optional[list[str]] = None,
    ) -> TaskRoute:
        task_type, preferred, reason = classify_task(
            intent=intent,
            user_text=user_text,
            source=source,
            base_capability=base_capability,
        )
        capabilities = [preferred]
        # If automatic selection has no eligible specialist, fall back only to
        # capabilities that are relevant to response generation. Explicit
        # model requests remain strict and never silently downgrade.
        if explicit_model is None:
            for capability in (
                "financial_qa",
                "tool_assisted_qa",
                "financial_explanation",
                "response_generation",
            ):
                if capability not in capabilities:
                    capabilities.append(capability)

        last_error: Optional[Exception] = None
        for capability in capabilities:
            try:
                route = self.model_router.route(
                    capability=capability,
                    risk_level=risk_level,
                    language=language,
                    explicit_model=explicit_model,
                    network_mode=network_mode,
                    data_sensitivity=data_sensitivity,
                    allowed_providers=allowed_providers,
                )
                actual_reason = reason
                if capability != preferred:
                    actual_reason = (
                        f"{reason}; preferred capability unavailable, "
                        f"used eligible fallback capability '{capability}'"
                    )
                return TaskRoute(
                    task_type=task_type,
                    capability=capability,
                    selection_reason=actual_reason,
                    route=route,
                    language=str(language or "English"),
                )
            except (RuntimeError, ValueError, KeyError) as exc:
                last_error = exc
                if explicit_model is not None:
                    raise
        raise RuntimeError(
            f"No eligible model for task '{task_type}' "
            f"(preferred capability '{preferred}')."
        ) from last_error
