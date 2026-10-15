from datetime import datetime, timedelta
import inspect
from pathlib import Path

from orchestrator.engine import FinAIOrchestrator
from router.domain_router import FinAIDomainRouter
from orchestrator.finance_dispatcher import FinanceDispatcher
from orchestrator.market_data_dispatcher import MarketDataDispatcher
from orchestrator.market_date_parser import parse_market_date_range
from orchestrator.market_operation_planner import (
    OP_ANALYTICS,
    OP_HISTORY,
    OP_QUOTE,
    plan_market_operations,
)
from orchestrator.risk_controller import RiskCapabilityController
from orchestrator.execution_plan import (
    Capability,
    CapabilityStateGraph,
    ExecutionMode,
    build_execution_plan,
)
import os
from uuid import uuid4

from policy.network_mode import get_network_mode


ROOT = Path(__file__).resolve().parents[1]


class FinAIHybridEngine:

    def __init__(self, response_service=None, rag_retriever=None):
        self.base_engine = FinAIOrchestrator()
        self.finance = FinanceDispatcher()
        self.controller = RiskCapabilityController()
        self.domain_router = FinAIDomainRouter()
        self.response_service = response_service

        # Lazily constructed because it can load an external market-data
        # provider. The dispatcher remains behind the provider abstraction.
        self.market_data = None

        # Inject a retriever in tests; construct the production retriever lazily.
        # This prevents GPU model loading during normal engine initialization.
        self.rag_retriever = rag_retriever

    def _get_rag_retriever(self):
        if self.rag_retriever is None:
            db_path = ROOT / "data" / "rag" / "finai_rag.db"
            index_path = (
                ROOT / "data" / "rag" / "embeddings" / "finai_rag.faiss"
            )
            document_ids_path = (
                ROOT / "data" / "rag" / "embeddings" / "document_ids.npy"
            )
            required_assets = (db_path, index_path, document_ids_path)
            missing_assets = [path for path in required_assets if not path.is_file()]
            if missing_assets:
                missing = ", ".join(str(path) for path in missing_assets)
                raise FileNotFoundError(
                    "FinAI RAG assets are incomplete: "
                    f"{missing}. First provide approved source chunks under "
                    "data/domain_chunks/, then run scripts/build_rag_index.py "
                    "and scripts/build_rag_faiss.py. Large datasets and generated "
                    "indexes are intentionally not downloaded automatically."
                )

            from rag.hybrid_retriever import HybridRetriever
            from llm.qwen_embedding_adapter import QwenEmbeddingAdapter

            # The adapter selects CUDA when it is available and otherwise uses CPU.
            # Avoid hard-coding CUDA on CPU-only clean clones.
            embedding_adapter = QwenEmbeddingAdapter(
                device=None,
                max_seq_length=640,
            )

            self.rag_retriever = HybridRetriever(
                db_path=db_path,
                faiss_index_path=index_path,
                document_ids_path=document_ids_path,
                embedding_adapter=embedding_adapter,
            )

        return self.rag_retriever

    @staticmethod
    def _format_rag_documents(documents):
        return [
            {
                "document_id": int(doc.document_id),
                "title": doc.title,
                "source": doc.source,
                "date": doc.date,
                "text": doc.text,
                "lexical_score": doc.lexical_score,
                "semantic_score": doc.semantic_score,
                "fused_score": doc.fused_score,
            }
            for doc in documents
        ]

    def _plan_to_dict(self, plan):
        return {
            "intent": plan.intent,
            "decision": plan.decision,
            "risk_level": plan.risk_level,
            "category": plan.category,
            "capability": plan.capability,
            "execution_class": plan.execution_class,
            "authority_class": plan.authority_class,
            "authority_source": plan.authority_source,
            "allowed_components": list(
                plan.allowed_components
            ),
            "authentication_required": (
                plan.authentication_required
            ),
            "confirmation_required": (
                plan.confirmation_required
            ),
            "tool": plan.tool,
            "llm_role": plan.llm_role,
            "verification_mode": plan.verification_mode,
        }

    @staticmethod
    def _generate_response(service, risk_level, **kwargs):
        """Call injected or production response services compatibly."""
        parameters = inspect.signature(service.generate).parameters
        if "risk_level" in parameters:
            kwargs["risk_level"] = risk_level
        return service.generate(**kwargs)

    def _get_market_data_dispatcher(self):
        if self.market_data is None:
            from market_data.providers.yfinance_provider import (
                YFinanceProvider,
            )
            from market_data.service import MarketDataService

            service = MarketDataService(
                providers={
                    "yfinance": YFinanceProvider(),
                },
                default_provider="yfinance",
            )

            self.market_data = MarketDataDispatcher(service)

        return self.market_data
    @staticmethod
    def _provider_configured() -> bool:
        """Return whether any supported cloud response provider has a key configured."""
        key_names = (
            "OPENAI_API_KEY",
            "OPENROUTER_API_KEY",
            "ANTHROPIC_API_KEY",
            "MISTRAL_API_KEY",
            "GOOGLE_API_KEY",
            "GEMINI_API_KEY",
            "SARVAM_API_KEY",
        )
        return any(bool(os.getenv(name, "").strip()) for name in key_names)

    def _capability_plan_for_result(
        self,
        *,
        result: dict,
        request_id: str,
        user_text: str,
        generate_response: bool,
    ) -> dict:
        """Attach an auditable, non-authorizing capability plan to every engine result.

        The existing router, policy engine, authority contract, and risk controller
        remain the enforcement points. This plan diagnoses the path and its currently
        observed capabilities; it does not authorize or execute tools itself.
        """
        router = result.get("router") or {}
        legacy_plan = result.get("execution_plan") or {}
        intent = str(router.get("intent") or "UNCLASSIFIED")
        stage = str(result.get("stage") or "")
        status = str(result.get("status") or "")
        generation = result.get("response_generation")
        generation = generation if isinstance(generation, dict) else {}
        generation_status = str(generation.get("status") or "")
        verification = generation.get("verification")
        verification_observed = (
            isinstance(verification, dict)
            or generation_status in {
                "GENERATED_VERIFIED",
                "VERIFICATION_FAILED",
                "INCOMPLETE_GENERATION",
            }
        )
        # Distinguish capabilities that exist on the machine from stages that
        # belong in this request's observed execution path.
        needs_retrieval = (
            str(legacy_plan.get("capability") or "") == "rag"
            and stage == "rag"
        )
        needs_generation = (
            bool(generate_response)
            and stage in {"finance_engine", "rag", "financial_knowledge"}
            and status not in {
                "MISSING_PARAMETERS", "RAG_ERROR", "NO_EVIDENCE",
            }
        )
        needs_market_data = (
            stage == "market_data"
            or str(legacy_plan.get("capability") or "") == "market_data"
        )
        needs_structured_knowledge = stage == "financial_knowledge"

        rag_paths = (
            ROOT / "data" / "rag" / "finai_rag.db",
            ROOT / "data" / "rag" / "embeddings" / "finai_rag.faiss",
            ROOT / "data" / "rag" / "embeddings" / "document_ids.npy",
        )
        retrieval_available = (
            getattr(self, "rag_retriever", None) is not None
            or all(path.exists() for path in rag_paths)
        )
        response_service_available = (
            getattr(self, "response_service", None) is not None
            or self._provider_configured()
        )
        generation_failed = generation_status in {
            "PROVIDER_UNAVAILABLE",
            "MODEL_UNAVAILABLE",
            "GENERATION_ERROR",
        }
        model_available = needs_generation and (
            bool(generation) and not generation_failed
            if generate_response and stage in {
                "finance_engine", "rag", "financial_knowledge"
            } and status != "MISSING_PARAMETERS"
            else response_service_available
        )
        verification_available = needs_generation and (
            verification_observed
            if generate_response and generation
            else verification_observed
        )

        all_modes = tuple(ExecutionMode)
        online_only = (ExecutionMode.ONLINE, ExecutionMode.DEGRADED)
        mode = ExecutionMode(get_network_mode())
        # A successful observed generation is evidence that the selected local
        # or remote path ran. Mere credentials/configuration never prove that.
        model_modes = (
            all_modes
            if generation and not generation_failed
            else online_only
        )
        resource_planning_available = (
            (ROOT / "llm" / "resource_orchestrator.py").is_file()
            and (ROOT / "llm" / "model_router.py").is_file()
        )
        graph = CapabilityStateGraph(
            capabilities=(
                Capability(
                    "policy",
                    True,
                    all_modes,
                    metadata={"source": "existing_policy_and_risk_controller"},
                ),
                Capability(
                    "market_data",
                    needs_market_data,
                    all_modes,
                    reason="the observed request did not enter the market-data dispatcher",
                    metadata={"source": "market_data_dispatcher"},
                ),
                Capability(
                    "deterministic_finance",
                    getattr(self, "finance", None) is not None,
                    all_modes,
                    reason="deterministic finance dispatcher is not initialized",
                    metadata={"source": "finance_dispatcher"},
                ),
                Capability(
                    "structured_knowledge",
                    needs_structured_knowledge,
                    all_modes,
                    reason="the observed request did not use the structured finance knowledge path",
                    metadata={"source": "financial catalog, encyclopedia, compliance and investment eligibility"},
                ),
                Capability(
                    "retrieval",
                    retrieval_available and needs_retrieval,
                    all_modes if retrieval_available and needs_retrieval else online_only,
                    reason=(
                        "RAG retriever or all required local index artifacts are unavailable"
                        if needs_retrieval
                        else "retrieval is not required by the observed request path"
                    ),
                    metadata={"source": "hybrid_rrf", "requested_for_path": needs_retrieval},
                ),
                Capability(
                    "resource_planning",
                    resource_planning_available,
                    all_modes,
                    reason="hardware-aware model/resource planner is not available",
                    metadata={"source": "llm.resource_orchestrator and llm.model_router"},
                ),
                Capability(
                    "model_generation",
                    model_available,
                    model_modes,
                    reason="no usable response generation result or provider configuration was observed",
                    metadata={"source": "injected response service or server-side provider configuration"},
                ),
                Capability(
                    "claim_verification",
                    verification_available,
                    all_modes,
                    reason="this request did not produce an observable claim-verification result",
                    metadata={"observed": verification_observed},
                ),
                Capability(
                    "response_verification",
                    verification_available,
                    all_modes,
                    reason="this request did not produce an observable response-verification result",
                    metadata={"observed": verification_observed},
                ),
            ),
            prerequisites={
                "market_data": ("policy",),
                "deterministic_finance": ("policy",),
                "structured_knowledge": ("policy",),
                "retrieval": ("policy",),
                "resource_planning": ("policy",),
                "model_generation": ("policy", "resource_planning"),
                "claim_verification": ("model_generation",),
                "response_verification": ("claim_verification",),
            },
        )
        plan = build_execution_plan(
            request_id=request_id,
            intent=intent,
            graph=graph,
            mode=mode,
            require_retrieval=needs_retrieval,
            require_market_data=needs_market_data,
            require_structured_knowledge=needs_structured_knowledge,
            require_resource_planning=needs_generation,
            require_model=needs_generation,
            require_claim_verification=needs_generation,
            require_response_verification=needs_generation,
        ).to_dict()

        # Keep the planner separate from enforcement, but annotate the plan with
        # what this request actually exposed so the UI cannot imply that a
        # planned stage necessarily executed successfully.
        policy_result = result.get("policy") or {}
        policy_status = str(policy_result.get("status") or "")
        if stage == "policy" or status in {
            "AUTH_REQUIRED", "CONFIRMATION_REQUIRED", "SECURITY_REVIEW_REQUIRED",
        }:
            observed_policy = status or policy_status or "BLOCKED_OR_PENDING"
        elif policy_status:
            observed_policy = policy_status
        else:
            observed_policy = "NOT_OBSERVED"

        finance_result = result.get("finance") or {}
        if stage == "finance_engine":
            observed_finance = str(finance_result.get("status") or status or "OBSERVED")
        elif not any(
            token in intent.lower()
            for token in (
                "calculate", "calculation", "emi", "loan", "budget",
                "portfolio", "payment", "interest", "tax", "sip",
                "compound", "fixed_deposit", "recurring_deposit",
                "finance_engine", "financial_calculation",
            )
        ):
            observed_finance = "NOT_REQUIRED"
        else:
            observed_finance = "NOT_OBSERVED"

        rag_result = result.get("rag") or {}
        if status == "RAG_ERROR":
            observed_retrieval = "FAILED"
        elif status == "NO_EVIDENCE":
            observed_retrieval = "NO_EVIDENCE"
        elif stage == "rag":
            observed_retrieval = (
                "EVIDENCE_FOUND"
                if rag_result.get("documents")
                else "OBSERVED"
            )
        elif not needs_retrieval:
            observed_retrieval = "NOT_REQUIRED"
        else:
            observed_retrieval = "NOT_OBSERVED"

        claim_result = generation.get("claim_verification")
        response_verification_result = generation.get("verification")
        if not generate_response:
            observed_generation = "NOT_REQUESTED"
        elif generation_status in {"PROVIDER_UNAVAILABLE", "MODEL_UNAVAILABLE", "GENERATION_ERROR"}:
            observed_generation = "FAILED"
        elif generation:
            observed_generation = generation_status or "OBSERVED"
        elif status in {"MISSING_PARAMETERS", "RAG_ERROR", "NO_EVIDENCE"}:
            observed_generation = "NOT_REACHED"
        else:
            observed_generation = "NOT_OBSERVED"

        def verification_status(value):
            if not isinstance(value, dict):
                return "NOT_OBSERVED"
            if value.get("applicable") is False:
                return "NOT_APPLICABLE"
            if isinstance(value.get("passed"), bool):
                return "PASSED" if value["passed"] else "FAILED"
            return "NOT_OBSERVED"

        observed_by_capability = {
            "policy": observed_policy,
            "market_data": status if stage == "market_data" else "NOT_REQUIRED",
            "deterministic_finance": observed_finance,
            "structured_knowledge": status if stage == "financial_knowledge" else "NOT_REQUIRED",
            "retrieval": observed_retrieval,
            "resource_planning": (
                "OBSERVED"
                if isinstance(generation.get("selection"), dict)
                else "NOT_OBSERVED"
            ),
            "model_generation": observed_generation,
            "claim_verification": verification_status(claim_result),
            "response_verification": verification_status(response_verification_result),
        }
        for step in plan.get("steps", []):
            step["observed_status"] = observed_by_capability.get(
                step.get("capability"), "NOT_OBSERVED"
            )

        plan["request_outcome"] = status or "UNKNOWN"
        plan["request_outcome_stage"] = stage or "UNKNOWN"
        plan["planner_role"] = "request_path_diagnostic"
        plan["enforcement"] = (
            "Existing routing, policy, authority, and risk-control layers remain authoritative."
        )
        plan["observed_stage"] = stage or None
        plan["observed_status"] = status or None
        return plan

    def process(
        self,
        user_text: str,
        authenticated: bool = False,
        confirmed: bool = False,
        account_id: str = "ACC1001",
        card_id: str = "CARD1001",
        transaction_id: str = "TXN002",
        upi_id: str = "UPI1001",
        transfer_id: str = "TRF1001",
        refund_id: str = "REF1001",
        generate_response: bool = False,
        language: str = "English",
        persona: str = "neutral",
        max_new_tokens: int = 256,
        model_id: str | None = None,
    ):
        request_id = uuid4().hex
        result = self._process_core(
            user_text=user_text,
            authenticated=authenticated,
            confirmed=confirmed,
            account_id=account_id,
            card_id=card_id,
            transaction_id=transaction_id,
            upi_id=upi_id,
            transfer_id=transfer_id,
            refund_id=refund_id,
            generate_response=generate_response,
            language=language,
            persona=persona,
            max_new_tokens=max_new_tokens,
            model_id=model_id,
        )
        result = dict(result)
        result["capability_execution_plan"] = self._capability_plan_for_result(
            result=result,
            request_id=request_id,
            user_text=user_text,
            generate_response=generate_response,
        )
        return result

    def _process_core(
        self,
        user_text: str,
        authenticated: bool = False,
        confirmed: bool = False,
        account_id: str = "ACC1001",
        card_id: str = "CARD1001",
        transaction_id: str = "TXN002",
        upi_id: str = "UPI1001",
        transfer_id: str = "TRF1001",
        refund_id: str = "REF1001",
        generate_response: bool = False,
        language: str = "English",
        persona: str = "neutral",
        max_new_tokens: int = 256,
        model_id: str | None = None,
    ):

        # ---------------------------------------------------------
        # Existing router/policy/session pipeline.
        # ---------------------------------------------------------

        base_result = self.base_engine.process(
            user_text=user_text,
            authenticated=authenticated,
            confirmed=confirmed,
            account_id=account_id,
            card_id=card_id,
            transaction_id=transaction_id,
            upi_id=upi_id,
            transfer_id=transfer_id,
            refund_id=refund_id,
        )

        router = base_result.get("router") or {}

        classified_intent = router.get("intent")

        # ---------------------------------------------------------
        # Second-stage scalable domain routing.
        # ---------------------------------------------------------

        domain_route = self.domain_router.route(
            user_text,
            classified_intent=classified_intent,
        )

        domain = domain_route.get("domain")

        router = dict(router)
        router["classified_intent"] = classified_intent
        router["domain"] = domain
        router["domain_reason"] = domain_route.get("reason")
        router["domain_source"] = domain_route.get("source")

        intent = classified_intent

        # Promote clear market-data requests to the dedicated
        # market-data execution intent.
        if domain == "MARKET_DATA":
            intent = "MARKET_DATA_QUERY"
            router["intent"] = intent
            router["intent_source"] = "domain_router"

            # A clearly recognized market-data request is a valid
            # read-only route even when the legacy 50-class classifier
            # could not classify it.
            router["decision"] = "ROUTE"
            router["risk_level"] = "low"

        router_decision = router.get(
            "decision",
            "REJECT",
        )

        # ---------------------------------------------------------
        # NEW: Risk / Capability execution planning.
        #
        # This layer plans the execution path.
        # It does NOT execute tools or models.
        # ---------------------------------------------------------

        plan = self.controller.build_plan(
            intent=intent,
            router_decision=router_decision,
        )

        execution_plan = self._plan_to_dict(plan)

        # ---------------------------------------------------------
        # RAG / retrieved-knowledge path.
        #
        # The router and authority controller decide that the request
        # requires retrieved evidence. The retriever supplies evidence;
        # the LLM does not become the authority.
        # ---------------------------------------------------------
        if (
            plan.decision == "EXECUTE"
            and plan.capability == "rag"
            and intent in {
                "FINANCIAL_PRODUCT_KNOWLEDGE",
                "FINANCIAL_GUIDANCE",
            }
        ):
            # Common product concepts use structured, curated knowledge first.
            # This avoids slow generative routing for straightforward definitions
            # and makes the authority chain explicit.
            from knowledge.financial_catalog import build_answer as build_catalog_answer
            from knowledge.finance_encyclopedia import build_answer as build_encyclopedia_answer
            from compliance_catalog import find_items
            from knowledge.india_finance_regulation import search_regulations
            from knowledge.investment_eligibility import search_investment_routes

            # Keep the structured knowledge path resilient: one optional
            # catalogue must not take down a valid finance explanation.
            try:
                catalog_result = build_catalog_answer(user_text)
            except Exception:
                catalog_result = {"found": False, "matches": [], "answer": ""}
            try:
                encyclopedia_result = build_encyclopedia_answer(user_text)
            except Exception:
                encyclopedia_result = {
                    "found": False,
                    "matches": [],
                    "answer": "",
                    "requires_current_data": False,
                }
            try:
                compliance_results = find_items(user_text)
            except Exception:
                compliance_results = []
            try:
                regulatory_results = search_regulations(user_text)
            except Exception:
                regulatory_results = []
            try:
                investment_route_results = search_investment_routes(user_text)
            except Exception:
                investment_route_results = []

            compliance_hint = any(
                term in user_text.lower()
                for term in (
                    "itr", "tax form", "tax forms", "tds", "form 16",
                    "form 16a", "26as", "ais", "15g", "15h", "form 67",
                    "gstr", "gst", "capital gains",
                )
            )

            investment_route_hint = any(
                term in user_text.lower()
                for term in (
                    "resident indian", "resident india", "nri",
                    "non-resident indian", "non resident indian", "oci",
                    "investment avenues", "where can i invest",
                    "invest in india", "invest outside india",
                    "lrs", "nre", "nro", "fcnr", "ppf", "small savings",
                    "government securities", "reit", "invit", "pms", "aif",
                    "fdi", "fpi", "foreign investment",
                )
            )

            regulatory_hint = any(
                term in user_text.lower()
                for term in (
                    "sebi", "listing", "ipo", "sme ipo", "innovators growth",
                    "foreign investment", "fdi", "fpi", "nri", "oci", "ifsc",
                    "etf", "aif", "create a crypto", "create cryptocurrency",
                    "create token", "mining", "proof of work",
                )
            )

            if investment_route_hint and investment_route_results:
                route = investment_route_results[0]
                investment_answer = (
                    f"{route['avenue']}\\n"
                    f"Resident India: {route['resident_status']}\\n"
                    f"NRI: {route['nri_status']}\\n\\n"
                    f"Resident route: {route['resident_route']}\\n"
                    f"NRI route: {route['nri_route']}\\n\\n"
                    "Key conditions:\\n"
                    + "\\n".join(f"- {condition}" for condition in route["key_conditions"])
                    + f"\\n\\nAuthority: {route['authority']}\\n"
                    f"Official source: {route['official_source']}\\n"
                    f"As of: {route['as_of']}\\n"
                    f"Accuracy note: {route['accuracy_note']}"
                )
                investment_route_knowledge = {
                    "answer": investment_answer,
                    "matches": [route],
                    "source": "resident_nri_investment_matrix",
                    "requires_current_data": True,
                }
            else:
                investment_route_knowledge = None

            if investment_route_knowledge:
                knowledge_result = investment_route_knowledge
            elif regulatory_hint and regulatory_results:
                item = regulatory_results[0]
                regulatory_answer = (
                    f"{item['title']}\\n{item['answer']}\\n\\n"
                    "Practical workflow:\\n"
                    + "\\n".join(f"- {step}" for step in item["steps"])
                    + f"\\n\\nAuthority: {item['authority']}\\n"
                    f"Official source: {item['official_url']}\\n"
                    f"Updated/source date: {item['updated']}\\n"
                    f"Caveat: {item['caveat']}"
                )
                regulatory_knowledge = {
                    "answer": regulatory_answer,
                    "matches": [item],
                    "source": "india_finance_regulation_catalog",
                    "requires_current_data": True,
                }
            else:
                regulatory_knowledge = None

            if regulatory_knowledge:
                knowledge_result = regulatory_knowledge
            elif compliance_hint and compliance_results:
                item = compliance_results[0]
                compliance_answer = (
                    f"{item['name']}\\n{item['purpose']}\\n\\n"
                    f"Who uses it: {item['who_uses_it']}\\n"
                    f"Key inputs: {', '.join(item['key_inputs'])}\\n\\n"
                    "Execution workflow:\\n"
                    + "\\n".join(
                        f"- {step}" for step in item["workflow"]
                    )
                    + f"\\n\\nOfficial source: {item['official_url']}\\n"
                    f"Source: {item['source_name']}\\n"
                    f"Note: {item['status_note']}"
                )
                compliance_knowledge = {
                    "answer": compliance_answer,
                    "matches": [item],
                    "source": "compliance_catalog",
                    "requires_current_data": True,
                }
            else:
                compliance_knowledge = None

            # Use the encyclopedia for mechanics/history/crypto protocol
            # questions because it contains deeper "how it works" coverage.
            # Keep the focused catalog for product-specific scheme concepts.
            mechanics_hint = any(
                term in user_text.lower()
                for term in (
                    "history", "how", "works", "mechanism", "why",
                    "bitcoin", "blockchain", "proof of work", "proof of stake",
                    "stablecoin", "defi", "order book", "repo",
                    "futures", "options", "yield curve", "arbitrage",
                )
            )

            if compliance_knowledge:
                knowledge_result = compliance_knowledge
            elif encyclopedia_result["found"] and mechanics_hint:
                knowledge_result = {
                    "answer": encyclopedia_result["answer"],
                    "matches": encyclopedia_result["matches"],
                    "source": "finance_encyclopedia",
                    "requires_current_data": encyclopedia_result["requires_current_data"],
                }
            elif catalog_result["found"]:
                knowledge_result = {
                    "answer": catalog_result["answer"],
                    "matches": catalog_result["matches"],
                    "source": "structured_financial_catalog",
                    "requires_current_data": False,
                }
            elif encyclopedia_result["found"]:
                knowledge_result = {
                    "answer": encyclopedia_result["answer"],
                    "matches": encyclopedia_result["matches"],
                    "source": "finance_encyclopedia",
                    "requires_current_data": encyclopedia_result["requires_current_data"],
                }
            else:
                knowledge_result = None

            if knowledge_result:
                final_response = knowledge_result["answer"]
                response_generation = None

                if generate_response:
                    try:
                        from llm.response_service import ResponseService

                        response_generation = self._generate_response(
                            (self.response_service or ResponseService()),
                            risk_level=plan.risk_level,
                            user_text=user_text,
                            intent=intent,
                            verified_result={
                                "knowledge_answer": knowledge_result["answer"],
                                "topics": knowledge_result["matches"],
                            },
                            source=knowledge_result["source"],
                            language=language,
                            persona=persona,
                            max_new_tokens=max_new_tokens,
                            model_id=model_id,
                            )
                        generated = str(response_generation.get("response", "")).strip()
                        if generated:
                            final_response = generated
                    except Exception:
                        # The verified deterministic knowledge answer remains the
                        # safe fallback when no generation provider is available.
                        response_generation = None

                return {
                    "stage": "financial_knowledge",
                    "status": "KNOWLEDGE_RETRIEVED",
                    "user_text": user_text,
                    "router": router,
                    "execution_plan": execution_plan,
                    "policy": {
                        "status": "ALLOWED",
                        "risk_level": plan.risk_level,
                        "authentication_required": plan.authentication_required,
                        "confirmation_required": plan.confirmation_required,
                        "tool": plan.tool,
                    },
                    "knowledge": {
                        "source": knowledge_result["source"],
                        "matches": knowledge_result["matches"],
                        "answer": knowledge_result["answer"],
                        "requires_current_data": knowledge_result["requires_current_data"],
                    },
                    "tool": None,
                    "message": final_response,
                    "response": final_response,
                    "response_generation": response_generation,
                    "timestamp": datetime.now().isoformat(),
                }

        if (
            plan.decision == "EXECUTE"
            and plan.capability == "rag"
        ):
            try:
                retriever = self._get_rag_retriever()
                documents = retriever.retrieve(
                    user_text,
                    top_k=5,
                )
            except Exception as exc:
                return {
                    "stage": "rag",
                    "status": "RAG_ERROR",
                    "user_text": user_text,
                    "router": router,
                    "execution_plan": execution_plan,
                    "policy": {
                        "status": "ALLOWED",
                        "risk_level": plan.risk_level,
                        "authentication_required": (
                            plan.authentication_required
                        ),
                        "confirmation_required": (
                            plan.confirmation_required
                        ),
                        "tool": plan.tool,
                    },
                    "rag": {
                        "query": user_text,
                        "retrieval_method": "hybrid_rrf",
                        "documents": [],
                        "error": str(exc),
                    },
                    "tool": None,
                    "message": "Knowledge retrieval is currently unavailable.",
                    "response": "Knowledge retrieval is currently unavailable.",
                    "timestamp": datetime.now().isoformat(),
                }

            formatted_documents = self._format_rag_documents(documents)

            if not formatted_documents:
                return {
                    "stage": "rag",
                    "status": "NO_EVIDENCE",
                    "user_text": user_text,
                    "router": router,
                    "execution_plan": execution_plan,
                    "policy": {
                        "status": "ALLOWED",
                        "risk_level": plan.risk_level,
                        "authentication_required": (
                            plan.authentication_required
                        ),
                        "confirmation_required": (
                            plan.confirmation_required
                        ),
                        "tool": plan.tool,
                    },
                    "rag": {
                        "query": user_text,
                        "retrieval_method": "hybrid_rrf",
                        "documents": [],
                    },
                    "tool": None,
                    "message": (
                        "I could not retrieve supporting evidence "
                        "for this request."
                    ),
                    "response": (
                        "I could not retrieve supporting evidence "
                        "for this request."
                    ),
                    "timestamp": datetime.now().isoformat(),
                }

            # ---------------------------------------------------------
            # Optional response-generation path.
            #
            # Retrieval remains authoritative. The response model only
            # explains the retrieved evidence.
            # ---------------------------------------------------------

            response_result = None

            if generate_response:

                from llm.response_service import ResponseService

                service = (
                    self.response_service
                    or ResponseService()
                )

                verified_evidence = {
                    "query": user_text,
                    "evidence_count": len(formatted_documents),
                    "documents": formatted_documents,
                }

                response_result = self._generate_response(
                    service,
                    risk_level=plan.risk_level,
                    user_text=user_text,
                    intent=intent,
                    verified_result=verified_evidence,
                    source="retrieval_evidence",
                    language=language,
                    persona=persona,
                    max_new_tokens=max_new_tokens,
                    model_id=model_id,
                )

            final_response = (
                response_result["response"]
                if response_result
                else "Supporting evidence retrieved successfully."
            )

            rag_status = "RETRIEVED"
            if response_result:
                generation_status = response_result.get("status")
                if generation_status in {
                    "VERIFICATION_FAILED",
                    "INCOMPLETE_GENERATION",
                }:
                    rag_status = generation_status

            return {
                "stage": "rag",
                "status": rag_status,
                "user_text": user_text,
                "router": router,
                "execution_plan": execution_plan,
                "policy": {
                    "status": "ALLOWED",
                    "risk_level": plan.risk_level,
                    "authentication_required": (
                        plan.authentication_required
                    ),
                    "confirmation_required": (
                        plan.confirmation_required
                    ),
                    "tool": plan.tool,
                },
                "rag": {
                    "query": user_text,
                    "retrieval_method": "hybrid_rrf",
                    "top_k": 5,
                    "documents": formatted_documents,
                    "evidence_count": len(formatted_documents),
                },
                "tool": None,
                "message": final_response,
                "response": final_response,
                "response_generation": response_result,
                "timestamp": datetime.now().isoformat(),
            }


        # ---------------------------------------------------------
        # Market-data execution path.
        #
        # Market data is authoritative from the configured provider.
        # The LLM may explain the returned structured result, but it
        # does not invent market values.
        # ---------------------------------------------------------

        if (
            plan.decision == "EXECUTE"
            and plan.capability == "market_data"
        ):
            dispatcher = self._get_market_data_dispatcher()

            normalized_text = user_text.lower()

            # Resolve the first supported instrument mentioned
            # in the user's request.
            instrument_query = None

            for instrument in dispatcher.resolver.instruments:
                candidates = (
                    instrument.aliases
                    + (instrument.display_name,)
                    + (instrument.instrument_id,)
                )

                if any(
                    str(candidate).lower() in normalized_text
                    for candidate in candidates
                ):
                    instrument_query = instrument.display_name
                    break

            if instrument_query is None:
                return {
                    "stage": "market_data",
                    "status": "CLARIFICATION_REQUIRED",
                    "user_text": user_text,
                    "router": router,
                    "execution_plan": execution_plan,
                    "policy": {
                        "status": "ALLOWED",
                        "risk_level": plan.risk_level,
                        "authentication_required": (
                            plan.authentication_required
                        ),
                        "confirmation_required": (
                            plan.confirmation_required
                        ),
                        "tool": plan.tool,
                    },
                    "market_data": None,
                    "tool": None,
                    "message": (
                        "Which financial instrument would you "
                        "like me to look up?"
                    ),
                    "response": (
                        "Which financial instrument would you "
                        "like me to look up?"
                    ),
                    "timestamp": datetime.now().isoformat(),
                }

            operation_plan = plan_market_operations(user_text)

            date_range = None
            start = None
            end = None

            if any(
                operation in operation_plan.operations
                for operation in (OP_HISTORY, OP_ANALYTICS)
            ):
                date_range = parse_market_date_range(user_text)
                start = date_range.start
                end = date_range.end

            operation_results = []

            try:
                for operation in operation_plan.operations:

                    if operation == OP_QUOTE:
                        operation_results.append(
                            dispatcher.quote(
                                instrument_query,
                            )
                        )

                    elif operation == OP_HISTORY:
                        operation_results.append(
                            dispatcher.history(
                                instrument_query,
                                start=start,
                                end=end,
                            )
                        )

                    elif operation == OP_ANALYTICS:
                        operation_results.append(
                            dispatcher.analytics(
                                instrument_query,
                                start=start,
                                end=end,
                            )
                        )

                    else:
                        raise ValueError(
                            f"Unsupported market operation: {operation}"
                        )

            except ValueError as exc:
                return {
                    "stage": "market_data",
                    "status": "CLARIFICATION_REQUIRED",
                    "user_text": user_text,
                    "router": router,
                    "execution_plan": execution_plan,
                    "policy": {
                        "status": "ALLOWED",
                        "risk_level": plan.risk_level,
                        "authentication_required": (
                            plan.authentication_required
                        ),
                        "confirmation_required": (
                            plan.confirmation_required
                        ),
                        "tool": plan.tool,
                    },
                    "market_data": None,
                    "tool": {
                        "tool": "market_data_dispatcher",
                        "success": False,
                    },
                    "message": str(exc),
                    "response": str(exc),
                    "timestamp": datetime.now().isoformat(),
                }

            except Exception as exc:
                return {
                    "stage": "market_data",
                    "status": "MARKET_DATA_ERROR",
                    "user_text": user_text,
                    "router": router,
                    "execution_plan": execution_plan,
                    "policy": {
                        "status": "ALLOWED",
                        "risk_level": plan.risk_level,
                        "authentication_required": (
                            plan.authentication_required
                        ),
                        "confirmation_required": (
                            plan.confirmation_required
                        ),
                        "tool": plan.tool,
                    },
                    "market_data": None,
                    "tool": {
                        "tool": "market_data_dispatcher",
                        "success": False,
                    },
                    "message": "Market data is currently unavailable.",
                    "response": "Market data is currently unavailable.",
                    "error": str(exc),
                    "timestamp": datetime.now().isoformat(),
                }

            market_data_result = {
                "operations": list(operation_plan.operations),
                "planning_reason": operation_plan.reason,
                "results": operation_results,
            }

            if date_range is not None:
                market_data_result["date_range_reason"] = date_range.reason
                market_data_result["range"] = {
                    "start": start,
                    "end": end,
                }

            return {
                "stage": "market_data",
                "status": "MARKET_DATA_RETRIEVED",
                "user_text": user_text,
                "router": router,
                "execution_plan": execution_plan,
                "policy": {
                    "status": "ALLOWED",
                    "risk_level": plan.risk_level,
                    "authentication_required": (
                        plan.authentication_required
                    ),
                    "confirmation_required": (
                        plan.confirmation_required
                    ),
                    "tool": plan.tool,
                },
                "market_data": market_data_result,
                "tool": {
                    "tool": "market_data_dispatcher",
                    "success": True,
                },
                "message": "Market data retrieved successfully.",
                "response": "Market data retrieved successfully.",
                "timestamp": datetime.now().isoformat(),
            }

        # ---------------------------------------------------------
        # Finance-specific deterministic path.
        # ---------------------------------------------------------

        if (
            plan.decision == "EXECUTE"
            and plan.capability == "finance_engine"
        ):

            finance_result = self.finance.dispatch(
                intent=intent,
                user_text=user_text,
            )

            if finance_result["handled"]:

                calculation = finance_result["result"]

                response_result = None

                if (
                    generate_response
                    and calculation["status"] == "CALCULATED"
                ):
                    from llm.response_service import ResponseService

                    service = (
                        self.response_service
                        or ResponseService()
                    )

                    response_result = self._generate_response(
                        service,
                        risk_level=plan.risk_level,
                        user_text=user_text,
                        intent=intent,
                        verified_result=calculation["result"],
                        source="deterministic_finance_engine",
                        language=language,
                        persona=persona,
                        max_new_tokens=max_new_tokens,
                        model_id=model_id,
                    )

                return {
                    "stage": "finance_engine",
                    "status": calculation["status"],
                    "user_text": user_text,

                    "router": router,

                    "execution_plan": execution_plan,

                    "policy": {
                        "status": "ALLOWED",
                        "risk_level": plan.risk_level,
                        "authentication_required": (
                            plan.authentication_required
                        ),
                        "confirmation_required": (
                            plan.confirmation_required
                        ),
                        "tool": plan.tool,
                    },

                    "finance": {
                        "operation": finance_result["operation"],
                        "status": calculation["status"],
                        "parameters": calculation["parameters"],
                        "missing": calculation["missing"],
                        "result": calculation["result"],
                        "source": (
                            "deterministic_finance_engine"
                        ),
                    },

                    "tool": None,

                    "message": calculation["message"],

                    "response": (
                        response_result["response"]
                        if response_result
                        else calculation["message"]
                    ),

                    "response_generation": response_result,

                    "timestamp": datetime.now().isoformat(),
                }

        # ---------------------------------------------------------
        # Existing banking/tool pipeline.
        #
        # Preserve its behavior, but expose the execution plan.
        # ---------------------------------------------------------

        result = dict(base_result)

        result["execution_plan"] = execution_plan

        return result


