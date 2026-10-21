"""Run a local-only ResilientPay ledger demonstration; no real money is moved."""
from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from resilient_pay.ledger import LocalSimulationAdapter, PaymentLedger, PaymentService


def main() -> int:
    with PaymentLedger() as ledger:
        service = PaymentService(ledger)
        intent, created = service.prepare(
            idempotency_key="demo-resilientpay-local-001",
            payer_ref="DEMO-PAYER",
            payee_ref="DEMO-PAYEE",
            amount_minor=1250,
            currency="INR",
        )
        if intent.state.value == "PREPARED":
            submitted = service.submit_prepared(
                intent.payment_id,
                adapter=LocalSimulationAdapter(),
                authenticated=True,
                confirmed=True,
            )
        else:
            submitted = intent
        settled = ledger.mark_settled(
            submitted.payment_id,
            external_reference=submitted.external_reference or "",
        )
        valid, failing_sequence = ledger.verify_journal()
        print(json.dumps({
            "demo_only": True,
            "real_funds_moved": False,
            "new_intent_created": created,
            "payment": settled.to_dict(),
            "journal_integrity": {"valid": valid, "failing_sequence": failing_sequence},
            "events": ledger.journal_events(settled.payment_id),
        }, indent=2))
        return 0 if valid else 1


if __name__ == "__main__":
    raise SystemExit(main())
