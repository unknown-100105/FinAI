from dataclasses import dataclass
from typing import Optional


@dataclass
class SafetyResult:
    allowed: bool
    reason: str
    requires_authentication: bool = False
    requires_confirmation: bool = False


SENSITIVE_TOOLS = {
    "block_card",
    "unblock_card",
    "create_dispute",
    "report_fraud",
    "secure_account",
    "cancel_payment",
    "initiate_password_reset",
    "update_kyc",
}


PRIVACY_BLOCK_PATTERNS = [
    "another customer's balance",
    "another customers balance",
    "someone else's balance",
    "someone elses balance",
    "another person's account",
    "another persons account",
    "someone else's account",
    "someone elses account",
    "another user's account",
    "another users account",
]


HIGH_RISK_PATTERNS = [
    "transfer money",
    "send money",
    "move money",
    "withdraw money",
    "change beneficiary",
    "change bank account",
]


def check_request(
    user_text: str,
    tool_name: Optional[str] = None,
) -> SafetyResult:

    if not user_text or not user_text.strip():
        return SafetyResult(
            allowed=False,
            reason="Request is empty.",
        )

    text = user_text.lower().strip()

    # Privacy protection
    for pattern in PRIVACY_BLOCK_PATTERNS:
        if pattern in text:
            return SafetyResult(
                allowed=False,
                reason=(
                    "The request involves another "
                    "person's private financial information."
                ),
            )

    # Sensitive tool protection
    if tool_name in SENSITIVE_TOOLS:
        return SafetyResult(
            allowed=True,
            reason=(
                "Sensitive operation requires "
                "authentication and confirmation."
            ),
            requires_authentication=True,
            requires_confirmation=True,
        )

    # High-risk financial actions
    for pattern in HIGH_RISK_PATTERNS:
        if pattern in text:
            return SafetyResult(
                allowed=True,
                reason=(
                    "Financial action requires "
                    "authentication and authorization."
                ),
                requires_authentication=True,
                requires_confirmation=True,
            )

    return SafetyResult(
        allowed=True,
        reason="Request passed basic safety checks.",
    )


def authorize_tool(
    tool_name: str,
    authenticated: bool,
    confirmed: bool,
) -> SafetyResult:

    if not tool_name:
        return SafetyResult(
            allowed=False,
            reason="No tool was specified.",
        )

    if tool_name in SENSITIVE_TOOLS:

        if not authenticated:
            return SafetyResult(
                allowed=False,
                reason=(
                    "Authentication is required "
                    "for this operation."
                ),
                requires_authentication=True,
            )

        if not confirmed:
            return SafetyResult(
                allowed=False,
                reason=(
                    "Explicit confirmation is required "
                    "before executing this operation."
                ),
                requires_confirmation=True,
            )

    return SafetyResult(
        allowed=True,
        reason="Tool authorization passed.",
    )