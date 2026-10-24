# Persistent SwarmTrade paper ledger

This is a local, opt-in paper ledger. It does not connect to an exchange, submit live orders, or assert that a real-world fill occurred.

## Enable it for trusted local verification

Set these values in `.env`:

```dotenv
FINAI_ENABLE_SWARMTRADE_PAPER_LEDGER=1
FINAI_SWARMTRADE_PAPER_DB=data/swarmtrade/paper_ledger.sqlite3
```

Do not expose the endpoint publicly without appropriate authentication and access controls. The ledger is disabled unless the enable flag is explicitly set.

## Routes

- `GET /api/v1/swarmtrade/paper/status`
- `POST /api/v1/swarmtrade/paper/accounts` — create a starting-capital account.
- `GET /api/v1/swarmtrade/paper/accounts/{account_id}` — inspect equity excluding unrealized PnL, realized PnL, open risk and positions.
- `POST /api/v1/swarmtrade/paper/accounts/{account_id}/positions` — requires an approved SwarmTrade plan and `acknowledge_simulation_only: true`.
- `POST /api/v1/swarmtrade/paper/accounts/{account_id}/positions/{position_id}/close` — record a manual simulated exit at a supplied price.

Each mutation requires a unique `idempotency_key`. Repeating the exact same key and payload replays the prior response; reusing the key for a different payload is rejected. SQLite transactions serialize writes and guard the aggregate open-position risk cap against concurrent opens.

## Financial-model boundaries

The ledger is for paper simulation. It records assumed entry/exit prices and estimated fees/slippage; it does not receive broker fills. Equity/crypto and option-premium PnL use price change × multiplier × quantity. Futures PnL uses tick-size/tick-value metadata. Forex PnL uses pip-size and account-currency pip value. Verify these fields, contract sizes, currency conversion, fees and margin at the venue. Unrealized PnL is not included in account equity or daily loss, and no automatic stop/target trigger is assumed—the caller explicitly closes a paper position.

## Tests

```powershell
python -m pytest -q tests/test_swarmtrade_paper_ledger.py
```
