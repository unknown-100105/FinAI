from datetime import datetime


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


def check_kyc_status():
    return {
        "status": "verified",
        "requires_real_authentication": True,
    }


def get_loan_status():
    return {
        "status": "under_review",
        "loan_id": "DEMO-LOAN-001",
        "requires_real_authentication": True,
    }


TOOLS = {
    "get_transaction_status": get_transaction_status,
    "get_account_balance": get_account_balance,
    "get_transaction_history": get_transaction_history,
    "get_refund_status": get_refund_status,
    "block_card": block_card,
    "create_dispute": create_dispute,
    "report_fraud": report_fraud,
    "check_kyc_status": check_kyc_status,
    "get_loan_status": get_loan_status,
}