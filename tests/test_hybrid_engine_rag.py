from orchestrator.hybrid_engine import FinAIHybridEngine
from rag.hybrid_retriever import RetrievedDocument


class MockRetriever:
    def retrieve(self, query, top_k=5):
        return [
            RetrievedDocument(
                document_id=210522,
                title="RBI Payment System Data Requirements",
                source="test_source",
                date="2025-01-01",
                text="Payment system operators must store payment transaction data.",
                lexical_score=2.1,
                semantic_score=0.91,
                fused_score=0.032,
            )
        ]


def test_rag_capability_execution():
    engine = FinAIHybridEngine(rag_retriever=MockRetriever())

    result = engine.process(
        user_text="What documents are required for KYC?"
    )

    assert result["router"]["intent"] == "KYC_DOCUMENTS"
    assert result["execution_plan"]["capability"] == "rag"
    assert result["status"] == "RETRIEVED"
    assert result["stage"] == "rag"

    assert result["rag"]["retrieval_method"] == "hybrid_rrf"
    assert result["rag"]["evidence_count"] == 1
    assert result["rag"]["documents"][0]["document_id"] == 210522


def test_finance_path_is_unchanged():
    engine = FinAIHybridEngine()

    result = engine.process(
        user_text="Calculate EMI for 10 lakh at 8.5% for 20 years"
    )

    assert result["router"]["intent"] == "EMI_QUERY"
    assert result["execution_plan"]["capability"] == "finance_engine"
    assert result["status"] == "CALCULATED"
    assert result["stage"] == "finance_engine"
