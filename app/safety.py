from dataclasses import dataclass
from typing import Optional


@dataclass
class SafetyResult:
    allowed: bool
    reason: str
    requires_authentication: bool = False
    requires_confirmation: bool = False


# ------------------------------------------------------------
# Sensitive operations
# ------------------------------------------------------------

SENSITIVE_TOOLS = {
    "block_card",
    "unblock_card",
    "create_dispute",
    "report_fraud",
    "secure_account",
    "initiate_password_reset",
    "update_kyc",
    "cancel_payment",
}


# ------------------------------------------------------------
# Privacy / security phrases
# ------------------------------------------------------------

BLOCKED_PATTERNS = [
    "another customer's balance",
    "someone else's balance",
    "another user's account",
    "someone else's account",
    "give me another person's",
    "show me another customer's",
]


# ------------------------------------------------------------
# High-risk financial phrases
# ------------------------------------------------------------

HIGH_RISK_PATTERNS = [
    "transfer money",
    "send money",
    "move money",
    "withdraw money",
    "change bank account",
    "change beneficiary",
    "change account number",
]


def check_input(
    text: str,
    tool_name: Optional[str] = None,
) -> SafetyResult:

    if not text or not text.strip():

        return SafetyResult(
            allowed=False,
            reason="Empty request.",
        )

    normalized = text.lower().strip()

    # --------------------------------------------------------
    # Privacy protection
    # --------------------------------------------------------

    for pattern in BLOCKED_PATTERNS:

        if pattern in normalized:

            return SafetyResult(
                allowed=False,
                reason=(
                    "Request involves another person's "
                    "private financial information."
                ),
            )

    # --------------------------------------------------------
    # Sensitive tool handling
    # --------------------------------------------------------

    if tool_name in SENSITIVE_TOOLS:

        return SafetyResult(
            allowed=True,
            reason=(
                "Sensitive operation allowed only "
                "after authentication and backend validation."
            ),
            requires_authentication=True,
            requires_confirmation=True,
        )

    # --------------------------------------------------------
    # High-risk financial action
    # --------------------------------------------------------

    for pattern in HIGH_RISK_PATTERNS:

        if pattern in normalized:

            return SafetyResult(
                allowed=True,
                reason=(
                    "Financial action requires "
                    "authentication and authorization."
                ),
                requires_authentication=True,
                requires_confirmation=True,
            )

    # --------------------------------------------------------
    # Normal request
    # --------------------------------------------------------

    return SafetyResult(
        allowed=True,
        reason="Request passed basic safety checks.",
    )


def check_tool_authorization(
    tool_name: str,
    authenticated: bool,
    confirmed: bool = False,
) -> SafetyResult:

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