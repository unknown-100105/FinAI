from datetime import datetime


# ============================================================
# FINAI DEMO FINANCIAL TOOLS
#
# IMPORTANT:
# These are DEMONSTRATION tools only.
# They do not connect to a real bank or move real money.
# ============================================================


def get_transaction_status(transaction_id=None):
    return {
        "status": "pending",
        "transaction_id": transaction_id or "DEMO-TXN-001",
        "amount": 1250.00,
        "currency": "INR",
        "merchant": "Demo Merchant",
        "timestamp": datetime.now().isoformat(),
    }


def get_account_balance():
    return {
        "available_balance": 25000.00,
        "currency": "INR",
        "account": "DEMO-ACCOUNT",
    }


def get_transaction_history():
    return {
        "transactions": [
            {
                "id": "TXN001",
                "amount": 500.00,
                "status": "success",
                "merchant": "Demo Store",
            },
            {
                "id": "TXN002",
                "amount": 1250.00,
                "status": "pending",
                "merchant": "Demo Merchant",
            },
        ]
    }


def get_refund_status():
    return {
        "refund_status": "processing",
        "refund_amount": 1250.00,
        "currency": "INR",
        "estimated_days": 5,
    }


def block_card():
    return {
        "status": "success",
        "message": "Demo card has been blocked.",
        "requires_real_authentication": True,
    }


def unblock_card():
    return {
        "status": "success",
        "message": "Demo card unblock request recorded.",
        "requires_real_authentication": True,
    }


def create_dispute():
    return {
        "status": "created",
        "dispute_id": "DEMO-DSP-001",
        "requires_real_authentication": True,
    }


def report_fraud():
    return {
        "status": "reported",
        "case_id": "DEMO-FRD-001",
        "requires_real_authentication": True,
    }


def secure_account():
    return {
        "status": "secured",
        "message": "Demo account security action recorded.",
        "requires_real_authentication": True,
    }


def check_kyc_status():
    return {
        "status": "verified",
        "requires_real_authentication": True,
    }


def update_kyc():
    return {
        "status": "submitted",
        "message": "Demo KYC update submitted.",
        "requires_real_authentication": True,
    }


def get_loan_status():
    return {
        "status": "under_review",
        "loan_id": "DEMO-LOAN-001",
        "requires_real_authentication": True,
    }


def get_loan_details():
    return {
        "loan_id": "DEMO-LOAN-001",
        "principal": 500000.00,
        "currency": "INR",
        "interest_rate": "demo",
        "status": "under_review",
        "requires_real_authentication": True,
    }


def get_cash_withdrawal_status():
    return {
        "status": "failed",
        "transaction_id": "DEMO-ATM-001",
        "amount": 5000.00,
        "currency": "INR",
        "message": "Demo ATM withdrawal failed.",
    }


def cancel_payment():
    return {
        "status": "cancel_request_created",
        "transaction_id": "DEMO-TXN-001",
        "requires_real_authentication": True,
    }


def get_account_status():
    return {
        "status": "active",
        "account": "DEMO-ACCOUNT",
        "requires_real_authentication": True,
    }


def update_profile():
    return {
        "status": "submitted",
        "message": "Demo profile update recorded.",
        "requires_real_authentication": True,
    }


def initiate_password_reset():
    return {
        "status": "reset_requested",
        "message": "Demo password reset request created.",
        "requires_real_authentication": True,
    }


# ============================================================
# COMPLETE TOOL REGISTRY
# ============================================================

TOOLS = {
    "get_transaction_status": get_transaction_status,
    "get_account_balance": get_account_balance,
    "get_transaction_history": get_transaction_history,
    "get_refund_status": get_refund_status,

    "block_card": block_card,
    "unblock_card": unblock_card,

    "create_dispute": create_dispute,
    "report_fraud": report_fraud,
    "secure_account": secure_account,

    "check_kyc_status": check_kyc_status,
    "update_kyc": update_kyc,

    "get_loan_status": get_loan_status,
    "get_loan_details": get_loan_details,

    "get_cash_withdrawal_status":
        get_cash_withdrawal_status,

    "cancel_payment": cancel_payment,

    "get_account_status": get_account_status,
    "update_profile": update_profile,
    "initiate_password_reset":
        initiate_password_reset,
}