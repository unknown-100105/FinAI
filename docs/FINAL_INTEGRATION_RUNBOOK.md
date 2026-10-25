# FinAI Integrated Acceptance Runbook

## Purpose

Use this runbook to verify the checked-out FinAI integration in one local session rather than running one isolated test at a time. The automated runner is **scripts/verify-finai-all.ps1**. It is intended for a Windows PowerShell development checkout.

It composes the existing verification workflow with a temporary API process and a complete paper-ledger HTTP round trip. CI configuration is intentionally out of scope and is not changed by the runner.

## Prepare once

- Install the Python dependencies from **requirements.txt** in the active virtual environment.
- Install a current Node.js LTS release so npm is on PATH.
- Ensure **frontend/package-lock.json** is committed and available for **npm ci**.
- Check out the target feature branch and pull the latest remote commits.
- Stop any other local API bound to **127.0.0.1:8000**. The script refuses to reuse an existing service.
- Keep licensed/approved finance source chunks, generated RAG indexes, router training assets, local model weights, and provider credentials outside Git as required by their terms.

Example from the current dedicated worktree:

~~~powershell
& "C:\Users\roghe\FinAI\.venv\Scripts\Activate.ps1"
git fetch origin
git pull --ff-only
powershell -ExecutionPolicy Bypass -File .\scripts\verify-finai-all.ps1
~~~

If the worktree is in a different location, activate the virtual environment that belongs to your setup instead. The runner uses the checkout's .venv Python when present; otherwise it uses the Python selected by the active PowerShell PATH.

## What the runner performs

1. Captures the branch and commit SHA for the report.
2. Reserves port 8000 and starts an API process bound only to loopback.
3. Sets up a fresh, run-specific SQLite paper ledger, explicitly enables the paper-only feature, and explicitly disables live execution.
4. Runs **scripts/verify-finai.ps1**, which executes backend pytest, frontend dependency installation, TypeScript/Vite production build, frontend lint, local API contract checks, offline package/artifact preflight, provider-configuration checks without network requests, patent-mechanism benchmark, counterfactual-screening benchmark, and the seeded 500-case SwarmTrade safety benchmark.
5. Runs paper-ledger API checks: account creation, approved simulated entry, idempotent retry, conflicting-idempotency rejection (HTTP 409), simulated close, close retry, and account/history reconciliation.
6. Validates machine-readable SwarmTrade benchmark counts and zero-failure guardrail fields.
7. Writes a JSON preflight snapshot and a consolidated JSON report.
8. Stops the temporary API process and restores the original process environment.

The runner never sets the opt-in flag for live LLM provider smoke calls. It does not submit broker orders. Do not expose the temporary API to the public internet.

## Outputs

Each run writes files below **verification-output/<UTC timestamp>/**:

- **verification-report.json** — status, exact commit, completed stages, benchmark summary, asset/configuration gaps, and explicit limitations.
- **preflight.json** — local-only dependency, model endpoint configuration, router artifact, RAG artifact, and source-data inventory.
- **api.stdout.log** and **api.stderr.log** — API start-up and server diagnostics.
- **paper-ledger.sqlite3** — disposable synthetic account/position data from this run.

The verification-output directory is excluded from version control. Preserve the report and logs if a failure needs to be diagnosed. Generated benchmark JSON files are written at the repository root and are already ignored by Git.

## Failure handling

The runner stops on the first required check that fails, writes a report with status failed, prints the API stderr tail when available, restores the environment, and terminates the API child process. Fix the reported failure and rerun the same command. A missing dependency or a local environment problem should be diagnosed rather than bypassed.

The runner requires port 8000 to be free. Do not modify the port in this script without also changing the existing verifier's API URLs.

## What passing means

A passed report means the checks actually included in that local run succeeded on the commit recorded in the report, including test/build/lint, API contracts, a simulated ledger round trip, and synthetic benchmark invariants.

It does not mean all external integrations are connected. The offline preflight intentionally reports absent assets without downloading them. Local model inference requires the separate server and weights. RAG requires approved source chunks and generated indexes. Live provider reachability is not checked by the normal runner. Frontend compile/lint is not the same as a full manual browser acceptance session. Causal claims and trading profitability require empirical, point-in-time datasets and holdout evaluation. No broker adapter, live fill reconciliation, or production trading authorization is asserted.

## Final acceptance checklist

- [ ] Full local runner passes on the commit intended for review.
- [ ] The JSON report is saved and its branch/commit SHA matches the tested checkout.
- [ ] Missing router/RAG assets are resolved or explicitly documented as not part of the intended demo.
- [ ] Local inference produces a real response with the model weights/server available, with offline-mode network behavior tested separately.
- [ ] Frontend workflows are opened in a browser and chart, watchlist, Retrieval Lab, Assistant, and Trade View interactions are manually checked.
- [ ] Provider-backed market data is smoke-tested only when credentials, terms, and API quota permit.
- [ ] Research experiments use approved timestamped data, baselines, and chronological holdouts before claims of empirical performance.
- [ ] Real-money order submission remains disabled unless a separately reviewed broker/exchange implementation, reconciliation, authentication, monitoring, and operational kill switch have all passed independent release gates.
