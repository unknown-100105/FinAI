from dataclasses import dataclass
from typing import Optional, Tuple

from .rules import get_policy, is_known_intent


@dataclass(frozen=True)
class AuthorityContract:
    intent: str
    risk_level: str
    category: str

    # What is authoritative for the final result?
    authority_class: str
    authority_source: str

    # What system components may participate?
    allowed_components: Tuple[str, ...]

    # What role is the LLM allowed to play?
    llm_role: str

    # What must be verified before the answer is accepted?
    verification_mode: str

    # Whether the request is a state-changing operation.
    execution_class: str


_FINANCE_ENGINE_INTENTS = {
    "EMI_QUERY",
    "INTEREST_QUERY",
}

_KNOWLEDGE_INTENTS = {
    "KYC_DOCUMENTS",
    "FINANCIAL_GUIDANCE",
    "FINANCIAL_PRODUCT_KNOWLEDGE",
}

_RULE_ENGINE_INTENTS = {
    "LOAN_ELIGIBILITY",
}


def _build_non_tool_contract(intent: str) -> AuthorityContract:

    policy = get_policy(intent)

    if policy is None:
        raise ValueError(
            f"Cannot build authority contract for unknown intent: "
            f"{intent}"
        )

    if intent in _FINANCE_ENGINE_INTENTS:

        return AuthorityContract(
            intent=intent,
            risk_level=policy.risk_level,
            category=policy.category,
            authority_class="DETERMINISTIC_COMPUTATION",
            authority_source="deterministic_finance_engine",
            allowed_components=(
                "finance_engine",
                "response_verifier",
            ),
            llm_role="EXPLAIN_ONLY",
            verification_mode="NUMERIC_AND_SEMANTIC_CONSISTENCY",
            execution_class="COMPUTE",
        )

    if intent == "MARKET_DATA_QUERY":

        return AuthorityContract(
            intent=intent,
            risk_level=policy.risk_level,
            category=policy.category,
            authority_class="MARKET_DATA",
            authority_source="market_data_provider",
            allowed_components=(
                "market_data",
                "response_verifier",
            ),
            llm_role="EXPLAIN_TOOL_RESULT",
            verification_mode="MARKET_DATA_RESULT_CONSISTENCY",
            execution_class="LOOKUP",
        )
    if intent in _KNOWLEDGE_INTENTS:

        return AuthorityContract(
            intent=intent,
            risk_level=policy.risk_level,
            category=policy.category,
            authority_class="RETRIEVED_KNOWLEDGE",
            authority_source="retrieval_evidence",
            allowed_components=(
                "rag",
                "evidence_verifier",
            ),
            llm_role="EVIDENCE_GROUNDED_EXPLANATION",
            verification_mode="EVIDENCE_SUPPORT",
            execution_class="RETRIEVE",
        )

    # Conservative fallback:
    # no tool + no dedicated authority mapping
    # must use retrieval rather than LLM memory.
    return AuthorityContract(
        intent=intent,
        risk_level=policy.risk_level,
        category=policy.category,
        authority_class="RETRIEVED_KNOWLEDGE",
        authority_source="retrieval_evidence",
        allowed_components=(
            "rag",
            "evidence_verifier",
        ),
        llm_role="EVIDENCE_GROUNDED_EXPLANATION",
        verification_mode="EVIDENCE_SUPPORT",
        execution_class="RETRIEVE",
    )


def build_authority_contract(
    intent: str,
) -> Optional[AuthorityContract]:

    if not is_known_intent(intent):
        return None

    policy = get_policy(intent)

    if policy is None:
        return None

    if policy.tool is None:
        return _build_non_tool_contract(intent)

    if policy.risk_level == "high":

        authority_class = "AUTHORIZED_TOOL"
        llm_role = "EXPLAIN_EXECUTION_RESULT"
        verification_mode = (
            "POLICY_AUTH_CONFIRM_TOOL_SUCCESS"
        )

    elif policy.risk_level == "medium":

        authority_class = "VERIFIED_TOOL"
        llm_role = "EXPLAIN_TOOL_RESULT"
        verification_mode = "TOOL_RESULT_CONSISTENCY"

    else:

        authority_class = "INFORMATION_TOOL"
        llm_role = "EXPLAIN_TOOL_RESULT"
        verification_mode = "TOOL_RESULT_CONSISTENCY"

    # State-changing tools are actions even when their risk level
    # is low or medium. Risk and execution semantics are separate.
    _ACTION_TOOLS = {
        "secure_account",
        "reset_password",
        "update_profile",
        "activate_card",
        "block_card",
        "unblock_card",
        "cancel_payment",
        "report_duplicate_transaction",
        "report_wrong_amount",
        "investigate_unknown_transaction",
        "create_transaction_dispute",
        "report_fraud",
        "investigate_suspicious_activity",
        "update_kyc",
        "create_support_ticket",
    }

    execution_class = (
        "ACT"
        if policy.tool in _ACTION_TOOLS
        else "TOOL_LOOKUP"
    )

    return AuthorityContract(
        intent=intent,
        risk_level=policy.risk_level,
        category=policy.category,
        authority_class=authority_class,
        authority_source=f"tool:{policy.tool}",
        allowed_components=(
            "policy_engine",
            "tool_engine",
            "response_verifier",
        ),
        llm_role=llm_role,
        verification_mode=verification_mode,
        execution_class=execution_class,
    )


def get_authority_contract(
    intent: str,
) -> Optional[AuthorityContract]:
    return build_authority_contract(intent)


def is_authoritative_component(
    intent: str,
    component: str,
) -> bool:

    contract = build_authority_contract(intent)

    if contract is None:
        return False

    return component in contract.allowed_components


def can_llm_explain(
    intent: str,
) -> bool:
    """
    Returns True when the LLM has an allowed explanatory role.

    This does NOT grant authorization authority.
    """

    contract = build_authority_contract(intent)

    if contract is None:
        return False

    return contract.llm_role in {
        "EXPLAIN_ONLY",
        "EVIDENCE_GROUNDED_EXPLANATION",
        "EXPLAIN_TOOL_RESULT",
        "EXPLAIN_EXECUTION_RESULT",
    }


def can_llm_authorize(
    intent: str,
) -> bool:
    """
    Hard security invariant:
    the LLM is never an authorization authority.
    """

    return False


def is_high_risk_operation(
    intent: str,
) -> bool:

    contract = build_authority_contract(intent)

    return (
        contract is not None
        and contract.risk_level == "high"
    )


if __name__ == "__main__":

    print("=" * 80)
    print("FINAI TASK -> AUTHORITY CONTRACT TEST")
    print("=" * 80)

    test_intents = [
        "EMI_QUERY",
        "INTEREST_QUERY",
        "ACCOUNT_BALANCE",
        "CARD_LOST",
        "FRAUD_REPORT",
        "KYC_DOCUMENTS",
        "LOAN_ELIGIBILITY",
        "SUPPORT_REQUEST",
    ]

    for intent in test_intents:

        contract = get_authority_contract(intent)

        print()
        print("INTENT:", intent)
        print("CONTRACT:", contract)
        print("LLM CAN EXPLAIN:", can_llm_explain(intent))
        print("LLM CAN AUTHORIZE:", can_llm_authorize(intent))

    print()
    print("UNKNOWN:", get_authority_contract("UNKNOWN"))


