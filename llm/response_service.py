from typing import Any, Dict, Optional

from llm.model_gateway import ModelGateway
from llm.model_registry import enabled_models
from llm.response_verifier import FinancialResponseVerifier
from rag.evidence_verifier import RAGEvidenceVerifier
from response_engine.financial import FinancialResponseEngine
from xai.claim_extractor import FinancialClaimExtractor
from xai.claim_verifier import ClaimVerifier
from xai.claims import build_finance_claims

from llm.response_adapter import SarvamResponseAdapter
from llm.rllm_finqa_adapter import RLLMFinQAModelAdapter
from llm.cloud.gemini_adapter import GeminiResponseAdapter
from llm.cloud.openrouter_adapter import OpenRouterResponseAdapter


class ResponseService:

    CAPABILITY_BY_INTENT = {
        "EMI_QUERY": "financial_qa",
        "INTEREST_QUERY": "financial_qa",
        # Retrieval-grounded financial knowledge can use the local
        # financial-QA model when cloud providers are unavailable.
        "KYC_DOCUMENTS": "financial_qa",
        "FINANCIAL_GUIDANCE": "financial_qa",
    }

    ADAPTERS = {
        "gemini-cloud": GeminiResponseAdapter,
        "openrouter-cloud": OpenRouterResponseAdapter,
        "rllm-finqa-4b": RLLMFinQAModelAdapter,
        "sarvam-1": SarvamResponseAdapter,
    }

    FALLBACK_MODEL_IDS_BY_CAPABILITY = {
        "response_generation": (
            "openrouter-cloud",
        ),
        "financial_qa": (
            "openrouter-cloud",
            "rllm-finqa-4b",
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

    def select_model(self, intent: str) -> str:

        capability = self.CAPABILITY_BY_INTENT.get(
            intent,
            "response_generation",
        )

        candidates = [
            spec
            for spec in enabled_models()
            if capability in spec.capabilities
        ]

        if not candidates:
            raise RuntimeError(
                f"No enabled model supports capability "
                f"'{capability}'."
            )

        return candidates[0].model_id

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
    ) -> Dict[str, Any]:
        """Generate with capability-compatible provider fallbacks."""

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

            fallback_candidates = (
                self.FALLBACK_MODEL_IDS_BY_CAPABILITY.get(
                    capability,
                    (),
                )
            )

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
    ) -> Dict[str, Any]:

        selected_model = (
            model_id
            if model_id is not None
            else self.select_model(intent)
        )

        capability = self.CAPABILITY_BY_INTENT.get(
            intent,
            "response_generation",
        )

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
                "selection": {
                    "capability": capability,
                    "model_id": selected_model,
                    "actual_model_id": actual_selected_model,
                    "fallback_used": bool(
                        result.get("fallback_used", False)
                    ),
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

        if response_failed or claims_failed:

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
                    "selection": {
                        "capability": capability,
                        "model_id": selected_model,
                        "actual_model_id": actual_model_id,
                        "fallback_used": bool(
                            result.get("fallback_used", False)
                        ),
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
                "selection": {
                    "capability": capability,
                    "model_id": selected_model,
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

        return {
            **result,
            "status": status,
            "model_id": actual_model_id,
            "verification": verification,
            "claim_verification": claim_verification,
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
            },
        }
