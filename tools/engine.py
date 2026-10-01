from datetime import datetime

from tools.mock_data.database import (
    MOCK_ACCOUNTS,
    MOCK_CARDS,
    MOCK_TRANSACTIONS,
    MOCK_TRANSFERS,
    MOCK_UPI,
    MOCK_REFUNDS,
    MOCK_KYC,
)


class MockToolEngine:

    def __init__(self):
        self.accounts = MOCK_ACCOUNTS
        self.cards = MOCK_CARDS
        self.transactions = MOCK_TRANSACTIONS
        self.transfers = MOCK_TRANSFERS
        self.upi = MOCK_UPI
        self.refunds = MOCK_REFUNDS
        self.kyc = MOCK_KYC

    def _result(self, tool, success, data=None, message=""):
        return {
            "tool": tool,
            "success": success,
            "timestamp": datetime.now().isoformat(),
            "data": data or {},
            "message": message,
        }

    def get_account_balance(self, account_id):
        account = self.accounts.get(account_id)

        if not account:
            return self._result(
                "get_account_balance",
                False,
                message="Account not found."
            )

        return self._result(
            "get_account_balance",
            True,
            {
                "account_id": account_id,
                "balance": account["balance"],
                "available_balance": account["available_balance"],
                "currency": account["currency"],
            },
            "Account balance retrieved successfully."
        )

    def get_transaction_history(self, account_id):
        transactions = self.transactions.get(account_id)

        if transactions is None:
            return self._result(
                "get_transaction_history",
                False,
                message="Account transaction history not found."
            )

        return self._result(
            "get_transaction_history",
            True,
            {
                "account_id": account_id,
                "transactions": transactions,
            },
            "Transaction history retrieved successfully."
        )

    def check_payment_status(self, transaction_id):
        for account_id, transactions in self.transactions.items():
            for txn in transactions:
                if txn["transaction_id"] == transaction_id:
                    return self._result(
                        "check_payment_status",
                        True,
                        txn,
                        "Payment status retrieved."
                    )

        return self._result(
            "check_payment_status",
            False,
            message="Transaction not found."
        )

    def check_upi_payment(self, upi_id):
        payment = self.upi.get(upi_id)

        if not payment:
            return self._result(
                "check_upi_payment",
                False,
                message="UPI transaction not found."
            )

        return self._result(
            "check_upi_payment",
            True,
            payment,
            "UPI payment status retrieved."
        )

    def check_bank_transfer(self, transfer_id):
        transfer = self.transfers.get(transfer_id)

        if not transfer:
            return self._result(
                "check_bank_transfer",
                False,
                message="Bank transfer not found."
            )

        return self._result(
            "check_bank_transfer",
            True,
            transfer,
            "Bank transfer status retrieved."
        )

    def check_refund_status(self, refund_id):
        refund = self.refunds.get(refund_id)

        if not refund:
            return self._result(
                "check_refund_status",
                False,
                message="Refund not found."
            )

        return self._result(
            "check_refund_status",
            True,
            refund,
            "Refund status retrieved."
        )

    def check_kyc_status(self, account_id):
        kyc = self.kyc.get(account_id)

        if not kyc:
            return self._result(
                "check_kyc_status",
                False,
                message="KYC record not found."
            )

        return self._result(
            "check_kyc_status",
            True,
            kyc,
            "KYC status retrieved."
        )

    def block_card(self, card_id):
        card = self.cards.get(card_id)

        if not card:
            return self._result(
                "block_card",
                False,
                message="Card not found."
            )

        if card["status"] == "blocked":
            return self._result(
                "block_card",
                True,
                {
                    "card_id": card_id,
                    "status": "blocked",
                },
                "Card is already blocked."
            )

        card["status"] = "blocked"

        return self._result(
            "block_card",
            True,
            {
                "card_id": card_id,
                "status": "blocked",
            },
            "Card blocked successfully."
        )

    def unblock_card(self, card_id):
        card = self.cards.get(card_id)

        if not card:
            return self._result(
                "unblock_card",
                False,
                message="Card not found."
            )

        card["status"] = "active"

        return self._result(
            "unblock_card",
            True,
            {
                "card_id": card_id,
                "status": "active",
            },
            "Card unblocked successfully."
        )

    def get_payment_limit(self, account_id):
        if account_id not in self.accounts:
            return self._result(
                "get_payment_limit",
                False,
                message="Account not found."
            )

        return self._result(
            "get_payment_limit",
            True,
            {
                "account_id": account_id,
                "daily_limit": 100000,
                "per_transaction_limit": 50000,
                "currency": "INR",
            },
            "Payment limits retrieved."
        )

    def check_card_payment(self, transaction_id):
        return self.check_payment_status(transaction_id)

    def check_pin_status(self, card_id):
        card = self.cards.get(card_id)

        if not card:
            return self._result(
                "check_pin_status",
                False,
                message="Card not found."
            )

        return self._result(
            "check_pin_status",
            True,
            {
                "card_id": card_id,
                "pin_status": "active",
                "attempts_remaining": 3,
            },
            "PIN status retrieved."
        )

    def get_account_limit(self, account_id):
        return self.get_payment_limit(account_id)

    def execute(self, tool_name, **kwargs):
        tool = getattr(self, tool_name, None)

        if not callable(tool):
            return self._result(
                tool_name,
                False,
                message=f"Tool '{tool_name}' is not registered."
            )

        try:
            return tool(**kwargs)

        except TypeError as exc:
            return self._result(
                tool_name,
                False,
                message=f"Invalid tool arguments: {exc}"
            )

        except Exception as exc:
            return self._result(
                tool_name,
                False,
                message=f"Tool execution error: {exc}"
            )


if __name__ == "__main__":

    engine = MockToolEngine()

    tests = [
        ("get_account_balance", {"account_id": "ACC1001"}),
        ("get_transaction_history", {"account_id": "ACC1001"}),
        ("check_payment_status", {"transaction_id": "TXN002"}),
        ("check_upi_payment", {"upi_id": "UPI1001"}),
        ("check_bank_transfer", {"transfer_id": "TRF1001"}),
        ("check_refund_status", {"refund_id": "REF1001"}),
        ("check_kyc_status", {"account_id": "ACC1001"}),
        ("block_card", {"card_id": "CARD1001"}),
        ("get_payment_limit", {"account_id": "ACC1001"}),
        ("invalid_tool", {}),
    ]

    print("=" * 80)
    print("FinAI MOCK TOOL ENGINE TEST")
    print("=" * 80)

    for tool_name, kwargs in tests:

        print()
        print("TOOL:", tool_name)
        print("ARGS:", kwargs)

        result = engine.execute(
            tool_name,
            **kwargs
        )

        print("SUCCESS:", result["success"])
        print("MESSAGE:", result["message"])
        print("DATA:", result["data"])
