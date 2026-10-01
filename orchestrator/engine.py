from datetime import datetime
from typing import Optional

from router.router_gate import FinAIRouterGate
from policy.engine import PolicyEngine
from orchestrator.tools import FinAIToolEngine


class FinAIOrchestrator:

    def __init__(self):
        self.router = FinAIRouterGate()
        self.policy = PolicyEngine()
        self.tools = FinAIToolEngine()

    def process(
        self,
        user_text: str,
        authenticated: bool = False,
        confirmed: bool = False,
        account_id: str = "ACC1001",
        card_id: str = "CARD1001",
        transaction_id: str = "TXN002",
        upi_id: str = "UPI1001",
        transfer_id: str = "TRF1001",
        refund_id: str = "REF1001",
    ):

        # ---------------------------------------------------------
        # 1. ROUTING
        # ---------------------------------------------------------

        route = self.router.route(user_text)

        if route["decision"] == "UNKNOWN":
            return {
                "stage": "router",
                "status": "UNKNOWN",
                "user_text": user_text,
                "router": route,
                "policy": None,
                "tool": None,
                "message": (
                    "I could not determine a supported financial intent "
                    "from that request."
                ),
                "timestamp": datetime.now().isoformat(),
            }

        if route["decision"] == "CLARIFY":
            return {
                "stage": "router",
                "status": "CLARIFICATION_REQUIRED",
                "user_text": user_text,
                "router": route,
                "policy": None,
                "tool": None,
                "message": self._clarification_message(route),
                "timestamp": datetime.now().isoformat(),
            }

        intent = route["intent"]

        # ---------------------------------------------------------
        # 2. POLICY
        # ---------------------------------------------------------

        policy_result = self.policy.evaluate(
            intent=intent,
            authenticated=authenticated,
            confirmed=confirmed,
        )

        if not policy_result["allowed"]:
            return {
                "stage": "policy",
                "status": policy_result["status"],
                "user_text": user_text,
                "router": route,
                "policy": policy_result,
                "tool": None,
                "message": policy_result["message"],
                "timestamp": datetime.now().isoformat(),
            }

        # ---------------------------------------------------------
        # 3. TOOL ARGUMENTS
        # ---------------------------------------------------------

        tool_name = policy_result["tool"]

        kwargs = self._build_tool_args(
            tool_name=tool_name,
            account_id=account_id,
            card_id=card_id,
            transaction_id=transaction_id,
            upi_id=upi_id,
            transfer_id=transfer_id,
            refund_id=refund_id,
        )

        # ---------------------------------------------------------
        # 4. TOOL EXECUTION
        # ---------------------------------------------------------

        if tool_name:
            tool_result = self.tools.execute(
                tool_name,
                **kwargs
            )
        else:
            tool_result = None

        return {
            "stage": "tool" if tool_result else "policy",
            "status": (
                "TOOL_EXECUTED"
                if tool_result
                else "ALLOWED_NO_TOOL"
            ),
            "user_text": user_text,
            "router": route,
            "policy": policy_result,
            "tool": tool_result,
            "message": (
                tool_result["message"]
                if tool_result
                else "Request can be answered without a tool."
            ),
            "timestamp": datetime.now().isoformat(),
        }

    def _build_tool_args(
        self,
        tool_name,
        account_id,
        card_id,
        transaction_id,
        upi_id,
        transfer_id,
        refund_id,
    ):

        account_tools = {
            "get_account_balance",
            "secure_account",
            "check_account_lock",
            "reset_password",
            "update_profile",
            "get_transaction_history",
            "get_payment_limit",
            "get_account_limit",
            "check_beneficiary",
            "check_kyc_status",
            "update_kyc",
            "check_loan_status",
            "report_fraud",
            "investigate_suspicious_activity",
            "create_support_ticket",
            "check_upi_id",
            "get_account_limit",
        }

        if tool_name in account_tools:

            if tool_name == "create_support_ticket":
                return {"account_id": account_id}

            return {"account_id": account_id}

        card_tools = {
            "activate_card",
            "block_card",
            "unblock_card",
            "check_pin_status",
        }

        if tool_name in card_tools:
            return {"card_id": card_id}

        transaction_tools = {
            "check_payment_status",
            "check_card_payment",
            "cancel_payment",
            "check_cash_withdrawal",
            "check_reversed_transaction",
            "report_duplicate_transaction",
            "report_wrong_amount",
            "investigate_unknown_transaction",
            "create_transaction_dispute",
        }

        if tool_name in transaction_tools:
            return {"transaction_id": transaction_id}

        if tool_name == "check_upi_payment":
            return {"upi_id": upi_id}

        if tool_name == "check_upi_collect":
            return {"upi_id": upi_id}

        if tool_name == "check_bank_transfer":
            return {"transfer_id": transfer_id}

        refund_tools = {
            "check_refund_amount",
            "check_refund_status",
        }

        if tool_name in refund_tools:
            return {"refund_id": refund_id}

        if tool_name == "check_merchant_credit":
            return {"account_id": account_id}

        return {}

    def _clarification_message(self, route):

        top_k = route.get("top_k", [])

        if len(top_k) >= 2:

            first = top_k[0]["intent"]
            second = top_k[1]["intent"]

            return (
                f"I need a little more information. "
                f"Your request may relate to {first} or {second}. "
                f"Please clarify which one you mean."
            )

        return "Please provide a little more detail about your request."


