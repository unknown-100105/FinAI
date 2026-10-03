from types import SimpleNamespace

from orchestrator.hybrid_engine import FinAIHybridEngine


class FakeBaseEngine:
    def process(self, **kwargs):
        return {
            "router": {
                "intent": "KYC_DOCUMENTS",
                "decision": "ROUTE",
                "risk_level": "low",
            },
        }


class FakeDomainRouter:
    def route(self, user_text, classified_intent=None):
        return {
            "domain": "FINANCIAL_KNOWLEDGE",
            "reason": "test domain route",
            "source": "test",
        }


class FakeController:
    def build_plan(self, intent, router_decision):
        return SimpleNamespace(
            intent=intent,
            decision="EXECUTE",
            risk_level="low",
            category="financial_knowledge",
            capability="rag",
            execution_class="RETRIEVE",
            authority_class="RETRIEVED_KNOWLEDGE",
            authority_source="retrieval_evidence",
            allowed_components=("rag", "llm"),
            authentication_required=False,
            confirmation_required=False,
            tool=None,
            llm_role="EVIDENCE_GROUNDED_EXPLANATION",
            verification_mode="EVIDENCE_SUPPORT",
        )


class FakeRetriever:
    def retrieve(self, user_text, top_k=5):
        return [
            SimpleNamespace(
                document_id=1,
                title="KYC requirements",
                source="test",
                date="2025-01-01",
                text="PAN and address proof may be required.",
                lexical_score=1.0,
                semantic_score=1.0,
                fused_score=1.0,
            )
        ]


class FakeResponseService:
    def generate(self, **kwargs):
        return {
            "status": "VERIFICATION_FAILED",
            "response": (
                "I couldn't verify the generated explanation "
                "against the retrieved evidence."
            ),
            "verification": {
                "applicable": True,
                "passed": False,
                "mode": "EVIDENCE_SUPPORT",
            },
        }


def _engine():
    engine = FinAIHybridEngine.__new__(FinAIHybridEngine)
    engine.base_engine = FakeBaseEngine()
    engine.finance = None
    engine.controller = FakeController()
    engine.domain_router = FakeDomainRouter()
    engine.response_service = FakeResponseService()
    engine.market_data = None
    engine.rag_retriever = FakeRetriever()
    return engine


def test_rag_verification_failure_propagates_to_top_level_status():
    result = _engine().process(
        user_text="What documents are required for KYC?",
        generate_response=True,
    )

    assert result["stage"] == "rag"
    assert result["status"] == "VERIFICATION_FAILED"
    assert result["response_generation"]["status"] == "VERIFICATION_FAILED"
    assert result["response_generation"]["verification"]["passed"] is False
    assert result["message"].startswith("I couldn't verify")


def test_successful_rag_retrieval_without_generation_keeps_retrieved_status():
    engine = _engine()
    engine.response_service = None

    result = engine.process(
        user_text="What documents are required for KYC?",
        generate_response=False,
    )

    assert result["stage"] == "rag"
    assert result["status"] == "RETRIEVED"
    assert result["response_generation"] is None
