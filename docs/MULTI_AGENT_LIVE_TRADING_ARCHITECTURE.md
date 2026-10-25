# FinAI Multi-Agent, Multi-Asset Trading Architecture

## Status

**Design specification only.** This document does not enable live trading and is not evidence that broker execution, profitability, or production readiness has been verified. The existing SwarmTrade planner and paper ledger are simulation-oriented. Live execution must remain disabled until the acceptance gates below are met.

## Objective

Extend FinAI toward a multi-agent research and trading platform that can evaluate multiple supported asset classes, share sourced evidence, propose trades, manage risk deterministically, and eventually route approved orders through broker-specific APIs.

No architecture can guarantee profits. A large number of agents is not itself a performance advantage; agents must earn continued use through measured incremental value on out-of-sample data after fees, spread, slippage, funding, borrow costs, and realistic execution assumptions.

## Hierarchical agent design

Use a configurable pool of specialist workers (potentially hundreds for research workloads), coordinated by a small number of explicit supervisory roles. Do not create 300 independent order submitters.

### Tier 1 — Data and evidence workers

- Market-data quality, timestamps, corporate actions, symbol/contract mapping, trading calendar, and stale-feed detection.
- News and event extraction with source attribution and publication timestamps.
- Fundamental, macroeconomic, sector, technical, order-book/liquidity, and volatility research.
- Derivatives-specific workers for contract expiry, multiplier, lot size, Greeks, implied volatility, open interest, margin estimates, and payoff scenarios.
- Cross-provider discrepancy detection and missing-data reporting.

### Tier 2 — Strategy researchers

- Trend/momentum, mean-reversion, statistical-arbitrage, event-driven, factor, and volatility strategies.
- Options structures and futures basis/carry strategies only when required market data and contract metadata are available.
- Causal-risk and scenario stress testing, with causal claims clearly distinguished from correlations.
- Independent bear-case / adversarial reviewer.
- Backtest integrity reviewer that checks look-ahead bias, survivorship bias, leakage, and unrealistic fills.

### Tier 3 — Supervisors

- Market supervisor: consolidates evidence by asset class and time horizon.
- Portfolio supervisor: checks correlations, concentration, leverage, margin, currency, and cross-market exposure.
- Strategy allocator: ranks candidates using validated metrics and uncertainty, not raw agent votes.
- Risk supervisor: can veto any proposal; cannot be overridden by LLM agents.
- Execution supervisor: converts an approved intent into a broker-specific order request and tracks the order lifecycle.
- Audit supervisor: records data lineage, model/strategy version, proposal, risk decision, approval, broker response, fills, fees, and reconciliation.

## Shared information contract

Every agent output should be structured and versioned, including:

- `run_id`, `agent_id`, role, agent/model version, and timestamp.
- Instrument identifier, venue, asset class, contract expiry, currency, and data timeframe where applicable.
- Claims and supporting source IDs, source timestamps, data freshness, and confidence/uncertainty.
- Hypothesis, invalidation conditions, expected holding horizon, and scenario risks.
- Proposed action (if any), expected entry/exit logic, maximum loss estimate, and assumptions.
- Conflicts with other agents, missing evidence, and abstention reason.

Agents must not treat another agent's output as verified market data. Shared findings need provenance, freshness checks, and conflict resolution. Untrusted news or tool output must never be treated as executable instructions.

## Implemented research API surface

The current research-only agent evidence service is exposed at:
- `GET /api/v1/swarmtrade/agent-mesh/status`
- `POST /api/v1/swarmtrade/agent-mesh/runs`
- `POST /api/v1/swarmtrade/agent-mesh/runs/{run_id}/evidence`
- `GET /api/v1/swarmtrade/agent-mesh/runs/{run_id}/summary`