if __name__ == "__main__":

    orchestrator = FinAIOrchestrator()

    tests = [
        {
            "name": "Balance without authentication",
            "text": "How much is my account balance?",
            "authenticated": False,
            "confirmed": False,
        },
        {
            "name": "Balance after authentication",
            "text": "How much is my account balance?",
            "authenticated": True,
            "confirmed": False,
        },
        {
            "name": "Lost card without authentication",
            "text": "My card is lost",
            "authenticated": False,
            "confirmed": False,
        },
        {
            "name": "Lost card authenticated",
            "text": "My card is lost",
            "authenticated": True,
            "confirmed": False,
        },
        {
            "name": "Lost card authenticated + confirmed",
            "text": "My card is lost",
            "authenticated": True,
            "confirmed": True,
        },
        {
            "name": "UPI failure",
            "text": "My UPI payment failed",
            "authenticated": True,
            "confirmed": False,
        },
        {
            "name": "Ambiguous payment",
            "text": "The payment failed",
            "authenticated": True,
            "confirmed": False,
        },
        {
            "name": "Out of domain",
            "text": "Tell me about cricket",
            "authenticated": False,
            "confirmed": False,
        },
    ]

    print("=" * 80)
    print("FinAI END-TO-END ORCHESTRATOR TEST")
    print("=" * 80)

    for test in tests:

        print()
        print("-" * 80)
        print(test["name"])
        print("-" * 80)

        result = orchestrator.process(
            user_text=test["text"],
            authenticated=test["authenticated"],
            confirmed=test["confirmed"],
        )

        print("USER:", test["text"])
        print("STATUS:", result["status"])
        print("STAGE:", result["stage"])
        print(
            "INTENT:",
            result["router"].get("intent")
            if result.get("router")
            else None
        )

        if result.get("router"):
            print(
                "ROUTER CONFIDENCE:",
                f"{result['router']['confidence']:.4f}"
            )
            print(
                "ROUTER DECISION:",
                result["router"]["decision"]
            )

        if result.get("policy"):
            print(
                "POLICY:",
                result["policy"]["status"]
            )
            print(
                "AUTH REQUIRED:",
                result["policy"]["authentication_required"]
            )
            print(
                "CONFIRM REQUIRED:",
                result["policy"]["confirmation_required"]
            )

        if result.get("tool"):
            print(
                "TOOL:",
                result["tool"]["tool"]
            )
            print(
                "TOOL SUCCESS:",
                result["tool"]["success"]
            )
            print(
                "TOOL MESSAGE:",
                result["tool"]["message"]
            )
            print(
                "TOOL DATA:",
                result["tool"]["data"]
            )

        print("MESSAGE:", result["message"])
