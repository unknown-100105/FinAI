from orchestrator.risk_controller import (
    RiskCapabilityController,
)


def test_emi_routes_to_finance_engine():

    controller = RiskCapabilityController()

    plan = controller.build_plan(
        intent="EMI_QUERY",
        router_decision="ROUTE",
    )

    assert plan.decision == "EXECUTE"
    assert plan.risk_level == "low"
    assert plan.capability == "finance_engine"
    assert plan.execution_class == "COMPUTE"
    assert (
        plan.authority_source
        == "deterministic_finance_engine"
    )
    assert plan.authentication_required is False
    assert plan.confirmation_required is False
    assert plan.tool is None


def test_account_balance_routes_to_tool():

    controller = RiskCapabilityController()

    plan = controller.build_plan(
        intent="ACCOUNT_BALANCE",
        router_decision="ROUTE",
    )

    assert plan.decision == "EXECUTE"
    assert plan.risk_level == "medium"
    assert plan.capability == "tool_engine"
    assert plan.execution_class == "TOOL_LOOKUP"
    assert plan.tool == "get_account_balance"
    assert plan.authentication_required is True
    assert plan.confirmation_required is False


def test_card_lost_requires_high_risk_action_path():

    controller = RiskCapabilityController()

    plan = controller.build_plan(
        intent="CARD_LOST",
        router_decision="ROUTE",
    )

    assert plan.decision == "EXECUTE"
    assert plan.risk_level == "high"
    assert plan.capability == "tool_engine"
    assert plan.execution_class == "ACT"
    assert plan.tool == "block_card"
    assert plan.authentication_required is True
    assert plan.confirmation_required is True

    assert (
        plan.verification_mode
        == "POLICY_AUTH_CONFIRM_TOOL_SUCCESS"
    )


def test_support_request_is_an_action():

    controller = RiskCapabilityController()

    plan = controller.build_plan(
        intent="SUPPORT_REQUEST",
        router_decision="ROUTE",
    )

    assert plan.decision == "EXECUTE"
    assert plan.execution_class == "ACT"
    assert plan.capability == "tool_engine"
    assert plan.tool == "create_support_ticket"


def test_kyc_documents_use_retrieval():

    controller = RiskCapabilityController()

    plan = controller.build_plan(
        intent="KYC_DOCUMENTS",
        router_decision="ROUTE",
    )

    assert plan.decision == "EXECUTE"
    assert plan.capability == "rag"
    assert plan.execution_class == "RETRIEVE"
    assert (
        plan.authority_class
        == "RETRIEVED_KNOWLEDGE"
    )


def test_non_route_request_does_not_execute():

    controller = RiskCapabilityController()

    plan = controller.build_plan(
        intent="CARD_LOST",
        router_decision="CLARIFY",
    )

    assert plan.decision == "CLARIFY"
    assert plan.execution_class == "NONE"
    assert plan.capability == "none"
    assert plan.tool is None


def test_unknown_intent_is_rejected():

    controller = RiskCapabilityController()

    plan = controller.build_plan(
        intent="UNKNOWN",
        router_decision="ROUTE",
    )

    assert plan.decision == "REJECT"
    assert plan.execution_class == "NONE"
    assert plan.capability == "none"
    assert plan.risk_level == "unknown"


def test_missing_intent_is_rejected():

    controller = RiskCapabilityController()

    plan = controller.build_plan(
        intent=None,
        router_decision="ROUTE",
    )

    assert plan.decision == "REJECT"
    assert plan.capability == "none"


def test_llm_role_is_never_authorization():

    controller = RiskCapabilityController()

    for intent in (
        "EMI_QUERY",
        "ACCOUNT_BALANCE",
        "CARD_LOST",
        "FRAUD_REPORT",
    ):

        plan = controller.build_plan(
            intent=intent,
            router_decision="ROUTE",
        )

        assert plan.llm_role != "AUTHORIZE"
        assert plan.llm_role != "EXECUTE"

def test_controller_normalizes_numpy_like_intent_values():

    import numpy as np

    controller = RiskCapabilityController()

    plan = controller.build_plan(
        intent=np.str_("EMI_QUERY"),
        router_decision=np.str_("ROUTE"),
    )

    assert type(plan.intent) is str
    assert plan.intent == "EMI_QUERY"
    assert type(plan.decision) is str
    assert plan.decision == "EXECUTE"
