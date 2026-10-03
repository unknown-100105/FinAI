from xai.trace import XAITrace


def test_xai_trace_records_rag_verification_and_generation_state():
    trace = XAITrace("test-rag-session")

    trace.record_execution_plan({
        "capability": "rag",
        "execution_class": "RETRIEVE",
        "authority_class": "RETRIEVED_KNOWLEDGE",
        "authority_source": "retrieval_evidence",
        "tool": None,
        "decision": "EXECUTE",
    })

    trace.record_rag({
        "query": "What documents are required for KYC?",
        "retrieval_method": "hybrid_rrf",
        "top_k": 5,
        "documents": [
            {
                "document_id": 1,
                "title": "KYC requirements",
                "source": "test",
                "date": "2025-01-01",
                "text": "PAN and address proof may be required.",
            }
        ],
    })

    trace.record_response_generation({
        "model_id": "rllm-finqa-4b",
        "status": "GENERATED_VERIFIED",
        "source": "retrieval_evidence",
        "language": "English",
        "persona": "neutral",
        "generation_complete": True,
        "truncated": False,
        "finish_reason": "stop",
        "retry_after_truncation": True,
        "metrics": {"generated_tokens": 120},
        "verification": {
            "applicable": True,
            "passed": True,
            "mode": "EVIDENCE_SUPPORT",
            "evidence_count": 1,
            "supported_claims": [{"claim": "PAN may be required."}],
            "unsupported_claims": [],
        },
        "claim_verification": {
            "applicable": False,
            "passed": True,
            "report": None,
            "claims": [],
        },
        "selection": {
            "capability": "financial_qa",
            "model_id": "gemini-cloud",
            "actual_model_id": "rllm-finqa-4b",
            "fallback_used": True,
        },
    })

    assert trace.data["authority"]["authority_class"] == (
        "RETRIEVED_KNOWLEDGE"
    )
    assert trace.data["execution"]["capability"] == "rag"
    assert trace.data["rag"]["evidence_count"] == 1
    assert trace.data["verification"]["applicable"] is True
    assert trace.data["verification"]["passed"] is True
    assert trace.data["verification"]["mode"] == "EVIDENCE_SUPPORT"
    assert trace.data["model"]["generation_complete"] is True
    assert trace.data["model"]["truncated"] is False
    assert trace.data["model"]["finish_reason"] == "stop"
    assert trace.data["model"]["retry_after_truncation"] is True
