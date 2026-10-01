from router.router_gate import FinAIRouterGate
from policy.rules import get_policy
from policy.authority import build_authority_contract


def test_investment_question_routes_to_financial_guidance():
    router = FinAIRouterGate()

    result = router.route(
        "Where can I invest my savings?"
    )

    assert result["intent"] == "FINANCIAL_GUIDANCE"
    assert result["decision"] == "ROUTE"
    assert result["risk_level"] == "low"
    assert result["requires_clarification"] is False
    assert result["reason"] == "financial_guidance_rule"


def test_mutual_fund_question_routes_to_financial_guidance():
    router = FinAIRouterGate()

    result = router.route(
        "What is a mutual fund?"
    )

    assert result["intent"] == "FINANCIAL_GUIDANCE"


def test_sip_question_routes_to_financial_guidance():
    router = FinAIRouterGate()

    result = router.route(
        "How does SIP work?"
    )

    assert result["intent"] == "FINANCIAL_GUIDANCE"


def test_financial_guidance_policy():
    policy = get_policy("FINANCIAL_GUIDANCE")

    assert policy is not None
    assert policy.risk_level == "low"
    assert policy.authentication_required is False
    assert policy.confirmation_required is False
    assert policy.tool is None
    assert policy.category == "financial_information"


def test_financial_guidance_authority():
    contract = build_authority_contract(
        "FINANCIAL_GUIDANCE"
    )

    assert contract is not None
    assert contract.authority_class == "RETRIEVED_KNOWLEDGE"
    assert contract.authority_source == "retrieval_evidence"
    assert contract.execution_class == "RETRIEVE"
    assert contract.llm_role == "EVIDENCE_GROUNDED_EXPLANATION"


def test_security_or_action_query_is_not_financial_guidance():
    router = FinAIRouterGate()

    queries = [
        "My SIP payment failed",
        "My investment transaction is pending",
        "Someone used my investment account fraudulently",
    ]

    for query in queries:
        result = router.route(query)
        assert result["intent"] != "FINANCIAL_GUIDANCE"


def test_existing_card_lost_flow_is_preserved():
    router = FinAIRouterGate()

    result = router.route("My card is lost")

    assert result["intent"] == "CARD_LOST"
    assert result["decision"] == "ROUTE"
    assert result["risk_level"] == "high"
