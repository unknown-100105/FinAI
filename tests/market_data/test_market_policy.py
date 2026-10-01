from orchestrator.risk_controller import RiskCapabilityController
from policy.authority import get_authority_contract
from policy.rules import get_policy


def test_market_data_policy():
    policy = get_policy("MARKET_DATA_QUERY")

    assert policy is not None
    assert policy.risk_level == "low"
    assert policy.authentication_required is False
    assert policy.confirmation_required is False
    assert policy.tool is None
    assert policy.category == "market_data"


def test_market_data_authority():
    contract = get_authority_contract("MARKET_DATA_QUERY")

    assert contract is not None
    assert contract.authority_class == "MARKET_DATA"
    assert contract.authority_source == "market_data_provider"
    assert "market_data" in contract.allowed_components
    assert contract.llm_role == "EXPLAIN_TOOL_RESULT"
    assert contract.execution_class == "LOOKUP"


def test_market_data_capability():
    controller = RiskCapabilityController()

    plan = controller.build_plan(
        intent="MARKET_DATA_QUERY",
        router_decision="ROUTE",
    )

    assert plan.decision == "EXECUTE"
    assert plan.capability == "market_data"
    assert plan.authority_class == "MARKET_DATA"
    assert plan.authentication_required is False
    assert plan.confirmation_required is False
