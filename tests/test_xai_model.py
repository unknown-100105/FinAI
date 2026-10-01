from xai.trace import XAITrace


def test_xai_trace_records_model_metadata():

    trace = XAITrace("model-trace-test")

    trace.record_model({
        "model_id": "rllm-finqa-4b",
        "status": "GENERATED_VERIFIED",
        "source": "deterministic_finance_engine",
        "language": "English",
        "persona": "neutral",
        "metrics": {
            "generation_seconds": 1.25,
            "generated_tokens": 100,
        },
        "selection": {
            "capability": "financial_qa",
            "model_id": "rllm-finqa-4b",
        },
    })

    model = trace.data["model"]

    assert model["model_id"] == "rllm-finqa-4b"
    assert model["status"] == "GENERATED_VERIFIED"
    assert model["capability"] == "financial_qa"
    assert model["source"] == "deterministic_finance_engine"
    assert model["language"] == "English"
    assert model["persona"] == "neutral"
    assert model["metrics"]["generated_tokens"] == 100


def test_xai_trace_handles_missing_model_result():

    trace = XAITrace("model-empty-test")

    trace.record_model(None)

    assert trace.data["model"]["model_id"] is None
    assert trace.data["model"]["status"] is None


def test_response_generation_trace_marks_verified_model_claims():

    trace = XAITrace("verified-model-claims-test")

    response_generation = {
        "model_id": "rllm-finqa-4b",
        "status": "GENERATED_VERIFIED",
        "source": "deterministic_finance_engine",
        "language": "English",
        "persona": "neutral",
        "selection": {
            "capability": "financial_qa",
            "model_id": "rllm-finqa-4b",
        },
        "claim_verification": {
            "applicable": True,
            "passed": True,
            "report": {
                "passed": True,
                "matched": [],
                "mismatched": [],
                "unsupported": [],
                "rejected_claims": [],
                "authority_violations": [],
                "missing_required_fields": [],
            },
            "claims": [
                {
                    "field": "monthly_emi",
                    "value": 8678.23,
                    "claim_type": "MODEL_INFERRED",
                    "authority_source": "llm",
                    "verification_status": "PENDING",
                    "evidence_ref": None,
                    "metadata": {},
                }
            ],
        },
    }

    trace.record_response_generation(
        response_generation
    )

    claims = trace.data["claims"]

    assert claims["all_verified"] is True
    assert claims["authoritative_count"] == 0
    assert claims["items"][0]["claim_type"] == (
        "MODEL_INFERRED"
    )
    assert claims["items"][0]["authority_source"] == "llm"
    assert claims["items"][0]["verification_status"] == (
        "VERIFIED"
    )
    assert claims["items"][0]["metadata"][
        "verified_against"
    ] == "response_verification"
