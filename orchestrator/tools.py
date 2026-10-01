from datetime import datetime

from tools.engine import MockToolEngine


class FinAIToolEngine(MockToolEngine):
    """
    Extended mock tool layer.

    All operations use synthetic data and are intended only for
    development/testing of the FinAI hybrid architecture.
    """

    def _simple_success(self, tool, message, data=None):
        return self._result(
            tool,
            True,
            data or {},
            message
        )

    def secure_account(self, account_id):
        if account_id not in self.accounts:
            return self._result(
                "secure_account",
                False,
                message="Account not found."
            )

        return self._simple_success(
            "secure_account",
            "Mock account security procedure completed.",
            {
                "account_id": account_id,
                "security_status": "SECURED"
            }
        )

    def check_account_lock(self, account_id):
        if account_id not in self.accounts:
            return self._result(
                "check_account_lock",
                False,
                message="Account not found."
            )

        return self._simple_success(
            "check_account_lock",
            "Account lock status retrieved.",
            {
                "account_id": account_id,
                "status": "UNLOCKED"
            }
        )

    def reset_password(self, account_id):
        if account_id not in self.accounts:
            return self._result(
                "reset_password",
                False,
                message="Account not found."
            )

        return self._simple_success(
            "reset_password",
            "Mock password reset workflow initiated.",
            {
                "account_id": account_id,
                "status": "RESET_INITIATED"
            }
        )

    def update_profile(self, account_id):
        if account_id not in self.accounts:
            return self._result(
                "update_profile",
                False,
                message="Account not found."
            )

        return self._simple_success(
            "update_profile",
            "Mock profile update workflow initiated.",
            {
                "account_id": account_id,
                "status": "UPDATE_INITIATED"
            }
        )

    def activate_card(self, card_id):
        card = self.cards.get(card_id)

        if not card:
            return self._result(
                "activate_card",
                False,
                message="Card not found."
            )

        card["status"] = "active"

        return self._simple_success(
            "activate_card",
            "Card activated successfully in the mock system.",
            {
                "card_id": card_id,
                "status": "active"
            }
        )

    def check_upi_collect(self, upi_id):
        return self._simple_success(
            "check_upi_collect",
            "UPI collect request status retrieved.",
            {
                "upi_id": upi_id,
                "status": "PENDING"
            }
        )

    def check_upi_id(self, account_id):
        if account_id not in self.accounts:
            return self._result(
                "check_upi_id",
                False,
                message="Account not found."
            )

        return self._simple_success(
            "check_upi_id",
            "UPI ID information retrieved.",
            {
                "account_id": account_id,
                "upi_id": "testuser@mockupi",
                "status": "ACTIVE"
            }
        )

    def check_beneficiary(self, account_id):
        if account_id not in self.accounts:
            return self._result(
                "check_beneficiary",
                False,
                message="Account not found."
            )

        return self._simple_success(
            "check_beneficiary",
            "Beneficiary status retrieved.",
            {
                "account_id": account_id,
                "beneficiary_status": "ACTIVE"
            }
        )

    def check_cash_withdrawal(self, transaction_id="TXN001"):
        return self._simple_success(
            "check_cash_withdrawal",
            "Cash withdrawal status retrieved.",
            {
                "transaction_id": transaction_id,
                "status": "FAILED"
            }
        )

    def check_reversed_transaction(self, transaction_id="TXN001"):
        return self._simple_success(
            "check_reversed_transaction",
            "Transaction reversal status retrieved.",
            {
                "transaction_id": transaction_id,
                "status": "REVERSED"
            }
        )

    def report_duplicate_transaction(self, transaction_id="TXN001"):
        return self._simple_success(
            "report_duplicate_transaction",
            "Duplicate transaction report created in mock system.",
            {
                "transaction_id": transaction_id,
                "case_id": "CASE-DUP-1001",
                "status": "OPEN"
            }
        )

    def report_wrong_amount(self, transaction_id="TXN001"):
        return self._simple_success(
            "report_wrong_amount",
            "Wrong-amount dispute created in mock system.",
            {
                "transaction_id": transaction_id,
                "case_id": "CASE-AMT-1001",
                "status": "OPEN"
            }
        )

    def investigate_unknown_transaction(self, transaction_id="TXN001"):
        return self._simple_success(
            "investigate_unknown_transaction",
            "Unknown transaction investigation created.",
            {
                "transaction_id": transaction_id,
                "case_id": "CASE-UNK-1001",
                "status": "OPEN"
            }
        )

    def create_transaction_dispute(self, transaction_id="TXN001"):
        return self._simple_success(
            "create_transaction_dispute",
            "Transaction dispute created in mock system.",
            {
                "transaction_id": transaction_id,
                "case_id": "CASE-DIS-1001",
                "status": "OPEN"
            }
        )

    def report_fraud(self, account_id):
        if account_id not in self.accounts:
            return self._result(
                "report_fraud",
                False,
                message="Account not found."
            )

        return self._simple_success(
            "report_fraud",
            "Fraud report created in mock system.",
            {
                "account_id": account_id,
                "case_id": "CASE-FRAUD-1001",
                "status": "OPEN"
            }
        )

    def investigate_suspicious_activity(self, account_id):
        if account_id not in self.accounts:
            return self._result(
                "investigate_suspicious_activity",
                False,
                message="Account not found."
            )

        return self._simple_success(
            "investigate_suspicious_activity",
            "Suspicious activity investigation created.",
            {
                "account_id": account_id,
                "case_id": "CASE-SUS-1001",
                "status": "OPEN"
            }
        )

    def check_refund_amount(self, refund_id="REF1001"):
        refund = self.refunds.get(refund_id)

        if not refund:
            return self._result(
                "check_refund_amount",
                False,
                message="Refund not found."
            )

        return self._simple_success(
            "check_refund_amount",
            "Refund amount retrieved.",
            {
                "refund_id": refund_id,
                "amount": refund["amount"],
                "currency": "INR"
            }
        )

    def check_merchant_credit(self, account_id):
        if account_id not in self.accounts:
            return self._result(
                "check_merchant_credit",
                False,
                message="Account not found."
            )

        return self._simple_success(
            "check_merchant_credit",
            "Merchant credit status retrieved.",
            {
                "account_id": account_id,
                "merchant_credit_status": "PENDING"
            }
        )

    def update_kyc(self, account_id):
        if account_id not in self.accounts:
            return self._result(
                "update_kyc",
                False,
                message="Account not found."
            )

        return self._simple_success(
            "update_kyc",
            "Mock KYC update workflow initiated.",
            {
                "account_id": account_id,
                "status": "UPDATE_INITIATED"
            }
        )

    def check_loan_status(self, account_id):
        if account_id not in self.accounts:
            return self._result(
                "check_loan_status",
                False,
                message="Account not found."
            )

        return self._simple_success(
            "check_loan_status",
            "Loan status retrieved.",
            {
                "account_id": account_id,
                "loan_status": "UNDER_REVIEW"
            }
        )

    def create_support_ticket(self, account_id=None):
        return self._simple_success(
            "create_support_ticket",
            "Support ticket created in mock system.",
            {
                "case_id": "CASE-SUPPORT-1001",
                "status": "OPEN",
                "account_id": account_id
            }
        )

    def cancel_payment(self, transaction_id="TXN001"):
        return self._simple_success(
            "cancel_payment",
            "Payment cancellation request created in mock system.",
            {
                "transaction_id": transaction_id,
                "status": "CANCELLATION_REQUESTED"
            }
        )