The SQLite evidence store retains agent role/version, claim, source IDs, source/observation timestamps, confidence, stance, invalidation conditions, and missing-data flags. It rejects unknown roles, missing provenance, invalid confidence, timezone-free/far-future timestamps, duplicate evidence IDs, unknown runs, and more than 300 evidence records per run. Summaries expose stale-evidence flags and stance counts, but explicitly do not claim calibrated probabilities or grant execution authority.

This is an initial shared-evidence substrate, not yet a distributed agent runtime: it does not spawn 300 independent workers, call external LLMs, subscribe to real-time feeds, calculate a validated trading edge, or route broker orders. Those components remain separate work and require runtime tests before they can be considered operational.

## Candidate-to-order state machine

`OBSERVE -> RESEARCH -> CANDIDATE -> RISK_CHECK -> APPROVAL_OR_POLICY_GATE -> SUBMITTED -> ACKNOWLEDGED -> PARTIALLY_FILLED/FILLED/REJECTED/CANCELLED -> RECONCILED`

- Research agents only produce evidence and proposals.
- The deterministic risk engine is the sole authority for limit checks.
- Live order submission is a separate capability from strategy generation.
- Unknown order status must trigger broker reconciliation before a retry; never blindly resubmit.
- Use idempotency/client-order IDs where supported and persist every state transition.
- Positions and balances must be reconciled to broker records, not inferred from model messages.
- A global kill switch must stop new orders. Cancellation of working orders must be an explicit, separately tested behavior.

## Deterministic risk controls

At minimum, configure and test:

- Per-order notional and quantity caps.
- Per-instrument, per-strategy, and portfolio exposure caps.
- Daily realized plus mark-to-market loss limits and a drawdown stop.
- Maximum leverage, margin utilization, concentration, and correlated exposure.
- Options-specific contract/expiry/Greek and maximum-loss checks; reject instruments whose payoff or margin cannot be bounded reliably.
- Price collars, spread/liquidity thresholds, stale-data rejection, market-hours checks, and duplicate-order prevention.
- Fees, taxes, spread, slippage, borrow/funding costs, and currency conversion in estimates.
- Manual emergency stop and fail-closed behavior when data, broker, risk service, or persistence is unavailable.

Limits should be configured explicitly for each account, venue, and asset class. Never assume a risk limit that has not been set and validated.

## Broker and market adapters

Use a provider-neutral interface with separate adapters for each broker and asset class. A broker may not support every market, instrument, order type, or API operation. Verify permissions, product eligibility, data entitlements, rate limits, authentication, sandbox support, and regulatory requirements before enabling an adapter.

Adapter responsibilities:

1. Read account permissions, balances, positions, margin and open orders.
2. Validate venue/instrument/contract metadata and supported order types.
3. Submit, modify, cancel, and query orders where supported.
4. Normalize broker-specific states into a common internal state model.
5. Reconcile fills, partial fills, fees, positions, and balances.
6. Enforce timeouts and rate limits without duplicate order submission.
7. Keep secrets server-side; never expose broker credentials to the browser, LLM prompts, logs, or repository.

## Live-mode activation gates

Live trading must be **off by default**. A configuration flag alone is not sufficient authorization.

Before any real-money order is allowed, require all of the following:

1. A supported broker adapter for the selected account, venue, and instrument.
2. Secure server-side credentials and documented account permissions.
3. Successful unit, integration, fault-injection, idempotency, and reconciliation tests.
4. Broker sandbox or simulated execution tests where available.
5. Walk-forward and untouched out-of-sample evaluation with realistic costs and baselines.
6. Paper-forward results across different regimes and a documented acceptance review.
7. Account-specific limits, an operator-visible kill switch, alerts, and immutable audit records.
8. Explicit operator activation and a clear live-mode indicator in the UI.
9. Legal, tax, broker terms, and applicable regulatory review for the intended jurisdiction and product.

Until all gates are signed off, the system must remain in research/paper mode and must not send live orders.

## Evaluation for claimed profitability