if __name__ == "__main__":

    engine = FinAIHybridEngine()

    tests = [
        {
            "name": "Complete EMI",
            "text": (
                "Calculate EMI for â‚¹10 lakh at "
                "8.5% for 20 years"
            ),
        },
        {
            "name": "Incomplete EMI",
            "text": "Calculate my EMI",
        },
        {
            "name": "Account balance",
            "text": "How much is my account balance?",
        },
        {
            "name": "UPI failure",
            "text": "My UPI payment failed",
        },
        {
            "name": "Ambiguous payment",
            "text": "The payment failed",
        },
        {
            "name": "Lost card",
            "text": "My card is lost",
        },
    ]

    print("=" * 80)
    print("FINAI HYBRID ENGINE + RISK CONTROLLER")
    print("=" * 80)

    for test in tests:

        print()
        print("-" * 80)
        print(test["name"])
        print("-" * 80)

        result = engine.process(
            user_text=test["text"],
            authenticated=True,
            confirmed=False,
        )

        print("USER:", test["text"])
        print("STATUS:", result["status"])
        print("STAGE:", result["stage"])

        print(
            "INTENT:",
            result.get("router", {}).get("intent")
        )

        print(
            "EXECUTION PLAN:",
            result.get("execution_plan")
        )

        if result.get("finance"):

            print(
                "FINANCE OPERATION:",
                result["finance"]["operation"]
            )

            print(
                "FINANCE STATUS:",
                result["finance"]["status"]
            )

            print(
                "FINANCE RESULT:",
                result["finance"]["result"]
            )

            print(
                "FINANCE SOURCE:",
                result["finance"]["source"]
            )

        if result.get("tool"):

            print(
                "TOOL:",
                result["tool"]["tool"]
            )

            print(
                "TOOL SUCCESS:",
                result["tool"]["success"]
            )

        print("MESSAGE:", result["message"])











