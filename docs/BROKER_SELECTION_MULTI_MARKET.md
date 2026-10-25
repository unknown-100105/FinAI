# Broker selection for FinAI's multi-market rollout

**Research date:** 2026-10-25. Verify provider terms, API entitlements, and local rules again before implementation or activation. This is a provider shortlist, not a claim that any account is approved or that every market is available to every customer.

## Recommendation

Use a provider-neutral adapter contract and connect one broker at a time. There is no single broker API that should be assumed to cover every market, instrument, country, and product. Keep the core agent/risk system separate from each provider's authentication, instrument identifiers, order types, rate limits, and status vocabulary.

### Initial candidates

| Priority | Provider | Why it is a candidate | Important constraints |
|---|---|---|---|
| Global multi-market candidate | Interactive Brokers (IBKR) | Official API documentation describes Web API (REST/HTTP + WebSocket), TWS API, account access and trading capabilities. It is a reasonable first candidate to investigate for US and international market breadth. | Product access, exchanges, derivatives permissions, market-data subscriptions, regional account eligibility, authentication and API entitlements must be verified for the actual account. Do not assume universal access. |
| Indian-market candidate | Upstox API | Official documentation covers account/funds, orders, portfolio, rate limits, kill switch/static IP controls, and a sandbox for place/modify/cancel order APIs. | Sandbox coverage is limited to documented operations; verify each instrument/segment and current API policy. |
| Indian-market candidate | Zerodha Kite Connect | Official docs cover order execution, portfolio and WebSocket market data. | No broker-provided sandbox according to its FAQ; use internal simulation and paper-forward tests. Paid plan is required for live WebSocket and historical candle data. |
| Additional Indian candidate | Angel One SmartAPI | Official docs describe order APIs and NSE/BSE/NFO/BFO/MCX-related instrument/market-data fields. | From 2026-04-01, order API execution requires a registered static IP per provider notice. Verify account/product permissions and exact current terms. |

## Official provider references

- Interactive Brokers API documentation: https://www.interactivebrokers.com/docs/
- Upstox developer API and sandbox documentation: https://upstox.com/developer/api-documentation
- Zerodha Kite Connect API documentation: https://www.kite.trade/docs/connect/v3/
- Zerodha API plans and entitlements: https://www.zerodha.com/products/api/
- Angel One SmartAPI documentation: https://smartapi.angelone.in/docs
- Angel One static-IP change notice: https://www.angelone.in/news/market-updates/what-s-changing-in-angel-one-s-smartapi-access-from-april-1-2026

## Proposed rollout

1. **Shared core:** agent findings, provenance, strategy candidate schema, deterministic risk checks, order state machine, audit events and paper ledger.
2. **IBKR evaluation adapter:** first evaluate account eligibility and required market-data entitlements for cross-border equities/options/futures. Start with read-only account/market-data calls; do not submit live orders.
3. **Upstox sandbox adapter:** evaluate the Indian order lifecycle in its sandbox, with automated tests for duplicate requests, timeouts, rejection, partial fills where representable, and reconciliation.
4. **Zerodha or Angel One as a separate adapter:** add only if the user's account/market needs justify it. Never reuse provider-specific tokens, symbols or order assumptions across adapters.
5. **Crypto:** keep separate exchange adapters and separate spot vs derivatives risk policies. Do not claim support until a specific venue, jurisdiction, API and product are chosen and verified.

## Required adapter contract

Each adapter should explicitly report capabilities rather than pretending to support all markets:

- provider_id, supported venues, asset classes, product types and order types.
- Whether sandbox/paper endpoint is supported and which operations it simulates.
- Account and margin reads, instrument metadata, order submit/modify/cancel/query, fills, positions and balance reconciliation.
- Market-data entitlement and timestamp semantics.
- Authentication/session expiry, rate limits, static-IP requirements, idempotency support and known limitations.

An unsupported operation must return a typed UnsupportedCapability result before any order submission. Provider errors and timeouts must not cause blind retries. If submission outcome is uncertain, mark it UNKNOWN, query the broker, and reconcile before considering another submission.

## Safety and regulatory gate

- Live execution remains disabled by default and in the current code.
- No secrets in browser code, LLM prompts, logs, or Git.
- Use server-side secrets management, identity/account ownership checks, audit trails and least privilege.
- Apply instrument-aware quantity, notional, margin, leverage, spread, quote-age, portfolio exposure and daily loss controls.
- Require kill-switch testing and broker-state reconciliation.
- Verify the user's account permissions, broker terms and applicable jurisdictional requirements, including current retail algorithmic trading rules in India where relevant.
- This document does not establish that the strategy is profitable, legal for a particular deployment, or production ready.
