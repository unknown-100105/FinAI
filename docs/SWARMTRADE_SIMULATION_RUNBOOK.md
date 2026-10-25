# SwarmTrade Simulation Operations Runbook

This runbook is for local development and paper-ledger evaluation only. SwarmTrade in this branch has **no live broker adapter**. Do not connect it to real-money execution.

## 1. Confirm branch and baseline

From the dedicated feature worktree:

~~~powershell
git status
git fetch origin
git pull --ff-only
python -m pytest -q
~~~

A previous local run at commit f149514 reported 787 passed in 20 seconds. Re-run the suite after pulling any new commits; that earlier result does not verify later changes.

## 2. Start the API

Activate the project virtual environment first. For example, if the shared environment is at C:\Users\roghe\FinAI\.venv:

~~~powershell
& "C:\Users\roghe\FinAI\.venv\Scripts\Activate.ps1"
uvicorn app.main:app --host 127.0.0.1 --port 8000
~~~

Bind to loopback for local development. Do not expose this experimental API directly to the public internet. Production API authentication, TLS, network policy, secrets handling, monitoring, and access control require separate deployment review.

## 3. Check safety status

In a second PowerShell window:

~~~powershell
Invoke-RestMethod http://127.0.0.1:8000/api/v1/swarmtrade/status
Invoke-RestMethod http://127.0.0.1:8000/api/v1/swarmtrade/safety/status
Invoke-RestMethod http://127.0.0.1:8000/api/v1/swarmtrade/paper/status
~~~

Expected safety properties:
- SwarmTrade planning is deterministic simulation only.
- Safety gate reports broker_connected: false and order_submission_supported: false.
- Paper ledger is disabled unless explicitly enabled.
- No response should claim a live order or live fill.

If status differs from these expectations, stop and investigate before continuing.

## 4. Enable a local paper ledger explicitly

Use a dedicated local database path, not a shared production database:

~~~powershell
$env:FINAI_ENABLE_SWARMTRADE_PAPER_LEDGER = "1"
$env:FINAI_SWARMTRADE_PAPER_DB = "$PWD\data\swarmtrade\paper_ledger.local.sqlite3"
~~~

Restart the local API after setting the variables. The ledger persists simulated accounts and positions in SQLite. Treat the file as financial test data: keep it out of version control, backups shared with others, and public artifacts.

Create an account using the documented API schema:

~~~powershell
$account = Invoke-RestMethod -Method Post -Uri "http://127.0.0.1:8000/api/v1/swarmtrade/paper/accounts" -ContentType "application/json" -Body '{"label":"Local paper account","currency":"INR","initial_capital":100000}'
$account
~~~

Save the returned account_id. The account currency must match the plan's declared quote_currency; the API does not perform currency conversion.

## 5. Paper-position workflow

The supported workflow is:

1. Prepare a plan with realistic, reviewed instrument metadata, price levels, fees, slippage, and risk settings.
2. Submit it to POST /api/v1/swarmtrade/paper/accounts/{account_id}/positions with a unique idempotency_key, the matching quote_currency, acknowledge_simulation_only: true, and a nested plan.
3. Check the account and open positions using GET /api/v1/swarmtrade/paper/accounts/{account_id} and GET /api/v1/swarmtrade/paper/accounts/{account_id}/positions?status=open.
4. Close a simulated position with POST /api/v1/swarmtrade/paper/accounts/{account_id}/positions/{position_id}/close, a new idempotency key, a finite positive exit_price, and an appropriate close reason.
5. Review closed-position history and account realized P&L. The supplied exit price is a simulation input, not an exchange-verified quote or fill.

Use a new idempotency key for every distinct operation. A retry must reuse the original key and identical payload. Never interpret a paper-ledger response as a broker acknowledgement or execution.

## 6. Required validation before sign-off

- [ ] Run the full test suite on the exact commit being evaluated.
- [ ] Run the SwarmTrade safety benchmark and retain the full report.
- [ ] Test idempotency with identical and conflicting payloads.
- [ ] Test account currency mismatch, disabled feature flag, missing stops/targets, daily-loss cutoffs, and aggregate open-risk limits.
- [ ] Test close/replay behavior, invalid exit values, and stop/target trigger validation.
- [ ] Confirm the SQLite database path is ignored by Git and is not uploaded.
- [ ] Confirm live execution remains disabled even if FINAI_LIVE_TRADING_ENABLED=true.
- [ ] Review the risk and P&L formulas for each asset class against venue-specific contract specifications.

## 7. Explicit non-goals / live-execution blockers

This workflow does not provide authoritative real-time quotes, venue-verified instrument metadata, live order submission, real fill reconciliation, a broker sandbox integration, or an operational kill switch. The agent mesh records research evidence; it does not turn the logical-agent planner into 500 independently running autonomous agents. No profitability claim is supported by the deterministic safety benchmark.

**Release decision:** local simulation and paper-ledger testing only. Live trading is not approved by this repository state. A live adapter must be a separately reviewed implementation with trusted account state, idempotent execution, timeout/unknown-order reconciliation, audited controls, and independent safety approval.
