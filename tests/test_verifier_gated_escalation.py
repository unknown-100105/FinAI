from llm.verifier_gated_escalation import verifier_gated_escalate


def test_escalation_stops_at_first_verified_candidate():
    calls = []

    def generate(model_id):
        calls.append(model_id)
        return {"response": "answer", "model_id": model_id}

    def verify(response):
        if len(calls) == 1:
            return (
                {"applicable": True, "passed": False},
                {"applicable": False, "passed": True},
            )
        return (
            {"applicable": True, "passed": True},
            {"applicable": True, "passed": True},
        )

    result = verifier_gated_escalate(
        candidates=["weak-model", "strong-model", "third-model"],
        generate=generate,
        verify=verify,
        max_attempts=2,
    )

    assert calls == ["weak-model", "strong-model"]
    assert result["status"] == "GENERATED_VERIFIED_ESCALATED"
    assert result["model_id"] == "strong-model"
    assert result["verification_escalation"]["accepted"] is True
    assert result["verification_escalation"]["attempt_count"] == 2


def test_escalation_is_bounded_and_does_not_accept_failed_answers():
    calls = []

    def generate(model_id):
        calls.append(model_id)
        return {"response": "unsupported answer"}

    def verify(_response):
        return (
            {"applicable": True, "passed": False},
            {"applicable": True, "passed": False},
        )

    result = verifier_gated_escalate(
        candidates=["model-a", "model-b", "model-c"],
        generate=generate,
        verify=verify,
        max_attempts=1,
    )

    assert calls == ["model-a"]
    assert "status" not in result
    assert result["verification_escalation"]["accepted"] is False
    assert result["verification_escalation"]["attempt_count"] == 1


def test_escalation_records_provider_errors_without_leaking_exception_text():
    def generate(_model_id):
        raise RuntimeError("provider key or endpoint detail")

    result = verifier_gated_escalate(
        candidates=["model-a"],
        generate=generate,
        verify=lambda _response: ({}, {}),
        max_attempts=1,
    )

    assert result["verification_escalation"]["trace"] == [{
        "model_id": "model-a",
        "status": "generation_failed",
        "error_type": "RuntimeError",
    }]


def test_response_service_escalates_to_configured_model_after_claim_verification_fails():
    from types import SimpleNamespace

    from llm.model_gateway import ModelGateway
    from llm.response_service import ResponseService

    class FakeAdapter:
        def __init__(self, response):
            self.response = response
            self.calls = []

        def generate(self, **kwargs):
            self.calls.append(kwargs)
            return {"response": self.response, "metrics": {}}

    good = (
        "Monthly EMI: ₹8,678.23. "
        "Total payment: ₹2,082,775.76. "
        "Total interest: ₹1,082,775.76."
    )
    gateway = ModelGateway(default_model="gemini-cloud")
    primary = FakeAdapter("Monthly EMI: ₹9,000.00. Total interest: ₹1,082,775.76.")
    gateway.register(
        "gemini-cloud",
        primary,
        capabilities=["response_generation", "financial_qa"],
    )
    service = ResponseService(gateway=gateway)
    specialist = FakeAdapter(good)
    service._fallback_adapters["openrouter-cloud"] = specialist

    route = SimpleNamespace(
        selected_model="gemini-cloud",
        fallback_chain=["gemini-cloud", "openrouter-cloud"],
        allowed_providers=(),
        network_mode="online",
        data_sensitivity="standard",
    )
    verified = {
        "principal": 1_000_000,
        "annual_rate": 8.5,
        "tenure_months": 240,
        "monthly_emi": 8678.23,
        "total_payment": 2082775.76,
        "total_interest": 1082775.76,
    }
    first_verification = service._verify_response(
        "Monthly EMI: ₹9,000.00. Total interest: ₹1,082,775.76.",
        "EMI_QUERY",
        verified,
        "deterministic_finance_engine",
    )
    first_claims = service._verify_claims(
        "Monthly EMI: ₹9,000.00. Total interest: ₹1,082,775.76.",
        "EMI_QUERY",
        verified,
        "deterministic_finance_engine",
    )
    result = service._try_verifier_escalation(
        selected_model="gemini-cloud",
        explicit_model=False,
        route=route,
        capability="financial_qa",
        user_text="Calculate EMI",
        intent="EMI_QUERY",
        verified_result=verified,
        source="deterministic_finance_engine",
        language="English",
        persona="neutral",
        max_new_tokens=160,
        initial_response="Monthly EMI: ₹9,000.00. Total interest: ₹1,082,775.76.",
        verification=first_verification,
        claim_verification=first_claims,
    )

    assert result["status"] == "GENERATED_VERIFIED_ESCALATED"
    assert result["model_id"] == "openrouter-cloud"
    assert result["verification"]["passed"] is True
    assert result["claim_verification"]["passed"] is True
    assert result["verification_escalation"]["from_model"] == "gemini-cloud"
    assert len(specialist.calls) == 1


def test_response_service_retrieves_better_evidence_before_escalating():
    from types import SimpleNamespace

    from llm.model_gateway import ModelGateway
    from llm.response_service import ResponseService

    gateway = ModelGateway(default_model="gemini-cloud")
    service = ResponseService(
        gateway=gateway,
        evidence_retriever=lambda _text, _intent, _previous: [
            {"title": "Loan rate", "text": "The loan rate is 7 percent."}
        ],
    )
    response = "The loan rate is 7 percent."
    old_result = {
        "documents": [{"title": "Unrelated", "text": "A different topic."}]
    }
    verification = service._verify_response(
        response, "GENERAL_QUERY", old_result, "retrieval_evidence"
    )
    claims = service._verify_claims(
        response, "GENERAL_QUERY", old_result, "retrieval_evidence"
    )
    route = SimpleNamespace(
        selected_model="gemini-cloud",
        fallback_chain=["gemini-cloud"],
        allowed_providers=(),
        network_mode="online",
        data_sensitivity="standard",
    )

    result = service._try_verifier_escalation(
        selected_model="gemini-cloud",
        explicit_model=False,
        route=route,
        capability="tool_assisted_qa",
        user_text="What is the loan rate?",
        intent="GENERAL_QUERY",
        verified_result=old_result,
        source="retrieval_evidence",
        language="English",
        persona="neutral",
        max_new_tokens=160,
        initial_response=response,
        verification=verification,
        claim_verification=claims,
    )

    assert result["status"] == "GENERATED_VERIFIED_AFTER_RETRIEVAL"
    assert result["verification"]["passed"] is True
    assert result["verification_escalation"]["action"] == "retrieve_more_evidence"
