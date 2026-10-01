import re
from dataclasses import dataclass
from typing import Optional

from .safety import check_request, authorize_tool
from .tools import TOOLS


@dataclass
class RouteResult:
    intent: Optional[str]
    risk_level: str
    requires_tool: bool
    tool_name: Optional[str]
    allowed: bool
    reason: str


# ============================================================
# TOOL-BASED INTENTS
# ============================================================

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

    "CASH_WITHDRAWAL_FAILED": "get_cash_withdrawal_status",
    "CASH_WITHDRAWAL_STATUS": "get_cash_withdrawal_status",

    "REFUND_PENDING": "get_refund_status",
    "REFUND_FAILED": "get_refund_status",
    "REFUND_RECEIVED": "get_refund_status",
    "REFUND_AMOUNT_WRONG": "get_refund_status",

    "DISPUTE_TRANSACTION": "create_dispute",
    "FRAUD_REPORT": "report_fraud",
    "UNKNOWN_TRANSACTION": "get_transaction_status",
    "SUSPICIOUS_ACTIVITY": "report_fraud",
    "ACCOUNT_COMPROMISED": "secure_account",

    "CARD_LOST": "block_card",
    "CARD_STOLEN": "block_card",
    "CARD_BLOCK": "block_card",
    "CARD_UNBLOCK": "unblock_card",

    "ACCOUNT_BALANCE": "get_account_balance",
    "TRANSACTION_HISTORY": "get_transaction_history",
    "ACCOUNT_LOCKED": "get_account_status",
    "PROFILE_UPDATE": "update_profile",
    "PASSWORD_RESET": "initiate_password_reset",

    "KYC_STATUS": "check_kyc_status",
    "KYC_UPDATE": "update_kyc",

    "LOAN_STATUS": "get_loan_status",
    "EMI_QUERY": "get_loan_details",
    "INTEREST_QUERY": "get_loan_details",
}


# ============================================================
# INTENTS THAT DO NOT NEED A BACKEND TOOL
#
# These are handled through normal model/RAG responses.
# ============================================================

NO_TOOL_INTENTS = {
    "BANK_TRANSFER_FAILED",
    "BENEFICIARY_ISSUE",
    "CARD_ACTIVATION",
    "CARD_PAYMENT_FAILED",
    "KYC_DOCUMENTS",
    "KYC_FAILED",
    "LIMIT_QUERY",
    "LOAN_ELIGIBILITY",
    "PAYMENT_FAILED",
    "PAYMENT_LIMIT",
    "PIN_FAILED",
    "SUPPORT_REQUEST",
    "UPI_COLLECT_REQUEST",
    "UPI_ID_ISSUE",
    "UPI_PAYMENT_FAILED",
}


# ============================================================
# PARSE MODEL OUTPUT
# ============================================================

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

    tool_required_match = re.search(
        r"REQUIRES_TOOL:\s*(true|false)",
        model_output,
        re.IGNORECASE,
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
        tool_required_match.group(1).lower() == "true"
        if tool_required_match
        else False
    )

    return (
        intent,
        risk_level,
        requires_tool,
    )


# ============================================================
# ROUTER
# ============================================================

def route_model_output(
    user_text: str,
    model_output: str,
) -> RouteResult:

    (
        intent,
        risk_level,
        requires_tool,
    ) = parse_model_output(model_output)

    # --------------------------------------------------------
    # Invalid model output
    # --------------------------------------------------------

    if intent is None:

        return RouteResult(
            intent=None,
            risk_level="unknown",
            requires_tool=False,
            tool_name=None,
            allowed=False,
            reason="FinAI did not return a valid intent.",
        )

    # --------------------------------------------------------
    # Verify that the intent is one of our supported intents
    # --------------------------------------------------------

    if (
        intent not in INTENT_TO_TOOL
        and intent not in NO_TOOL_INTENTS
    ):

        return RouteResult(
            intent=intent,
            risk_level=risk_level,
            requires_tool=False,
            tool_name=None,
            allowed=False,
            reason=f"Unsupported intent: {intent}.",
        )

    # --------------------------------------------------------
    # NO-TOOL INTENT
    # --------------------------------------------------------

    if intent in NO_TOOL_INTENTS:

        safety = check_request(
            user_text,
            tool_name=None,
        )

        if not safety.allowed:

            return RouteResult(
                intent=intent,
                risk_level=risk_level,
                requires_tool=False,
                tool_name=None,
                allowed=False,
                reason=safety.reason,
            )

        return RouteResult(
            intent=intent,
            risk_level=risk_level,
            requires_tool=False,
            tool_name=None,
            allowed=True,
            reason="Intent does not require a backend tool.",
        )

    # --------------------------------------------------------
    # TOOL INTENT
    # --------------------------------------------------------

    selected_tool = INTENT_TO_TOOL.get(
        intent
    )

    if requires_tool and selected_tool is None:

        return RouteResult(
            intent=intent,
            risk_level=risk_level,
            requires_tool=True,
            tool_name=None,
            allowed=False,
            reason=(
                f"No approved tool mapping exists "
                f"for intent {intent}."
            ),
        )

    # --------------------------------------------------------
    # Verify that the tool actually exists
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
                    f"Tool '{selected_tool}' "
                    f"is not registered."
                ),
            )

    # --------------------------------------------------------
    # Safety layer
    # --------------------------------------------------------

    safety = check_request(
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


# ============================================================
# TOOL EXECUTION
# ============================================================

def execute_tool(
    route: RouteResult,
    authenticated: bool = False,
    confirmed: bool = False,
):

    if not route.allowed:

        return {
            "status": "blocked",
            "reason": route.reason,
        }

    if route.tool_name is None:

        return {
            "status": "no_tool",
            "message": "No backend tool is required.",
        }

    # --------------------------------------------------------
    # Authorization
    # --------------------------------------------------------

    authorization = authorize_tool(
        tool_name=route.tool_name,
        authenticated=authenticated,
        confirmed=confirmed,
    )

    if not authorization.allowed:

        return {
            "status": "authorization_required",
            "reason": authorization.reason,
        }

    # --------------------------------------------------------
    # Get registered tool
    # --------------------------------------------------------

    tool = TOOLS.get(
        route.tool_name
    )

    if tool is None:

        return {
            "status": "tool_not_found",
            "reason": (
                f"Tool '{route.tool_name}' "
                f"is not registered."
            ),
        }

    # --------------------------------------------------------
    # Execute
    # --------------------------------------------------------

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