from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class IntentPolicy:
    risk_level: str
    authentication_required: bool
    confirmation_required: bool
    tool: Optional[str]
    category: str


POLICIES = {

    # ---------------------------------------------------------
    # Account
    # ---------------------------------------------------------

    "ACCOUNT_BALANCE": IntentPolicy(
        "medium", True, False,
        "get_account_balance", "account"
    ),

    "ACCOUNT_COMPROMISED": IntentPolicy(
        "high", True, True,
        "secure_account", "security"
    ),

    "ACCOUNT_LOCKED": IntentPolicy(
        "medium", True, False,
        "check_account_lock", "account"
    ),

    "PASSWORD_RESET": IntentPolicy(
        "high", True, True,
        "reset_password", "security"
    ),

    "PROFILE_UPDATE": IntentPolicy(
        "medium", True, True,
        "update_profile", "account"
    ),

    # ---------------------------------------------------------
    # Card
    # ---------------------------------------------------------

    "CARD_ACTIVATION": IntentPolicy(
        "medium", True, True,
        "activate_card", "card"
    ),

    "CARD_BLOCK": IntentPolicy(
        "high", True, True,
        "block_card", "card"
    ),

    "CARD_LOST": IntentPolicy(
        "high", True, True,
        "block_card", "card"
    ),

    "CARD_STOLEN": IntentPolicy(
        "high", True, True,
        "block_card", "card"
    ),

    "CARD_UNBLOCK": IntentPolicy(
        "high", True, True,
        "unblock_card", "card"
    ),

    "CARD_PAYMENT_FAILED": IntentPolicy(
        "medium", True, False,
        "check_card_payment", "payment"
    ),

    "PIN_FAILED": IntentPolicy(
        "medium", True, False,
        "check_pin_status", "card"
    ),

    # ---------------------------------------------------------
    # Payments
    # ---------------------------------------------------------

    "PAYMENT_FAILED": IntentPolicy(
        "medium", True, False,
        "check_payment_status", "payment"
    ),

    "PAYMENT_PENDING": IntentPolicy(
        "medium", True, False,
        "check_payment_status", "payment"
    ),

    "PAYMENT_SUCCESS": IntentPolicy(
        "medium", True, False,
        "check_payment_status", "payment"
    ),

    "PAYMENT_CANCEL_REQUEST": IntentPolicy(
        "high", True, True,
        "cancel_payment", "payment"
    ),

    "PAYMENT_LIMIT": IntentPolicy(
        "low", False, False,
        "get_payment_limit", "information"
    ),

    # ---------------------------------------------------------
    # UPI
    # ---------------------------------------------------------

    "UPI_COLLECT_REQUEST": IntentPolicy(
        "medium", True, False,
        "check_upi_collect", "upi"
    ),

    "UPI_ID_ISSUE": IntentPolicy(
        "medium", True, False,
        "check_upi_id", "upi"
    ),

    "UPI_PAYMENT_FAILED": IntentPolicy(
        "medium", True, False,
        "check_upi_payment", "upi"
    ),

    "UPI_PENDING": IntentPolicy(
        "medium", True, False,
        "check_upi_payment", "upi"
    ),

    # ---------------------------------------------------------
    # Bank transfers
    # ---------------------------------------------------------

    "BANK_TRANSFER_FAILED": IntentPolicy(
        "medium", True, False,
        "check_bank_transfer", "transfer"
    ),

    "BANK_TRANSFER_PENDING": IntentPolicy(
        "medium", True, False,
        "check_bank_transfer", "transfer"
    ),

    "BANK_TRANSFER_STATUS": IntentPolicy(
        "medium", True, False,
        "check_bank_transfer", "transfer"
    ),

    "BENEFICIARY_ISSUE": IntentPolicy(
        "medium", True, False,
        "check_beneficiary", "transfer"
    ),

    # ---------------------------------------------------------
    # Cash withdrawal
    # ---------------------------------------------------------

    "CASH_WITHDRAWAL_FAILED": IntentPolicy(
        "medium", True, False,
        "check_cash_withdrawal", "cash"
    ),

    "CASH_WITHDRAWAL_STATUS": IntentPolicy(
        "medium", True, False,
        "check_cash_withdrawal", "cash"
    ),

    # ---------------------------------------------------------
    # Transactions
    # ---------------------------------------------------------

    "TRANSACTION_HISTORY": IntentPolicy(
        "medium", True, False,
        "get_transaction_history", "transaction"
    ),

    "TRANSACTION_REVERSED": IntentPolicy(
        "medium", True, False,
        "check_reversed_transaction", "transaction"
    ),

    "DUPLICATE_TRANSACTION": IntentPolicy(
        "high", True, True,
        "report_duplicate_transaction", "transaction"
    ),

    "WRONG_AMOUNT": IntentPolicy(
        "high", True, True,
        "report_wrong_amount", "transaction"
    ),

    "UNKNOWN_TRANSACTION": IntentPolicy(
        "high", True, True,
        "investigate_unknown_transaction", "security"
    ),

    "DISPUTE_TRANSACTION": IntentPolicy(
        "high", True, True,
        "create_transaction_dispute", "dispute"
    ),

    # ---------------------------------------------------------
    # Fraud / security
    # ---------------------------------------------------------

    "FRAUD_REPORT": IntentPolicy(
        "high", True, True,
        "report_fraud", "security"
    ),

    "SUSPICIOUS_ACTIVITY": IntentPolicy(
        "high", True, True,
        "investigate_suspicious_activity", "security"
    ),

    # ---------------------------------------------------------
    # Refunds
    # ---------------------------------------------------------

    "REFUND_AMOUNT_WRONG": IntentPolicy(
        "medium", True, True,
        "check_refund_amount", "refund"
    ),

    "REFUND_FAILED": IntentPolicy(
        "medium", True, False,
        "check_refund_status", "refund"
    ),

    "REFUND_PENDING": IntentPolicy(
        "medium", True, False,
        "check_refund_status", "refund"
    ),

    "REFUND_RECEIVED": IntentPolicy(
        "medium", True, False,
        "check_refund_status", "refund"
    ),

    "MERCHANT_NOT_CREDITED": IntentPolicy(
        "medium", True, False,
        "check_merchant_credit", "merchant"
    ),

    # ---------------------------------------------------------
    # KYC
    # ---------------------------------------------------------

    "KYC_DOCUMENTS": IntentPolicy(
        "low", False, False,
        None, "kyc"
    ),

    "KYC_FAILED": IntentPolicy(
        "medium", True, False,
        "check_kyc_status", "kyc"
    ),

    "KYC_STATUS": IntentPolicy(
        "medium", True, False,
        "check_kyc_status", "kyc"
    ),

    "KYC_UPDATE": IntentPolicy(
        "high", True, True,
        "update_kyc", "kyc"
    ),

    # ---------------------------------------------------------
    # Loans / finance information
    # ---------------------------------------------------------

    "EMI_QUERY": IntentPolicy(
        "low", False, False,
        None, "financial_information"
    ),

    "INTEREST_QUERY": IntentPolicy(
        "low", False, False,
        None, "financial_information"
    ),

    "LOAN_ELIGIBILITY": IntentPolicy(
        "low", False, False,
        None, "financial_information"
    ),

    "LOAN_STATUS": IntentPolicy(
        "medium", True, False,
        "check_loan_status", "loan"
    ),

    "LIMIT_QUERY": IntentPolicy(
        "low", False, False,
        "get_account_limit", "information"
    ),

    # ---------------------------------------------------------
    # Support
    # ---------------------------------------------------------

    "SUPPORT_REQUEST": IntentPolicy(
        "low", False, False,
        "create_support_ticket", "support"
    ),
}


def get_policy(intent: str) -> Optional[IntentPolicy]:
    return POLICIES.get(intent)


def is_known_intent(intent: str) -> bool:
    return intent in POLICIES
