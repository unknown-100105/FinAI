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
