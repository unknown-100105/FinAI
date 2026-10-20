from llm.task_aware_router import classify_task


def test_reasoning_task_uses_specialist_capability():
    task, capability, reason = classify_task(
        intent="PORTFOLIO_RISK",
        user_text="",
        base_capability="response_generation",
    )
    assert task == "complex_financial_reasoning"
    assert capability == "financial_reasoning"
    assert reason == "matched_reasoning_intent"


def test_reasoning_text_can_upgrade_generic_intent():
    task, capability, _ = classify_task(
        intent="GENERAL_QUERY",
        user_text="Please run a counterfactual stress test on my portfolio",
        base_capability="response_generation",
    )
    assert task == "complex_financial_reasoning"
    assert capability == "financial_reasoning"


def test_retrieval_evidence_uses_tool_assisted_qa():
    task, capability, _ = classify_task(
        intent="FINANCIAL_GUIDANCE",
        source="retrieval_evidence",
        base_capability="financial_qa",
    )
    assert task == "evidence_grounded_document_qa"
    assert capability == "tool_assisted_qa"


def test_explanation_request_uses_explanation_capability():
    task, capability, _ = classify_task(
        intent="GENERAL_QUERY",
        user_text="Explain compound interest in simple terms",
        base_capability="response_generation",
    )
    assert task == "financial_explanation"
    assert capability == "financial_explanation"


def test_known_financial_intent_uses_financial_qa():
    task, capability, _ = classify_task(
        intent="EMI_QUERY",
        user_text="",
        base_capability="financial_qa",
    )
    assert task == "financial_question_answering"
    assert capability == "financial_qa"


def test_default_task_uses_base_capability():
    task, capability, _ = classify_task(
        intent="GENERAL_QUERY",
        user_text="Hello",
        base_capability="response_generation",
    )
    assert task == "general_response"
    assert capability == "response_generation"

from types import SimpleNamespace

from llm.task_aware_router import TaskAwareModelRouter


def test_task_router_delegates_constraints_to_existing_model_router():
    router = TaskAwareModelRouter()
    seen = {}

    def fake_route(**kwargs):
        seen.update(kwargs)
        return SimpleNamespace(
            selected_model="gemini-cloud",
            to_dict=lambda: {"selected_model": "gemini-cloud"},
        )

    router.model_router.route = fake_route
    result = router.route(
        intent="GENERAL_QUERY",
        user_text="Explain this statement",
        source="retrieval_evidence",
        base_capability="response_generation",
        network_mode="offline",
        data_sensitivity="restricted",
        allowed_providers=["local"],
        language="Tamil",
    )
    assert result.task_type == "evidence_grounded_document_qa"
    assert result.capability == "tool_assisted_qa"
    assert seen["network_mode"] == "offline"
    assert seen["data_sensitivity"] == "restricted"
    assert seen["allowed_providers"] == ["local"]
    assert seen["language"] == "Tamil"


def test_task_router_reports_capability_downgrade_when_specialist_unavailable():
    router = TaskAwareModelRouter()
    calls = []

    def fake_route(**kwargs):
        calls.append(kwargs["capability"])
        if kwargs["capability"] == "financial_reasoning":
            raise RuntimeError("No enabled specialist")
        return SimpleNamespace(
            selected_model="gemini-cloud",
            to_dict=lambda: {"selected_model": "gemini-cloud"},
        )

    router.model_router.route = fake_route
    result = router.route(
        intent="PORTFOLIO_RISK",
        user_text="",
        base_capability="response_generation",
    )
    assert calls[:2] == ["financial_reasoning", "financial_qa"]
    assert result.capability == "financial_qa"
    assert "preferred capability unavailable" in result.selection_reason


def test_explicit_model_does_not_silently_downgrade_capability():
    router = TaskAwareModelRouter()

    def fake_route(**kwargs):
        raise RuntimeError("Explicit model lacks requested capability")

    router.model_router.route = fake_route
    try:
        router.route(
            intent="PORTFOLIO_RISK",
            explicit_model="gemini-cloud",
            base_capability="response_generation",
        )
    except RuntimeError as exc:
        assert "lacks requested capability" in str(exc)
        return
    raise AssertionError("Explicit model request was silently downgraded.")


def test_document_evidence_takes_precedence_over_generic_analysis_wording():
    task, capability, _ = classify_task(
        intent="GENERAL_QUERY",
        user_text="Analyze this document",
        source="retrieval_evidence",
        base_capability="response_generation",
    )
    assert task == "evidence_grounded_document_qa"
    assert capability == "tool_assisted_qa"


def test_high_risk_reasoning_fails_closed_when_no_specialist_is_eligible():
    router = TaskAwareModelRouter()
    calls = []

    def fake_route(**kwargs):
        calls.append(kwargs["capability"])
        raise RuntimeError("No eligible specialist")

    router.model_router.route = fake_route
    try:
        router.route(
            intent="PORTFOLIO_RISK",
            risk_level="critical",
            base_capability="response_generation",
        )
    except RuntimeError as exc:
        assert "No eligible model" in str(exc)
    else:
        raise AssertionError("High-risk reasoning silently downgraded.")
    assert calls == ["financial_reasoning"]
