from llm.task_aware_router import classify_task


def test_reasoning_task_uses_specialist_capability():
    task, capability, reason = classify_task(
        intent="PORTFOLIO_RISK",
        user_text="",
        base_capability="response_generation",
    )
    assert task == "complex_financial_reasoning"
    assert capability == "financial_reasoning"
    assert reason == "matched_reasoning_intent_or_query"


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
