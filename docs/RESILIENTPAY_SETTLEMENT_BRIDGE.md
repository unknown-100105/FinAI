# ResilientPay settlement integration seam

**Status:** Local-first payment-intent journal and adapter contract only. This is not a bank integration, payment processor, Hyperledger Fabric gateway, or production wallet.

## Included

- A SQLite-backed journal with unique idempotency keys, request-hash conflict detection, explicit states, atomic transitions, and a SHA-256 hash-chained event log.
- A PaymentService requiring authenticated context and explicit confirmation before calling an injected settlement adapter.
- Ambiguous adapter exceptions move the intent to RECONCILIATION_REQUIRED instead of triggering blind retries.
- LocalSimulationAdapter produces deterministic SIM references and explicitly marks them as sandbox.

## Not implemented

No funds are held or moved. The module does not calculate balances, guarantee offline double-spend prevention across disconnected devices, call a bank, invoke a DLT network, or provide legal settlement finality. A Hyperledger Fabric adapter still requires the selected Gateway SDK, channel/chaincode contract, identity provisioning, endorsement policy, replay/idempotency behavior, reconciliation contract, and local test-network validation. Do not describe the simulator as a completed DLT integration.

## Tests

Run from the repository root:

    python -m pytest -q tests/test_resilient_pay_ledger.py

Use integer minor units such as INR paise. Production adapters must resolve account references against an authenticated account directory; do not treat arbitrary client-provided payer/payee strings as authorization.
