from orchestrator.hybrid_engine import FinAIHybridEngine
from rag.hybrid_retriever import RetrievedDocument


class FakeRetriever:

    def retrieve(self, query, top_k=5):
        return [
            RetrievedDocument(
                document_id=210522,
                title="RBI Payment System Data Requirements",
                source="test_source",
                date="2025-01-01",
                text=(
                    "Payment system operators must store "
                    "payment transaction data."
                ),
                lexical_score=2.1,
                semantic_score=0.91,
                fused_score=0.032,
            )
        ]


class FakeResponseService:

    def __init__(self):
        self.calls = []

    def generate(
        self,
        user_text,
        intent,
        verified_result,
        source,
        language="English",
        persona="neutral",
        max_new_tokens=256,
        model_id=None,
    ):
        self.calls.append({
            "user_text": user_text,
            "intent": intent,
            "verified_result": verified_result,
            "source": source,
            "language": language,
            "persona": persona,
            "max_new_tokens": max_new_tokens,
            "model_id": model_id,
        })

        return {
            "status": "GENERATED_VERIFIED",
            "model_id": "fake-model",
            "source": source,
            "language": language,
            "persona": persona,
            "response": (
                "According to the retrieved evidence, "
                "payment transaction data must be stored."
            ),
            "selection": {
                "capability": "response_generation",
                "model_id": "fake-model",
            },
            "verification": {
                "applicable": False,
                "passed": True,
            },
            "claim_verification": {
                "applicable": False,
                "passed": True,
            },
        }


def test_rag_response_generation():

    service = FakeResponseService()

    engine = FinAIHybridEngine(
        response_service=service,
        rag_retriever=FakeRetriever(),
    )

    result = engine.process(
        user_text="What documents are required for KYC?",
        generate_response=True,
        language="English",
        persona="neutral",
    )

    assert result["router"]["intent"] == "KYC_DOCUMENTS"
    assert result["stage"] == "rag"
    assert result["status"] == "RETRIEVED"

    assert result["rag"]["evidence_count"] == 1

    assert result["response_generation"]["status"] == (
        "GENERATED_VERIFIED"
    )

    assert result["response"] == (
        "According to the retrieved evidence, "
        "payment transaction data must be stored."
    )

    assert len(service.calls) == 1

    call = service.calls[0]

    assert call["intent"] == "KYC_DOCUMENTS"
    assert call["source"] == "retrieval_evidence"

    evidence = call["verified_result"]

    assert evidence["evidence_count"] == 1
    assert evidence["documents"][0]["document_id"] == 210522


def test_rag_does_not_generate_by_default():

    service = FakeResponseService()

    engine = FinAIHybridEngine(
        response_service=service,
        rag_retriever=FakeRetriever(),
    )

    result = engine.process(
        user_text="What documents are required for KYC?",
    )

    assert result["stage"] == "rag"
    assert result["status"] == "RETRIEVED"
    assert result["response_generation"] is None
    assert len(service.calls) == 0
