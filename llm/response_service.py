from typing import Any, Dict, Optional

from llm.model_gateway import ModelGateway
from llm.model_registry import enabled_models, provider_configured, get_model_spec
from llm.response_verifier import FinancialResponseVerifier
from rag.evidence_verifier import RAGEvidenceVerifier
from response_engine.financial import FinancialResponseEngine
from xai.claim_extractor import FinancialClaimExtractor
from xai.claim_verifier import ClaimVerifier
from xai.claims import build_finance_claims

from llm.response_adapter import SarvamResponseAdapter
from llm.rllm_finqa_adapter import RLLMFinQAModelAdapter
from llm.colibri_adapter import ColibriResponseAdapter
from llm.cloud.gemini_adapter import GeminiProResponseAdapter, GeminiResponseAdapter
from llm.cloud.openrouter_adapter import OpenRouterResponseAdapter
from llm.cloud.anthropic_adapter import AnthropicResponseAdapter
from llm.cloud.mistral_adapter import MistralResponseAdapter
from llm.model_router import ModelRouter, provider_for
from llm.task_aware_router import TaskAwareModelRouter
from llm.verifier_gated_escalation import verifier_gated_escalate
from llm.cloud.openai_adapter import OpenAIAstraResponseAdapter, OpenAISolResponseAdapter, OpenAIResponseAdapter


