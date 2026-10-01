from dataclasses import asdict
from typing import Optional

from policy.rules import get_policy


class PolicyEngine:

    def evaluate(
        self,
        intent: str,
        authenticated: bool = False,
        confirmed: bool = False,
    ):

        policy = get_policy(intent)

        if policy is None:
            return {
                "allowed": False,
                "status": "UNKNOWN_INTENT",
                "intent": intent,
                "risk_level": "unknown",
                "authentication_required": False,
                "confirmation_required": False,
                "tool": None,
                "category": "unknown",
                "message": "The requested intent is not supported.",
            }

        # Authentication gate
        if policy.authentication_required and not authenticated:
            return {
                "allowed": False,
                "status": "AUTH_REQUIRED",
                "intent": intent,
                "risk_level": policy.risk_level,
                "authentication_required": True,
                "confirmation_required": policy.confirmation_required,
                "tool": policy.tool,
                "category": policy.category,
                "message": "Authentication is required before accessing this operation.",
            }

        # Confirmation gate
        if policy.confirmation_required and not confirmed:
            return {
                "allowed": False,
                "status": "CONFIRMATION_REQUIRED",
                "intent": intent,
                "risk_level": policy.risk_level,
                "authentication_required": policy.authentication_required,
                "confirmation_required": True,
                "tool": policy.tool,
                "category": policy.category,
                "message": "Confirmation is required before executing this operation.",
            }

        return {
            "allowed": True,
            "status": "ALLOWED",
            "intent": intent,
            "risk_level": policy.risk_level,
            "authentication_required": policy.authentication_required,
            "confirmation_required": policy.confirmation_required,
            "tool": policy.tool,
            "category": policy.category,
            "message": "Operation is permitted by policy.",
        }


if __name__ == "__main__":

    engine = PolicyEngine()

    tests = [
        ("ACCOUNT_BALANCE", False, False),
        ("ACCOUNT_BALANCE", True, False),
        ("CARD_LOST", False, False),
        ("CARD_LOST", True, False),
        ("CARD_LOST", True, True),
        ("FRAUD_REPORT", False, False),
        ("FRAUD_REPORT", True, False),
        ("FRAUD_REPORT", True, True),
        ("EMI_QUERY", False, False),
        ("SUPPORT_REQUEST", False, False),
        ("UNKNOWN", True, True),
    ]

    print("=" * 80)
    print("FinAI POLICY ENGINE TEST")
    print("=" * 80)

    for intent, authenticated, confirmed in tests:

        result = engine.evaluate(
            intent=intent,
            authenticated=authenticated,
            confirmed=confirmed,
        )

        print()
        print("INTENT:", intent)
        print("AUTHENTICATED:", authenticated)
        print("CONFIRMED:", confirmed)
        print("RESULT:", result["status"])
        print("ALLOWED:", result["allowed"])
        print("RISK:", result["risk_level"])
        print("AUTH REQUIRED:", result["authentication_required"])
        print("CONFIRM REQUIRED:", result["confirmation_required"])
        print("TOOL:", result["tool"])
        print("MESSAGE:", result["message"])
