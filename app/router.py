import re
from dataclasses import dataclass
from typing import Optional

from .safety import check_input
from .financial_tools import TOOLS


@dataclass
class RouteResult:
    intent: Optional[str]
    risk_level: str
    requires_tool: bool
    tool_name: Optional[str]
    allowed: bool
    reason: str


# ------------------------------------------------------------
# Intent → Tool mapping
# ------------------------------------------------------------

INTENT_TO_TOOL = {
    "PAYMENT_PENDING": "get_transaction_status",
    "PAYMENT_SUCCESS": "get_transaction_status",
    "MERCHANT_NOT_CREDITED": "get_transaction_status",
    "WRONG_AMOUNT": "get_transaction_status",
    "DUPLICATE_TRANSACTION": "get_transaction_status",
    "TRANSACTION_REVERSED": "get_transaction_status",

    "PAYMENT_CANCEL_REQUEST": "cancel_payment",

    "UPI_PENDING": "get_transaction_status",

    "BANK_TRANSFER_PENDING": "get_transaction_status",
    "BANK_TRANSFER_STATUS": "get_transaction_status",

    "CASH_WITHDRAWAL_FAILED":
        "get_cash_withdrawal_status",

    "CASH_WITHDRAWAL_STATUS":
        "get_cash_withdrawal_status",

    "REFUND_PENDING":
        "get_refund_status",

    "REFUND_FAILED":
        "get_refund_status",

    "REFUND_RECEIVED":
        "get_refund_status",

    "REFUND_AMOUNT_WRONG":
        "get_refund_status",

    "DISPUTE_TRANSACTION":
        "create_dispute",

    "FRAUD_REPORT":
        "report_fraud",

    "UNKNOWN_TRANSACTION":
        "get_transaction_status",

    "SUSPICIOUS_ACTIVITY":
        "report_fraud",

    "ACCOUNT_COMPROMISED":
        "secure_account",

    "CARD_LOST":
        "block_card",

    "CARD_STOLEN":
        "block_card",

    "CARD_BLOCK":
        "block_card",

    "CARD_UNBLOCK":
        "unblock_card",

    "ACCOUNT_BALANCE":
        "get_account_balance",

    "TRANSACTION_HISTORY":
        "get_transaction_history",

    "ACCOUNT_LOCKED":
        "get_account_status",

    "PROFILE_UPDATE":
        "update_profile",

    "PASSWORD_RESET":
        "initiate_password_reset",

    "KYC_STATUS":
        "check_kyc_status",

    "KYC_UPDATE":
        "update_kyc",

    "LOAN_STATUS":
        "get_loan_status",

    "EMI_QUERY":
        "get_loan_details",

    "INTEREST_QUERY":
        "get_loan_details",
}


# ------------------------------------------------------------
# Parse the structured output from the fine-tuned model
# ------------------------------------------------------------

def parse_model_output(model_output: str):

    intent_match = re.search(
        r"INTENT:\s*([A-Z0-9_]+)",
        model_output,
        re.IGNORECASE,
    )

    risk_match = re.search(
        r"RISK_LEVEL:\s*(\w+)",
        model_output,
        re.IGNORECASE,
    )

    requires_tool_match = re.search(
        r"REQUIRES_TOOL:\s*(true|false)",
        model_output,
        re.IGNORECASE,
    )

	tool_match = re.search(
    r"^\s*TOOL:\s*([A-Z0-9_]+|none)\s*$",
    model_output,
    re.IGNORECASE | re.MULTILINE,
)

    intent = (
        intent_match.group(1).upper()
        if intent_match
        else None
    )

    risk_level = (
        risk_match.group(1).lower()
        if risk_match
        else "unknown"
    )

    requires_tool = (
        requires_tool_match.group(1).lower() == "true"
        if requires_tool_match
        else False
    )

    tool_name = None

    if tool_match:

        raw_tool = tool_match.group(1)

        if raw_tool.lower() != "none":

            tool_name = raw_tool.lower()

    return (
        intent,
        risk_level,
        requires_tool,
        tool_name,
    )


# ------------------------------------------------------------
# Validate and route the model output
# ------------------------------------------------------------

def route_model_output(
    user_text: str,
    model_output: str,
) -> RouteResult:

    (
        intent,
        risk_level,
        requires_tool,
        model_tool,
    ) = parse_model_output(model_output)

    if intent is None:

        return RouteResult(
            intent=None,
            risk_level="unknown",
            requires_tool=False,
            tool_name=None,
            allowed=False,
            reason=(
                "Model did not return a valid intent."
            ),
        )

    expected_tool = INTENT_TO_TOOL.get(
        intent
    )

    # --------------------------------------------------------
    # Check consistency between intent and tool
    # --------------------------------------------------------

    if requires_tool and expected_tool is None:

        return RouteResult(
            intent=intent,
            risk_level=risk_level,
            requires_tool=True,
            tool_name=None,
            allowed=False,
            reason=(
                f"Intent {intent} requires a tool, "
                "but no approved tool is mapped."
            ),
        )

    # --------------------------------------------------------
    # Never trust the model's tool name blindly.
    # Use our server-side mapping.
    # --------------------------------------------------------

    selected_tool = expected_tool

    if model_tool is not None:

        if (
            expected_tool is not None
            and model_tool != expected_tool
        ):

            return RouteResult(
                intent=intent,
                risk_level=risk_level,
                requires_tool=requires_tool,
                tool_name=None,
                allowed=False,
                reason=(
                    "Model requested a tool that does not "
                    "match the approved intent-to-tool mapping."
                ),
            )

    # --------------------------------------------------------
    # Tool must exist in our actual tool registry
    # --------------------------------------------------------

    if selected_tool is not None:

        if selected_tool not in TOOLS:

            return RouteResult(
                intent=intent,
                risk_level=risk_level,
                requires_tool=requires_tool,
                tool_name=None,
                allowed=False,
                reason=(
                    f"Tool {selected_tool} is not registered."
                ),
            )

    # --------------------------------------------------------
    # Safety check
    # --------------------------------------------------------

    safety = check_input(
        user_text,
        tool_name=selected_tool,
    )

    if not safety.allowed:

        return RouteResult(
            intent=intent,
            risk_level=risk_level,
            requires_tool=requires_tool,
            tool_name=selected_tool,
            allowed=False,
            reason=safety.reason,
        )

    return RouteResult(
        intent=intent,
        risk_level=risk_level,
        requires_tool=requires_tool,
        tool_name=selected_tool,
        allowed=True,
        reason=safety.reason,
    )


# ------------------------------------------------------------
# Execute an approved low-risk demo tool
# ------------------------------------------------------------

def execute_demo_tool(
    route: RouteResult,
    authenticated=False,
    confirmed=False,
):

    if not route.allowed:

        return {
            "status": "blocked",
            "reason": route.reason,
        }

    if route.tool_name is None:

        return {
            "status": "no_tool",
            "message": (
                "No financial tool is required."
            ),
        }

    # Import authorization check.
    from safety import check_tool_authorization

    authorization = check_tool_authorization(
        tool_name=route.tool_name,
        authenticated=authenticated,
        confirmed=confirmed,
    )

    if not authorization.allowed:

        return {
            "status": "authorization_required",
            "reason": authorization.reason,
        }

    tool = TOOLS[route.tool_name]

    try:

        result = tool()

        return {
            "status": "success",
            "tool": route.tool_name,
            "result": result,
        }

    except Exception as error:

        return {
            "status": "tool_error",
            "tool": route.tool_name,
            "error": str(error),
        }