# SwarmTrade safety API: local verification guide

This integration exposes the deterministic risk gate as an authenticated FinAI API route. It is **not** a broker adapter or an execution engine. Every passing decision means simulation approval only.

## Routes

- `GET /api/v1/swarmtrade/safety/status` — capabilities and safety mode.
- `POST /api/v1/swarmtrade/safety/evaluate` — evaluate a candidate against quote freshness, spread, evidence, notional, portfolio, daily-loss, leverage, and derivative policy controls.
- Existing `POST /api/v1/swarmtrade/plan` — deterministic logical-agent planning.
- Existing `/api/v1/swarmtrade/paper/*` — SQLite paper ledger.
- Existing `/api/v1/swarmtrade/agent-mesh/*` — provenance-aware shared research evidence.

The safety API is included in `app.main:app` and inherits the app's API authentication middleware and CORS policy. Do not expose it publicly without configuring production authentication and TLS.

## Example request

```json
{
  "instrument_id": "DEMO-EQUITY",
  "asset_class": "equity",
  "side": "buy",
  "quantity": 2,
  "reference_price": 100,
  "multiplier": 1,
  "spread_bps": 5,
  "quote_age_seconds": 1,
  "portfolio_notional_after": 200,
  "daily_loss_after": 0,
  "leverage_after": 1,
  "evidence_count": 1,
  "limits": {
    "max_order_notional": 5000,
    "max_portfolio_notional": 20000,
    "max_daily_loss": 500,
    "max_leverage": 1,
    "max_spread_bps": 25,
    "max_quote_age_seconds": 5,
    "allow_derivatives": false
  }
}
```

Submit it to `POST /api/v1/swarmtrade/safety/evaluate` after starting the API locally. A passing response should say `approved_for_simulation`, with `order_submitted: false` and `fill_claimed: false`. Missing or stale quote information and missing evidence fail closed. Derivatives are disabled unless a caller explicitly enables them and supplies validated contract metadata plus bounded maximum loss.

## Local verification (Windows PowerShell)

```powershell
python -m pytest -q tests/test_multi_agent_trading_safety.py tests/test_swarmtrade_safety_api.py
python -m pytest -q
uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Then inspect `http://127.0.0.1:8000/docs`. These commands are instructions, not a claim that tests were executed during remote repository editing.

## Important limits

- No live order submission, broker credentials, or broker adapter are enabled.
- Evidence sharing across the existing agent-mesh API uses its own persistent store; the lightweight `SharedEvidenceStore` in `swarmtrade/multi_agent.py` is in-memory and is not a substitute for that persistence.
- A large logical-agent count does not mean that many independent LLM agents or parallel workers are running.
- This API does not provide real-time quote ingestion itself. The caller must provide quote age, spread, portfolio state, and evidence count from trusted services.
- No performance or profitability claim is implied. Before any future live-trading work, add provider-specific sandbox adapters, durable order intents and idempotency, broker reconciliation, operational kill switches, permissions separation, and independent security/risk review.
