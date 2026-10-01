from orchestrator.hybrid_engine import FinAIHybridEngine


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
            "response": "Verified EMI response.",
        }


def test_hybrid_engine_can_generate_verified_finance_response():

    service = FakeResponseService()
    engine = FinAIHybridEngine(
        response_service=service
    )

    result = engine.process(
        user_text=(
            "Calculate EMI for ₹10 lakh at "
            "8.5% for 20 years"
        ),
        generate_response=True,
        language="English",
        persona="neutral",
    )

    assert result["stage"] == "finance_engine"
    assert result["status"] == "CALCULATED"

    assert result["response"] == (
        "Verified EMI response."
    )

    assert result["response_generation"]["status"] == (
        "GENERATED_VERIFIED"
    )

    assert len(service.calls) == 1

    call = service.calls[0]

    assert call["intent"] == "EMI_QUERY"
    assert call["source"] == (
        "deterministic_finance_engine"
    )

    assert call["verified_result"]["monthly_emi"] == 8678.23
    assert call["verified_result"]["total_payment"] == 2082775.76
    assert call["verified_result"]["total_interest"] == 1082775.76


def test_hybrid_engine_does_not_generate_by_default():

    service = FakeResponseService()
    engine = FinAIHybridEngine(
        response_service=service
    )

    result = engine.process(
        user_text=(
            "Calculate EMI for ₹10 lakh at "
            "8.5% for 20 years"
        )
    )

    assert len(service.calls) == 0
    assert result["response_generation"] is None


def test_incomplete_finance_request_does_not_generate():

    service = FakeResponseService()
    engine = FinAIHybridEngine(
        response_service=service
    )

    result = engine.process(
        user_text="Calculate my EMI",
        generate_response=True,
    )

    assert result["status"] == "MISSING_PARAMETERS"
    assert len(service.calls) == 0
