from policy.authority import get_authority_contract
from orchestrator.risk_controller import RiskCapabilityController


def test_financial_product_intent_has_rag_authority():
    contract = get_authority_contract("FINANCIAL_PRODUCT_KNOWLEDGE")

    assert contract is not None
    assert contract.authority_class == "RETRIEVED_KNOWLEDGE"
    assert contract.authority_source == "retrieval_evidence"


def test_financial_product_intent_has_rag_execution():
    plan = RiskCapabilityController().build_plan(
        intent="FINANCIAL_PRODUCT_KNOWLEDGE",
        router_decision="ROUTE",
    )

    assert plan.decision == "EXECUTE"
    assert plan.capability == "rag"
