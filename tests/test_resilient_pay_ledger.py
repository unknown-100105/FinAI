import json
from pathlib import Path
import subprocess
import sys

import pytest

from resilient_pay.ledger import (
    IdempotencyConflict,
    InvalidPaymentTransition,
    LocalSimulationAdapter,
    PaymentLedger,
    PaymentService,
    PaymentState,
    SettlementOutcomeUnknown,
)


def prepared_payment(ledger, key="once"):
    return ledger.prepare_payment(
        idempotency_key=key, payer_ref="payer-1", payee_ref="payee-2",
        amount_minor=1250, currency="INR",
    )[0]


def test_prepare_is_idempotent_and_hashes_request():
    with PaymentLedger() as ledger:
        first, created = ledger.prepare_payment(
            idempotency_key="pay-key", payer_ref="P1", payee_ref="P2",
            amount_minor=250, currency="INR",
        )
        second, created_again = ledger.prepare_payment(
            idempotency_key="pay-key", payer_ref="P1", payee_ref="P2",
            amount_minor=250, currency="inr",
        )
        assert created is True
        assert created_again is False
        assert first.payment_id == second.payment_id
        assert first.state == PaymentState.PREPARED
        assert ledger.verify_journal() == (True, None)


def test_reusing_idempotency_key_for_different_instruction_is_rejected():
    with PaymentLedger() as ledger:
        prepared_payment(ledger, key="same")
        with pytest.raises(IdempotencyConflict):
            ledger.prepare_payment(
                idempotency_key="same", payer_ref="P1", payee_ref="P2",
                amount_minor=1251, currency="INR",
            )


def test_submission_requires_authorization_and_confirmation():
    with PaymentLedger() as ledger:
        intent = prepared_payment(ledger)
        service = PaymentService(ledger)
        with pytest.raises(PermissionError):
            service.submit_prepared(
                intent.payment_id, adapter=LocalSimulationAdapter(),
                authenticated=False, confirmed=True,
            )
        with pytest.raises(PermissionError):
            service.submit_prepared(
                intent.payment_id, adapter=LocalSimulationAdapter(),
                authenticated=True, confirmed=False,
            )
        assert ledger.get_payment(intent.payment_id).state == PaymentState.PREPARED


def test_simulated_submission_and_settlement_are_idempotent():
    with PaymentLedger() as ledger:
        intent = prepared_payment(ledger)
        service = PaymentService(ledger)
        submitted = service.submit_prepared(
            intent.payment_id, adapter=LocalSimulationAdapter(),
            authenticated=True, confirmed=True,
        )
        assert submitted.state == PaymentState.SUBMITTED
        assert submitted.settlement_mode == "sandbox"
        settled = ledger.mark_settled(
            intent.payment_id, external_reference=submitted.external_reference
        )
        assert settled.state == PaymentState.SETTLED
        assert ledger.mark_settled(
            intent.payment_id, external_reference=submitted.external_reference
        ).state == PaymentState.SETTLED
        assert [e["event_type"] for e in ledger.journal_events(intent.payment_id)] == [
            "PAYMENT_PREPARED", "PAYMENT_SUBMITTED", "PAYMENT_SETTLED"
        ]
        assert ledger.verify_journal() == (True, None)


def test_settlement_reference_must_match_submission():
    with PaymentLedger() as ledger:
        intent = prepared_payment(ledger)
        submitted = ledger.mark_submitted(
            intent.payment_id, external_reference="external-1", sandbox=False
        )
        with pytest.raises(InvalidPaymentTransition):
            ledger.mark_settled(intent.payment_id, external_reference="wrong-reference")
        assert submitted.state == PaymentState.SUBMITTED


def test_adapter_error_requires_reconciliation_and_blocks_blind_retry():
    class BrokenAdapter:
        def submit(self, intent):
            raise TimeoutError("destination may have accepted the payment")

    with PaymentLedger() as ledger:
        intent = prepared_payment(ledger)
        service = PaymentService(ledger)
        with pytest.raises(SettlementOutcomeUnknown):
            service.submit_prepared(
                intent.payment_id, adapter=BrokenAdapter(),
                authenticated=True, confirmed=True,
            )
        assert ledger.get_payment(intent.payment_id).state == PaymentState.RECONCILIATION_REQUIRED
        with pytest.raises(InvalidPaymentTransition):
            service.submit_prepared(
                intent.payment_id, adapter=LocalSimulationAdapter(),
                authenticated=True, confirmed=True,
            )


def test_invalid_amount_and_self_payment_are_rejected():
    with PaymentLedger() as ledger:
        with pytest.raises(ValueError):
            ledger.prepare_payment(
                idempotency_key="zero", payer_ref="P1", payee_ref="P2", amount_minor=0
            )
        with pytest.raises(ValueError):
            ledger.prepare_payment(
                idempotency_key="self", payer_ref="P1", payee_ref="P1", amount_minor=100
            )


def test_journal_detects_modified_payload():
    with PaymentLedger() as ledger:
        intent = prepared_payment(ledger)
        ledger._conn.execute(
            "UPDATE payment_journal SET payload_json=? WHERE payment_id=?",
            ('{"tampered":true}', intent.payment_id),
        )
        valid, failing_sequence = ledger.verify_journal()
        assert valid is False
        assert failing_sequence == 1


def test_demo_script_is_a_no_network_sandbox_flow():
    root = Path(__file__).resolve().parents[1]
    result = subprocess.run(
        [sys.executable, str(root / "scripts" / "demo_resilient_pay.py")],
        cwd=root, capture_output=True, text=True, timeout=15, check=True,
    )
    payload = json.loads(result.stdout)
    assert payload["demo_only"] is True
    assert payload["real_funds_moved"] is False
    assert payload["journal_integrity"] == {"valid": True, "failing_sequence": None}
    assert payload["payment"]["state"] == "SETTLED"
    assert payload["payment"]["settlement_mode"] == "sandbox"