Do not accept profitability claims from agent consensus or in-sample backtests. Record net returns after costs, volatility, maximum drawdown, tail loss, turnover, exposure, capacity, rejected/partial orders, and operational failures. Use chronological splits, walk-forward validation, untouched holdout periods, multiple market regimes, and simple baselines. Correct for repeated strategy search and selection bias. Retire or disable agents that do not add reproducible out-of-sample value.


## Broker selection for a multi-market rollout

No single provider should be assumed to cover every exchange, instrument, and account jurisdiction. Start with provider adapters that are explicitly enabled per account and market.

| Rollout need | Candidate | Why it is worth evaluating | Caveat |
|---|---|---|---|
| Global equities, options, futures, FX | Interactive Brokers (IBKR) | Its official API pages describe stocks, options, futures, currencies, bonds and access to multiple global markets. | Account eligibility, country restrictions, product permissions, market-data subscriptions, API product onboarding and venue-specific rules still need verification. |
| India-first development and sandbox validation | Upstox API | Official developer docs expose order lifecycle APIs, account/portfolio endpoints and a sandbox for place/modify/cancel order testing. | Treat it as an India adapter; do not assume it routes orders to foreign exchanges or supports every product/account type. |
| India alternative | Zerodha Kite Connect | Official docs describe order APIs, portfolio management and WebSocket market data for supported products. | Its FAQ says it does not provide a sandbox; use paper-mode adapter tests and carefully scoped live-account validation only after approval. |

Official provider references:
- IBKR API overview: https://www.interactivebrokers.com/en/trading/ib-api.php
- Upstox developer API and sandbox: https://upstox.com/developer/api-documentation
- Kite Connect API: https://kite.trade/docs/connect/v3/
- Kite Connect product/plan information: https://www.zerodha.com/products/api/

These are candidates, not endorsements or guarantees of account eligibility. Re-check the provider's current official terms and supported contract/venue metadata before implementation. Do not share broker passwords or API secrets with FinAI prompts or source control.

## India-specific automated-trading compliance gate

Before routing automated orders for Indian exchange products, review the current SEBI retail algorithmic-trading circular and the relevant exchange implementation standards with the chosen broker. The applicable framework may impose broker onboarding, API authentication, static-IP, tagging/registration, order-rate, logging, or other requirements depending on the trading arrangement and strategy. Do not infer that an API key alone authorizes a live autonomous strategy.

References:
- SEBI circular, “Safer participation of retail investors in Algorithmic trading” (4 February 2025): https://www.sebi.gov.in/legal/circulars/feb-2025/safer-participation-of-retail-investors-in-algorithmic-trading_91614.html
- NSE implementation standards: https://nsearchives.nseindia.com/content/circulars/INVG67858.pdf

Compliance is a launch gate, not a runtime warning to ignore. The platform must refuse live activation until the broker confirms the specific account, instruments, API configuration, and algorithmic-trading arrangement are eligible.

## Incremental implementation plan

1. Inventory the existing SwarmTrade planner, API schemas, paper ledger, risk checks, market-data adapters, and frontend.
2. Add the typed agent evidence contract, shared run store, provenance and conflict handling.
3. Implement a small end-to-end hierarchy first (data quality, strategy researcher, adversarial reviewer, portfolio/risk supervisor) and benchmark it.
4. Add specialist workers only when an evaluation demonstrates incremental value; scale workers asynchronously with budgets and timeouts.
5. Build provider-neutral broker interfaces and a first sandbox-capable adapter for the chosen brokerage account.
6. Add contract-aware futures/options risk models and market-specific instrument validation.
7. Complete paper-forward, fault-injection, and reconciliation testing.
8. Conduct the activation review before enabling any live execution path.

## Current limitations

- This design does not claim that 300 agents already exist.
- This design does not implement or enable live broker execution.
- No broker has been selected or account entitlements verified.
- No runtime tests, backtests, sandbox orders, or profitability evaluation are implied by this document.
- CI is outside the current remediation scope and should not be changed as part of this work.
