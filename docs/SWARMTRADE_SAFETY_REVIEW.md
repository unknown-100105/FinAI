# SwarmTrade Safety Review

**Review scope:** `feature/finai-runtime-trading-integration` at commit `f149514`  
**Review type:** Static code review of the deterministic planner, candidate risk gate, and API boundaries.  
**Conclusion:** Suitable for continued simulation and test development only. Not approved for live trading or production execution.

## Verified behavior

- The deterministic planner caps logical agent votes at 500 and explicitly reports that these are logical votes, not concurrent agents.
- The planner rejects invalid directional consensus, missing or incorrectly ordered protective levels, reached daily-loss limits, and risk sizing below one configured unit.
- New-trade risk is capped at 1% and aggregate open-position risk input at 3%; daily-loss, margin, leverage, estimated costs, and reward-to-risk checks are applied in the planner.
- Options require explicit loss assumptions; naked short calls are blocked. Futures and forex require additional instrument-specific sizing metadata.
- The candidate gate checks notional, portfolio/daily-loss inputs, leverage, spread, quote freshness, evidence presence/conflicts, and derivative metadata.
- Live execution is hard-disabled by `live_execution_enabled()`, including when the environment variable is set to `true`.
- API responses state simulation-only semantics and do not claim an order was submitted or filled.

## Important limitations and release blockers

1. **No broker or exchange adapter is implemented.** The current endpoints do not submit orders, fetch authoritative positions, or reconcile fills.
2. **Risk context is caller-supplied and stateless.** Values such as portfolio exposure, daily loss after trade, quote age, evidence count, and contract metadata flags are assertions in the request, not independently sourced facts. A future execution service must derive them from trusted sources and persisted account state.
3. **No stateful paper account is connected to the planner endpoint.** An approval is a sizing proposal, not a simulated fill, portfolio update, or realized performance result.
4. **Market and instrument metadata are not independently verified.** Contract multipliers, tick/pip values, margin, fees, slippage, and unit steps must be sourced from venue-specific metadata and validated for the actual instrument.
5. **No operational kill switch, idempotent order-submission workflow, broker timeout recovery, or end-to-end reconciliation is delivered.** The order-state enum and transition checks are primitives, not a complete execution state machine.
6. **Logical-agent consensus is deterministic feature weighting.** It is not evidence that 500 independent AI agents ran, nor that the signals are profitable or statistically validated.

## Required gates before any live-execution work

- Implement a trusted account/position state service and enforce portfolio, daily-loss, exposure, and concentration limits against that state.
- Integrate authoritative quotes and instrument metadata with freshness, provenance, and venue/session validation.
- Build a persistent paper-trading ledger with deterministic replay, fees/slippage, partial fills, rejects, cancels, and reconciliation.
- Add idempotency keys, broker timeout handling, unknown-order reconciliation, duplicate-order prevention, audit logs, and a kill switch.
- Add broker-adapter contract tests and sandbox/integration tests; verify all supported asset classes and market-session edge cases.
- Obtain an independent safety review and explicit operator approval before even considering a separately gated live-execution implementation.

## Current verification record

The repository owner reported a local full-suite run of **787 passed, 0 failed** in 20.00 seconds at `f149514`. This document does not independently rerun that suite. The reported run included four non-fatal deprecation/runtime warnings. Passing tests do not establish profitability, live-broker readiness, or production safety.
