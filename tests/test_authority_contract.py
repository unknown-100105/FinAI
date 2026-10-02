from policy.authority import (
    build_authority_contract,
    can_llm_authorize,
    can_llm_explain,
    get_authority_contract,
    is_authoritative_component,
    is_high_risk_operation,
)
from policy.rules import POLICIES


def test_every_policy_intent_has_an_authority_contract():

    for intent in POLICIES:

        contract = get_authority_contract(intent)

        assert contract is not None
        assert contract.intent == intent


def test_emi_uses_deterministic_finance_engine():

    contract = get_authority_contract("EMI_QUERY")

    assert contract.authority_class == (
        "DETERMINISTIC_COMPUTATION"
    )

    assert (
        contract.authority_source
        == "deterministic_finance_engine"
    )

    assert (
        "finance_engine"
        in contract.allowed_components
    )

    assert contract.llm_role == "EXPLAIN_ONLY"
    assert contract.execution_class == "COMPUTE"


def test_account_balance_uses_account_tool():

    contract = get_authority_contract(
        "ACCOUNT_BALANCE"
    )

    assert contract.authority_class == "VERIFIED_TOOL"

    assert (
        contract.authority_source
        == "tool:get_account_balance"
    )

    assert "tool_engine" in contract.allowed_components
    assert contract.execution_class == "TOOL_LOOKUP"


def test_high_risk_card_operation_requires_authorized_tool():

    contract = get_authority_contract("CARD_LOST")

    assert contract.authority_class == "AUTHORIZED_TOOL"

    assert (
        contract.authority_source
        == "tool:block_card"
    )

    assert (
        contract.verification_mode
        == "POLICY_AUTH_CONFIRM_TOOL_SUCCESS"
    )

    assert contract.execution_class == "ACT"

    assert is_high_risk_operation("CARD_LOST")


def test_high_risk_fraud_operation_requires_authorized_tool():

    contract = get_authority_contract(
        "FRAUD_REPORT"
    )

    assert contract.authority_class == "AUTHORIZED_TOOL"

    assert (
        contract.authority_source
        == "tool:report_fraud"
    )

    assert is_high_risk_operation(
        "FRAUD_REPORT"
    )


def test_llm_can_explain_but_never_authorize():

    assert can_llm_explain(
        "ACCOUNT_BALANCE"
    )

    assert can_llm_explain(
        "CARD_LOST"
    )

    assert can_llm_explain(
        "EMI_QUERY"
    )

    assert (
        can_llm_authorize("ACCOUNT_BALANCE")
        is False
    )

    assert (
        can_llm_authorize("CARD_LOST")
        is False
    )

    assert (
        can_llm_authorize("FRAUD_REPORT")
        is False
    )


def test_authoritative_components_are_explicit():

    assert is_authoritative_component(
        "EMI_QUERY",
        "finance_engine",
    )

    assert not is_authoritative_component(
        "EMI_QUERY",
        "llm",
    )

    assert is_authoritative_component(
        "CARD_LOST",
        "tool_engine",
    )

    assert is_authoritative_component(
        "CARD_LOST",
        "policy_engine",
    )

    assert not is_authoritative_component(
        "CARD_LOST",
        "llm",
    )


def test_unknown_intent_has_no_contract():

    assert (
        build_authority_contract(
            "UNKNOWN"
        )
        is None
    )


def test_policy_and_authority_fields_remain_aligned():

    for intent, policy in POLICIES.items():

        contract = get_authority_contract(intent)

        assert contract.risk_level == policy.risk_level
        assert contract.category == policy.category


def test_no_contract_allows_llm_to_be_source_of_truth():

    for intent in POLICIES:

        contract = get_authority_contract(intent)

        assert (
            contract.authority_source != "llm"
        )


def test_llm_is_never_authorization_authority():

    for intent in POLICIES:

        assert (
            can_llm_authorize(intent)
            is False
        )

def test_support_request_is_an_action():

    contract = get_authority_contract(
        "SUPPORT_REQUEST"
    )

    assert contract.execution_class == "ACT"


def test_profile_update_is_an_action():

    contract = get_authority_contract(
        "PROFILE_UPDATE"
    )

    assert contract.execution_class == "ACT"


def test_loan_eligibility_is_retrieval_authoritative():
    contract = get_authority_contract("LOAN_ELIGIBILITY")

    assert contract is not None
    assert contract.authority_class == "RETRIEVED_KNOWLEDGE"
    assert contract.authority_source == "retrieval_evidence"
    assert contract.execution_class == "RETRIEVE"
    assert contract.llm_role == "EVIDENCE_GROUNDED_EXPLANATION"
