from dataclasses import dataclass
from typing import Optional, Tuple

from policy.authority import get_authority_contract
from policy.rules import get_policy


@dataclass(frozen=True)
class ExecutionPlan:
    intent: str
    decision: str

    risk_level: str
    category: str

    capability: str
    execution_class: str

    authority_class: Optional[str]
    authority_source: Optional[str]

    allowed_components: Tuple[str, ...]

    authentication_required: bool
    confirmation_required: bool

    tool: Optional[str]

    llm_role: Optional[str]
    verification_mode: Optional[str]


class RiskCapabilityController:

    def build_plan(
        self,
        intent: Optional[str],
        router_decision: str = "ROUTE",
    ) -> ExecutionPlan:

        # Normalize classifier/library scalar types at the
        # orchestration boundary so downstream JSON/XAI layers
        # always receive native Python types.
        normalized_intent = (
            str(intent)
            if intent is not None
            else None
        )

        router_decision = str(router_decision)

        # ---------------------------------------------------------
        # Router did not approve routing.
        # ---------------------------------------------------------

        if router_decision != "ROUTE":

            return ExecutionPlan(
                intent=normalized_intent or "UNKNOWN",
                decision=router_decision,
                risk_level="unknown",
                category="unknown",
                capability="none",
                execution_class="NONE",
                authority_class=None,
                authority_source=None,
                allowed_components=(),
                authentication_required=False,
                confirmation_required=False,
                tool=None,
                llm_role=None,
                verification_mode=None,
            )

        # ---------------------------------------------------------
        # No recognized intent.
        # ---------------------------------------------------------

        contract = (
            get_authority_contract(normalized_intent)
            if intent
            else None
        )

        policy = (
            get_policy(normalized_intent)
            if intent
            else None
        )

        if contract is None or policy is None:

            return ExecutionPlan(
                intent=normalized_intent or "UNKNOWN",
                decision="REJECT",
                risk_level="unknown",
                category="unknown",
                capability="none",
                execution_class="NONE",
                authority_class=None,
                authority_source=None,
                allowed_components=(),
                authentication_required=False,
                confirmation_required=False,
                tool=None,
                llm_role=None,
                verification_mode=None,
            )

        # ---------------------------------------------------------
        # Convert authority semantics into an executable capability.
        # ---------------------------------------------------------

        capability_map = {
            "DETERMINISTIC_COMPUTATION": "finance_engine",
            "RULE_ENGINE": "financial_rules_engine",
            "RETRIEVED_KNOWLEDGE": "rag",
            "MARKET_DATA": "market_data",
            "AUTHORIZED_TOOL": "tool_engine",
            "VERIFIED_TOOL": "tool_engine",
            "INFORMATION_TOOL": "tool_engine",
        }

        capability = capability_map.get(
            contract.authority_class,
            "unknown",
        )

        if capability == "unknown":

            return ExecutionPlan(
                intent=normalized_intent,
                decision="REJECT",
                risk_level=contract.risk_level,
                category=contract.category,
                capability="unknown",
                execution_class="NONE",
                authority_class=contract.authority_class,
                authority_source=contract.authority_source,
                allowed_components=contract.allowed_components,
                authentication_required=policy.authentication_required,
                confirmation_required=policy.confirmation_required,
                tool=policy.tool,
                llm_role=contract.llm_role,
                verification_mode=contract.verification_mode,
            )

        return ExecutionPlan(
            intent=normalized_intent,
            decision="EXECUTE",
            risk_level=contract.risk_level,
            category=contract.category,
            capability=capability,
            execution_class=contract.execution_class,
            authority_class=contract.authority_class,
            authority_source=contract.authority_source,
            allowed_components=contract.allowed_components,
            authentication_required=policy.authentication_required,
            confirmation_required=policy.confirmation_required,
            tool=policy.tool,
            llm_role=contract.llm_role,
            verification_mode=contract.verification_mode,
        )


if __name__ == "__main__":

    controller = RiskCapabilityController()

    print("=" * 80)
    print("FINAI RISK/CAPABILITY CONTROLLER")
    print("=" * 80)

    tests = [
        ("EMI_QUERY", "ROUTE"),
        ("INTEREST_QUERY", "ROUTE"),
        ("ACCOUNT_BALANCE", "ROUTE"),
        ("CARD_LOST", "ROUTE"),
        ("FRAUD_REPORT", "ROUTE"),
        ("SUPPORT_REQUEST", "ROUTE"),
        ("KYC_DOCUMENTS", "ROUTE"),
        ("UNKNOWN", "ROUTE"),
        ("CARD_LOST", "CLARIFY"),
    ]

    for intent, decision in tests:

        plan = controller.build_plan(
            intent=intent,
            router_decision=decision,
        )

        print()
        print("INTENT:", intent)
        print("ROUTER DECISION:", decision)
        print("PLAN:", plan)


