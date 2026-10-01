MOCK_ACCOUNTS = {
    "ACC1001": {
        "customer_name": "Test User",
        "balance": 58240.75,
        "available_balance": 54120.50,
        "currency": "INR",
        "status": "active",
    },
    "ACC1002": {
        "customer_name": "Demo User",
        "balance": 125000.00,
        "available_balance": 119500.00,
        "currency": "INR",
        "status": "active",
    },
}

MOCK_CARDS = {
    "CARD1001": {
        "account_id": "ACC1001",
        "status": "active",
        "masked_number": "**** **** **** 4821",
    },
    "CARD1002": {
        "account_id": "ACC1002",
        "status": "blocked",
        "masked_number": "**** **** **** 7314",
    },
}

MOCK_TRANSACTIONS = {
    "ACC1001": [
        {
            "transaction_id": "TXN001",
            "type": "UPI",
            "amount": 850.00,
            "status": "SUCCESS",
            "merchant": "Coffee Shop",
        },
        {
            "transaction_id": "TXN002",
            "type": "CARD",
            "amount": 2400.00,
            "status": "FAILED",
            "merchant": "Online Store",
        },
        {
            "transaction_id": "TXN003",
            "type": "UPI",
            "amount": 1500.00,
            "status": "PENDING",
            "merchant": "Utility Bill",
        },
    ]
}

MOCK_TRANSFERS = {
    "TRF1001": {
        "account_id": "ACC1001",
        "amount": 5000.00,
        "status": "PENDING",
        "beneficiary": "Demo Beneficiary",
    }
}

MOCK_UPI = {
    "UPI1001": {
        "account_id": "ACC1001",
        "amount": 850.00,
        "status": "FAILED",
        "recipient": "demo@upi",
    },
    "UPI1002": {
        "account_id": "ACC1001",
        "amount": 1500.00,
        "status": "PENDING",
        "recipient": "utility@upi",
    }
}

MOCK_REFUNDS = {
    "REF1001": {
        "account_id": "ACC1001",
        "amount": 2400.00,
        "status": "PENDING",
        "merchant": "Online Store",
    }
}

MOCK_KYC = {
    "ACC1001": {
        "status": "VERIFIED",
        "documents": [
            "PAN",
            "Aadhaar",
        ],
    }
}