class ResponseService:

    CAPABILITY_BY_INTENT = {
        "EMI_QUERY": "financial_qa",
        "INTEREST_QUERY": "financial_qa",
        # Retrieval-grounded financial knowledge can use the local
        # financial-QA model when cloud providers are unavailable.
        "KYC_DOCUMENTS": "financial_qa",
        "FINANCIAL_GUIDANCE": "financial_qa",
        "FINANCIAL_PRODUCT_KNOWLEDGE": "financial_qa",
    }

    ADAPTERS = {
        "gemini-cloud": GeminiResponseAdapter,
        "openrouter-cloud": OpenRouterResponseAdapter,
        "openai-luna": OpenAIResponseAdapter,
        "openai-astra": OpenAIAstraResponseAdapter,
        "openai-sol": OpenAISolResponseAdapter,
        "gemini-pro-cloud": GeminiProResponseAdapter,
        "rllm-finqa-4b": RLLMFinQAModelAdapter,
        "colibri-local": ColibriResponseAdapter,
        "sarvam-1": SarvamResponseAdapter,
        "anthropic-claude": AnthropicResponseAdapter,
        "mistral-large": MistralResponseAdapter,
    }

    FALLBACK_MODEL_IDS_BY_CAPABILITY = {
        # Generic responses should remain on general-purpose providers.
        # The specialized financial-QA model is only a fallback for
        # financial_qa capability requests.
        "response_generation": (
            "gemini-cloud",
            "openrouter-cloud",
            "anthropic-claude",
            "mistral-large",
            "colibri-local",
        ),
        "financial_qa": (
            "gemini-cloud",
            "openrouter-cloud",
            "anthropic-claude",
            "mistral-large",
            "rllm-finqa-4b",
            "colibri-local",
        ),
        # Reasoning fallbacks must themselves advertise financial_reasoning.
        # General cloud models are intentionally excluded from this profile.
        "financial_reasoning": (
            "gemini-pro-cloud",
            "openai-astra",
            "openai-sol",
            "openai-luna",
            "anthropic-claude",
            "mistral-large",
            "rllm-finqa-4b",
        ),
        # These task profiles use the same eligible provider fallback family;
        # the selected capability is still enforced by the primary ModelRouter.
        "tool_assisted_qa": (
            "gemini-cloud",
            "openrouter-cloud",
            "anthropic-claude",
            "mistral-large",
            "colibri-local",
        ),
        "financial_explanation": (
            "gemini-cloud",
            "openrouter-cloud",
            "anthropic-claude",
            "mistral-large",
            "colibri-local",
        ),
    }

    REQUIRED_CLAIM_FIELDS = {
        "EMI_QUERY": (
            "monthly_emi",
            "total_payment",
            "total_interest",
        ),
    }

    def __init__(
        self,
        gateway: Optional[ModelGateway] = None,
        *,
        evidence_retriever: Any = None,
        max_verifier_escalations: int = 1,
    ):
        self.gateway = (
            gateway
            if gateway is not None
            else ModelGateway(
                default_model="gemini-cloud"
            )
        )

        self.response_verifier = (
            FinancialResponseVerifier()
        )

        self.rag_evidence_verifier = RAGEvidenceVerifier()

        self.claim_verifier = ClaimVerifier()

        self.fallback_engine = (
            FinancialResponseEngine()
        )

        # Provider-level fallback adapters are kept separate from the
        # normal model registry so fallback providers do not affect
        # automatic model selection.
        self._fallback_adapters: Dict[str, Any] = {}
        self.model_router = ModelRouter()
        self.task_router = TaskAwareModelRouter(self.model_router)
        self.evidence_retriever = evidence_retriever
        self.max_verifier_escalations = max(0, min(int(max_verifier_escalations), 2))

        if gateway is None:
            self._register_enabled_models()

    def _register_enabled_models(self) -> None:

        for spec in enabled_models():

            adapter_class = self.ADAPTERS.get(
                spec.model_id
            )

            if adapter_class is None:
                raise RuntimeError(
                    f"No adapter registered for enabled "
                    f"model '{spec.model_id}'."
                )

            if spec.model_id == "sarvam-1":
                adapter = adapter_class(
                    lazy_load=True,
                )
            else:
                adapter = adapter_class()

            self.gateway.register(
                model_id=spec.model_id,
                adapter=adapter,
                capabilities=list(
                    spec.capabilities
                ),
            )

    def select_model(
        self,
        intent: str,
        risk_level: str = "low",
        language: str = "English",
        explicit_model: Optional[str] = None,
        user_text: str = "",
        source: str = "",
        network_mode: str = "online",
        data_sensitivity: str = "standard",
        allowed_providers: Optional[list[str]] = None,
    ) -> str:
        base_capability = self.CAPABILITY_BY_INTENT.get(
            intent,
            "response_generation",
        )
        task_route = self.task_router.route(
            intent=intent,
            user_text=user_text,
            source=source,
            base_capability=base_capability,
            risk_level=risk_level,
            language=language,
            explicit_model=explicit_model,
            network_mode=network_mode,
            data_sensitivity=data_sensitivity,
            allowed_providers=allowed_providers,
        )
        return task_route.route.selected_model

    def _get_fallback_adapter(
        self,
        model_id: str,
    ) -> Any:
        """Return a cached fallback adapter for the requested model."""

        model_id = str(model_id).strip().lower()

        if model_id in self._fallback_adapters:
            return self._fallback_adapters[model_id]

        if model_id in self.gateway.available_models():
            adapter = self.gateway.get_adapter(model_id)
        else:
            adapter_class = self.ADAPTERS.get(model_id)

            if adapter_class is None:
                return None

            adapter = adapter_class()

        self._fallback_adapters[model_id] = adapter
        return adapter

    def _generate_with_provider_fallback(
        self,
        selected_model: str,
        explicit_model: bool,
        user_text: str,
        intent: str,
        verified_result: Dict[str, Any],
        source: str,
        language: str,
        persona: str,
        max_new_tokens: int,
        capability: str,
        network_mode: str = "online",
        data_sensitivity: str = "standard",
        allowed_providers: Optional[tuple[str, ...]] = None,
    ) -> Dict[str, Any]:
        """Generate with fallbacks constrained by the request's network policy."""

        try:
            result = self.gateway.generate(
                user_text=user_text,
                intent=intent,
                verified_result=verified_result,
                source=source,
                language=language,
                persona=persona,
                model_id=selected_model,
                max_new_tokens=max_new_tokens,
            )

            result.setdefault("fallback_used", False)
            result.setdefault(
                "fallback_chain",
                [selected_model],
            )

            return result

        except (RuntimeError, OSError) as primary_error:

            # Explicit model selection remains deterministic.
            if explicit_model:
                raise

            attempted = [selected_model]

            configured_fallback_candidates = (
                self.FALLBACK_MODEL_IDS_BY_CAPABILITY.get(
                    capability,
                    (),
                )
            )
            allowed = {
                str(provider).strip().lower()
                for provider in (allowed_providers or ())
                if str(provider).strip()
            }
            normalized_mode = str(network_mode or "online").strip().lower()
            normalized_sensitivity = str(data_sensitivity or "standard").strip().lower()
            fallback_candidates = []
            for fallback_id in configured_fallback_candidates:
                try:
                    spec = get_model_spec(fallback_id)
                    fallback_provider = provider_for(spec)
                except (KeyError, ValueError):
                    attempted.append(fallback_id)
                    continue

                # A fallback must satisfy the requested task capability too;
                # provider availability alone is not sufficient.
                if capability not in spec.capabilities:
                    continue

                # Offline and restricted-data policies are hard constraints:
                # a failed local attempt must never silently fall back to cloud.
                if normalized_mode == "offline" and fallback_provider != "local":
                    continue
                if normalized_sensitivity == "restricted" and fallback_provider != "local":
                    continue
                if allowed and fallback_provider not in allowed:
                    continue

                configured = (
                    fallback_id in self._fallback_adapters
                    or fallback_id in self.gateway.available_models()
                    or (
                        fallback_provider != "local"
                        and provider_configured(spec.provider)
                    )
                )
                if configured:
                    fallback_candidates.append(fallback_id)

            for fallback_model_id in fallback_candidates:

                if fallback_model_id == selected_model:
                    continue

                try:
                    adapter = self._get_fallback_adapter(
                        fallback_model_id
                    )
                except Exception:
                    attempted.append(fallback_model_id)
                    continue

                if adapter is None:
                    continue

                try:
                    fallback_result = adapter.generate(
                        user_text=user_text,
                        intent=intent,
                        verified_result=verified_result,
                        source=source,
                        language=language,
                        persona=persona,
                        max_new_tokens=max_new_tokens,
                    )

                    if not isinstance(
                        fallback_result,
                        dict,
                    ):
                        raise TypeError(
                            f"Fallback adapter "
                            f"'{fallback_model_id}' returned "
                            f"{type(fallback_result).__name__}; "
                            "expected dict."
                        )

                    fallback_result["model_id"] = (
                        fallback_model_id
                    )
                    fallback_result["fallback_used"] = True
                    fallback_result["fallback_from"] = (
                        selected_model
                    )
                    fallback_result["fallback_chain"] = (
                        attempted + [fallback_model_id]
                    )

                    return fallback_result

                except Exception:
                    attempted.append(
                        fallback_model_id
                    )

            raise RuntimeError(
                "All configured LLM providers failed. "
                f"Attempted providers: "
                f"{', '.join(attempted)}"
            ) from primary_error

    def _verify_response(
        self,
        response: str,
        intent: str,
        verified_result: Dict[str, Any],
        source: str = "",
    ) -> Dict[str, Any]:

        if source == "retrieval_evidence":
            documents = verified_result.get("documents") or []

            return self.rag_evidence_verifier.verify(
                response=response,
                documents=documents,
            )

        if intent == "EMI_QUERY":

            result = self.response_verifier.verify_emi(
                response=response,
                verified_result=verified_result,
            )

            return {
                "applicable": True,
                **result,
            }

        return {
            "applicable": False,
            "passed": True,
            "missing_values": [],
            "semantic_errors": [],
        }

    def _verify_claims(
        self,
        response: str,
        intent: str,
        verified_result: Dict[str, Any],
        source: str,
    ) -> Dict[str, Any]:

        required_fields = self.REQUIRED_CLAIM_FIELDS.get(
            intent
        )

        if not required_fields:

            return {
                "applicable": False,
                "passed": True,
                "report": None,
                "claims": [],
            }

        authoritative = build_finance_claims(
            result=verified_result,
            source=source,
            operation=intent,
        )

        proposed = FinancialClaimExtractor.extract(
            response=response,
            expected_fields=list(required_fields),
        )

        report = self.claim_verifier.verify(
            authoritative=authoritative,
            proposed=proposed,
            required_fields=list(required_fields),
        )

        return {
            "applicable": True,
            "passed": report.passed,
            "report": report.to_dict(),
            "claims": proposed.to_dict(),
        }

    def _retry_truncated_generation(
        self,
        result: Dict[str, Any],
        selected_model: str,
        user_text: str,
        intent: str,
        verified_result: Dict[str, Any],
        source: str,
        language: str,
        persona: str,
        max_new_tokens: int,
    ) -> Dict[str, Any]:
        """Perform one bounded retry when generation hits the token limit."""

        if not bool(result.get("truncated", False)):
            return result

        retry_tokens = min(
            max(max_new_tokens * 2, max_new_tokens + 64),
            512,
        )

        if retry_tokens <= max_new_tokens:
            return {
                **result,
                "status": "INCOMPLETE_GENERATION",
                "generation_complete": False,
                "truncated": True,
                "finish_reason": "length",
                "retry_after_truncation": False,
            }

        try:
            if selected_model in self.gateway.available_models():
                adapter = self.gateway.get_adapter(selected_model)
            else:
                adapter = self._get_fallback_adapter(selected_model)

            if adapter is None:
                raise RuntimeError(
                    f"No adapter available for '{selected_model}'."
                )

            retried = adapter.generate(
                user_text=user_text,
                intent=intent,
                verified_result=verified_result,
                source=source,
                language=language,
                persona=persona,
                max_new_tokens=retry_tokens,
            )

            if not isinstance(retried, dict):
                raise TypeError(
                    f"Retry adapter '{selected_model}' returned "
                    f"{type(retried).__name__}; expected dict."
                )

            retried["model_id"] = selected_model
            for metadata_key in (
                "fallback_used",
                "fallback_from",
                "fallback_chain",
            ):
                if metadata_key in result:
                    retried[metadata_key] = result[metadata_key]
            retried["retry_after_truncation"] = True
            retried["retry_max_new_tokens"] = retry_tokens

            if bool(retried.get("truncated", False)):
                retried["status"] = "INCOMPLETE_GENERATION"
                retried["generation_complete"] = False
                retried["finish_reason"] = retried.get(
                    "finish_reason",
                    "length",
                )

            return retried

        except Exception as exc:
            return {
                **result,
                "status": "INCOMPLETE_GENERATION",
                "generation_complete": False,
                "truncated": True,
                "finish_reason": "length",
                "retry_after_truncation": True,
                "retry_error": str(exc),
                "retry_max_new_tokens": retry_tokens,
            }

    def _build_verified_fallback(
        self,
        user_text: str,
        intent: str,
        verified_result: Dict[str, Any],
        source: str,
        persona: str,
    ) -> Dict[str, Any]:

        fallback = self.fallback_engine.generate(
            intent=intent,
            result={
                "result": verified_result,
            },
            status="CALCULATED",
            persona=persona,
        )

        verification = self._verify_response(
            response=fallback,
            intent=intent,
            verified_result=verified_result,
            source=source,
        )

        claim_verification = self._verify_claims(
            response=fallback,
            intent=intent,
            verified_result=verified_result,
            source=source,
        )

        return {
            "response": fallback,
            "verification": verification,
            "claim_verification": claim_verification,
        }

    def _try_verifier_escalation(
        self,
        *,
        selected_model: str,
        explicit_model: bool,
        route: Any,
        capability: str,
        user_text: str,
        intent: str,
        verified_result: Dict[str, Any],
        source: str,
        language: str,
        persona: str,
        max_new_tokens: int,
        initial_response: str,
        verification: Dict[str, Any],
        claim_verification: Dict[str, Any],
    ) -> Optional[Dict[str, Any]]:
        """Retry failed answers using only policy-eligible configured models."""
        failed = (
            (verification.get("applicable") and not verification.get("passed"))
            or (
                claim_verification.get("applicable")
                and not claim_verification.get("passed")
            )
        )
        if not failed or explicit_model or self.max_verifier_escalations <= 0:
            return None

        working_result = dict(verified_result)
        retrieval_attempted = False
        retrieval_error_type = None
        if source == "retrieval_evidence" and callable(self.evidence_retriever):
            retrieval_attempted = True
            try:
                documents = self.evidence_retriever(
                    user_text, intent, list(working_result.get("documents") or [])
                )
                if documents is not None:
                    working_result["documents"] = list(documents)
                    refreshed_verification, refreshed_claims = (
                        self._verify_response(
                            initial_response, intent, working_result, source
                        ),
                        self._verify_claims(
                            initial_response, intent, working_result, source
                        ),
                    )
                    refreshed_passed = (
                        not refreshed_verification.get("applicable")
                        or refreshed_verification.get("passed")
                    ) and (
                        not refreshed_claims.get("applicable")
                        or refreshed_claims.get("passed")
                    )
                    if refreshed_passed:
                        return {
                            "status": "GENERATED_VERIFIED_AFTER_RETRIEVAL",
                            "model_id": selected_model,
                            "response": initial_response,
                            "verification": refreshed_verification,
                            "claim_verification": refreshed_claims,
                            "verification_escalation": {
                                "attempted": True,
                                "accepted": True,
                                "action": "retrieve_more_evidence",
                                "from_model": selected_model,
                                "attempt_count": 0,
                                "evidence_retrieval_attempted": True,
                            },
                        }
            except Exception as exc:
                retrieval_error_type = type(exc).__name__

        candidates = []
        allowed = set(route.allowed_providers)
        try:
            selected_quality = int(getattr(get_model_spec(selected_model), "quality_tier", 0))
        except (KeyError, ValueError):
            selected_quality = 0
        for candidate in route.fallback_chain:
            if candidate in {selected_model, route.selected_model} or candidate in candidates:
                continue
            try:
                spec = get_model_spec(candidate)
                provider = provider_for(spec)
            except (KeyError, ValueError):
                continue
            if capability not in spec.capabilities:
                continue
            # Escalation means a strictly higher registry quality tier, not
            # merely another provider. Registry tiers are policy metadata,
            # not an empirical quality guarantee.
            if int(getattr(spec, "quality_tier", 0)) <= selected_quality:
                continue
            if route.network_mode == "offline" and provider != "local":
                continue
            if route.data_sensitivity == "restricted" and provider != "local":
                continue
            if allowed and provider not in allowed:
                continue
            # Never initialize a large local model solely for an escalation.
            if provider == "local":
                configured = (
                    candidate in self.gateway.available_models()
                    or candidate in self._fallback_adapters
                )
            else:
                configured = (
                    candidate in self.gateway.available_models()
                    or candidate in self._fallback_adapters
                    or provider_configured(spec.provider)
                )
            if configured:
                candidates.append(candidate)

        def generate_candidate(candidate: str) -> Dict[str, Any]:
            adapter = self._get_fallback_adapter(candidate)
            if adapter is None:
                raise RuntimeError("No configured adapter for candidate")
            return adapter.generate(
                user_text=user_text,
                intent=intent,
                verified_result=working_result,
                source=source,
                language=language,
                persona=persona,
                max_new_tokens=max_new_tokens,
            )

        def verify_candidate(response_text: str):
            return (
                self._verify_response(
                    response_text, intent, working_result, source
                ),
                self._verify_claims(
                    response_text, intent, working_result, source
                ),
            )

        result = verifier_gated_escalate(
            candidates=candidates,
            generate=generate_candidate,
            verify=verify_candidate,
            max_attempts=self.max_verifier_escalations,
        )
        if result.get("status") != "GENERATED_VERIFIED_ESCALATED":
            metadata = result.get("verification_escalation", {})
            metadata["evidence_retrieval_attempted"] = retrieval_attempted
            if retrieval_error_type:
                metadata["evidence_retrieval_error_type"] = retrieval_error_type
            result["verification_escalation"] = metadata
            return result if metadata.get("attempted") or retrieval_attempted else None
        result["verification_escalation"]["from_model"] = selected_model
        result["verification_escalation"]["evidence_retrieval_attempted"] = retrieval_attempted
        if retrieval_error_type:
            result["verification_escalation"]["evidence_retrieval_error_type"] = retrieval_error_type
        return result

    def generate(
        self,
        user_text: str,
        intent: str,
        verified_result: Dict[str, Any],
        source: str,
        language: str = "English",
        persona: str = "neutral",
        max_new_tokens: int = 160,
        model_id: Optional[str] = None,
        risk_level: str = "low",
        network_mode: Optional[str] = None,
        data_sensitivity: Optional[str] = None,
        allowed_providers: Optional[list[str]] = None,
    ) -> Dict[str, Any]:

        capability = self.CAPABILITY_BY_INTENT.get(
            intent,
            "response_generation",
        )
        runtime_network_mode = (
            network_mode
            or __import__("os").getenv("FINAI_NETWORK_MODE", "online")
        )
        runtime_data_sensitivity = (
            data_sensitivity
            or __import__("os").getenv("FINAI_DATA_SENSITIVITY", "standard")
        )
        configured_providers = __import__("os").getenv(
            "FINAI_ALLOWED_PROVIDERS",
            "",
        )
        runtime_allowed_providers = (
            allowed_providers
            if allowed_providers is not None
            else [
                item.strip()
                for item in configured_providers.split(",")
                if item.strip()
            ]
        )
        task_route = self.task_router.route(
            intent=intent,
            user_text=user_text,
            source=source,
            base_capability=capability,
            risk_level=risk_level,
            language=language,
            explicit_model=model_id,
            network_mode=runtime_network_mode,
            data_sensitivity=runtime_data_sensitivity,
            allowed_providers=runtime_allowed_providers,
        )
        route = task_route.route
        capability = task_route.capability
        selected_model = route.selected_model

        result = self._generate_with_provider_fallback(
            selected_model=selected_model,
            explicit_model=model_id is not None,
            capability=capability,
            user_text=user_text,
            intent=intent,
            verified_result=verified_result,
            source=source,
            language=language,
            persona=persona,
            max_new_tokens=max_new_tokens,
            network_mode=route.network_mode,
            data_sensitivity=route.data_sensitivity,
            allowed_providers=route.allowed_providers,
        )

        actual_selected_model = str(
            result.get("model_id", selected_model)
        )

        result = self._retry_truncated_generation(
            result=result,
            selected_model=actual_selected_model,
            user_text=user_text,
            intent=intent,
            verified_result=verified_result,
            source=source,
            language=language,
            persona=persona,
            max_new_tokens=max_new_tokens,
        )

        if result.get("status") == "INCOMPLETE_GENERATION":
            incomplete_message = (
                "I couldn't complete the generated response. "
                "Please retry the request."
            )

            return {
                **result,
                "status": "INCOMPLETE_GENERATION",
                "response": incomplete_message,
                "original_response": str(
                    result.get("response", "")
                ).strip(),
                "verification": {
                    "applicable": False,
                    "passed": False,
                    "mode": "GENERATION_COMPLETENESS",
                    "missing_values": [],
                    "semantic_errors": [],
                },
                "claim_verification": {
                    "applicable": False,
                    "passed": False,
                    "report": None,
                    "claims": [],
                },
                "task_routing": task_route.to_dict(),
                "selection": {
                    "capability": capability,
                    "model_id": selected_model,
                    "actual_model_id": actual_selected_model,
                    "fallback_used": bool(
                        result.get("fallback_used", False)
                    ),
                    "task_type": task_route.task_type,
                    "selection_reason": task_route.selection_reason,
                },
            }

        response = str(
            result.get("response", "")
        ).strip()

        verification = self._verify_response(
            response=response,
            intent=intent,
            verified_result=verified_result,
            source=source,
        )

        claim_verification = self._verify_claims(
            response=response,
            intent=intent,
            verified_result=verified_result,
            source=source,
        )

        response_failed = (
            verification["applicable"]
            and not verification["passed"]
        )

        claims_failed = (
            claim_verification["applicable"]
            and not claim_verification["passed"]
        )

        actual_model_id = (
            selected_model
            if model_id is not None
            else str(
                result.get(
                    "model_id",
                    selected_model,
                )
            )
        )

        if response_failed or claims_failed:

            escalation = self._try_verifier_escalation(
                selected_model=actual_model_id,
                explicit_model=model_id is not None,
                route=route,
                capability=capability,
                user_text=user_text,
                intent=intent,
                verified_result=verified_result,
                source=source,
                language=language,
                persona=persona,
                max_new_tokens=max_new_tokens,
                initial_response=response,
                verification=verification,
                claim_verification=claim_verification,
            )
            if escalation and escalation.get("status") in {
                "GENERATED_VERIFIED_ESCALATED",
                "GENERATED_VERIFIED_AFTER_RETRIEVAL",
            }:
                escalation["task_routing"] = task_route.to_dict()
                escalation["selection"] = {
                    "capability": capability,
                    "model_id": selected_model,
                    "actual_model_id": escalation.get("model_id", selected_model),
                    "fallback_used": escalation.get("status") == "GENERATED_VERIFIED_ESCALATED",
                    "task_type": task_route.task_type,
                    "selection_reason": task_route.selection_reason,
                    "verification_escalation": True,
                }
                return escalation

            if source == "retrieval_evidence":
                return {
                    **result,
                    "status": "VERIFICATION_FAILED",
                    "model_id": actual_model_id,
                    "response": (
                        "I couldn't verify the generated explanation "
                        "against the retrieved evidence."
                    ),
                    "original_response": response,
                    "verification": verification,
                    "claim_verification": claim_verification,
                    "verification_escalation": (
                        escalation.get("verification_escalation")
                        if escalation else {
                            "attempted": False,
                            "accepted": False,
                            "reason": "no eligible configured candidate",
                        }
                    ),
                    "task_routing": task_route.to_dict(),
                    "selection": {
                        "capability": capability,
                        "model_id": selected_model,
                        "actual_model_id": actual_model_id,
                        "fallback_used": bool(result.get("fallback_used", False)),
                        "route_reason": route.reason,
                        "route_policy": route.policy,
                        "route_risk_level": route.risk_level,
                        "route_fallback_candidates": list(route.fallback_chain),
                        "task_type": task_route.task_type,
                        "selection_reason": task_route.selection_reason,
                    },
                }

            fallback = self._build_verified_fallback(
                user_text=user_text,
                intent=intent,
                verified_result=verified_result,
                source=source,
                persona=persona,
            )

            return {
                "status": "FALLBACK_VERIFIED",
                "model_id": selected_model,
                "source": source,
                "language": language,
                "persona": persona,
                "response": fallback["response"],
                "verification": verification,
                "claim_verification": claim_verification,
                "fallback_verification": (
                    fallback["verification"]
                ),
                "fallback_claim_verification": (
                    fallback["claim_verification"]
                ),
                "original_response": response,
                "verification_escalation": (
                    escalation.get("verification_escalation")
                    if escalation else {
                        "attempted": False,
                        "accepted": False,
                        "reason": "no eligible configured candidate",
                    }
                ),
                "task_routing": task_route.to_dict(),
                "selection": {
                    "capability": capability,
                    "model_id": selected_model,
                    "route_reason": route.reason,
                    "route_policy": route.policy,
                    "route_risk_level": route.risk_level,
                    "route_fallback_candidates": list(route.fallback_chain),
                    "task_type": task_route.task_type,
                    "selection_reason": task_route.selection_reason,
                },
            }

        status = (
            "GENERATED_VERIFIED"
            if (
                verification["applicable"]
                or claim_verification["applicable"]
            )
            else "GENERATED"
        )

        # Explicit model selection is authoritative. This preserves
        # deterministic model_id behavior even when a test double or
        # adapter returns a different model_id.

        return {
            **result,
            "status": status,
            "model_id": actual_model_id,
            "verification": verification,
            "claim_verification": claim_verification,
            "task_routing": task_route.to_dict(),
            "selection": {
                "capability": capability,
                "model_id": selected_model,
                "actual_model_id": actual_model_id,
                "fallback_used": bool(
                    result.get(
                        "fallback_used",
                        False,
                    )
                ),
                "task_type": task_route.task_type,
                "selection_reason": task_route.selection_reason,
            },
        }
