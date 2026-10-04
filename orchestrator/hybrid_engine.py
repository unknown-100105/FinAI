from datetime import datetime, timedelta
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
            from rag.hybrid_retriever import HybridRetriever
            from llm.qwen_embedding_adapter import QwenEmbeddingAdapter

            embedding_adapter = QwenEmbeddingAdapter(
                device="cuda",
                max_seq_length=640,
            )

            self.rag_retriever = HybridRetriever(
                db_path=ROOT / "data" / "rag" / "finai_rag.db",
                faiss_index_path=(
                    ROOT
                    / "data"
                    / "rag"
                    / "embeddings"
                    / "finai_rag.faiss"
                ),
                document_ids_path=(
                    ROOT
                    / "data"
                    / "rag"
                    / "embeddings"
                    / "document_ids.npy"
                ),
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

                        response_generation = (self.response_service or ResponseService()).generate(
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

                response_result = service.generate(
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

                    response_result = service.generate(
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











