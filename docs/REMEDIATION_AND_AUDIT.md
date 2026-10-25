# FinAI Remediation Plan and Verification Record

## Scope

This document tracks the non-CI remediation requested after the repository audit. It does not claim that unexecuted tests, builds, provider calls, model inference, or empirical benchmarks have passed.

Target branch: `feature/finai-runtime-trading-integration`

## Remediation changes in this pass

- [x] Production CORS no longer inherits localhost development origins by default.
- [x] Production browser origins can be configured using `FINAI_CORS_ALLOW_ORIGINS`.
- [x] Credentialed CORS rejects wildcard origins.
- [x] Added unit tests for development defaults, production fail-closed behavior, explicit origins, deduplication, and wildcard rejection in `tests/test_cors_config.py`.
- [x] Documented the production CORS setting in `.env.example`.
- [x] Clarified that shared bearer authentication is not user identity or per-account authorization in `docs/API_PROTOCOLS.md`.

## Required local verification (not run in this editing session)

Run from a clean checkout on Windows PowerShell.

### 1. Clean checkout and dependency setup

```powershell
git fetch origin
git checkout feature/finai-runtime-trading-integration
git pull --ff-only origin feature/finai-runtime-trading-integration
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

For the frontend:

```powershell
Set-Location frontend
npm ci
npm run build
npm run lint
Set-Location ..
```

### 2. Backend regression and focused security checks

```powershell
.\.venv\Scripts\python.exe -m pytest -q tests\test_cors_config.py tests\test_api_security.py tests\test_api_main.py tests\test_swarmtrade_engine.py tests\test_swarmtrade_paper_ledger.py tests\test_research_control_api.py
.\.venv\Scripts\python.exe -m pytest -q
```

The full suite may require the generated router artifact and separately prepared datasets/indexes. Use the preflight report to identify prerequisites; do not interpret a skipped test path as a pass.

### 3. Clean-clone artifact and runtime checks

```powershell
.\.venv\Scripts\python.exe scripts\finai_preflight.py
.\.venv\Scripts\python.exe scripts\finai_preflight.py --json
```

Obtain or generate the licensed domain chunks, router model, SQLite FTS5 index, FAISS index, and document-ID map required by the current configuration. The repository intentionally does not bundle all large source datasets and generated artifacts. Record the exact source, version, and build command for each artifact before treating retrieval as reproducible.

### 4. CORS deployment check

For local development, unset `FINAI_CORS_ALLOW_ORIGINS` and use `FINAI_ENV=development`.

For production, set both:
- `FINAI_ENV=production`
- `FINAI_CORS_ALLOW_ORIGINS` to the exact comma-separated HTTPS frontend origins.

Confirm an allowed origin receives the expected CORS headers and an unlisted origin does not. CORS does not protect the API from non-browser clients and does not replace authentication.

### 5. API security acceptance

- Verify protected routes reject missing, malformed, and incorrect bearer tokens in bearer/production mode.
- Verify production without a sufficiently long token fails closed.
- Keep `/health` public only if the deployment accepts its limited metadata exposure.
- Do not expose the API directly to the public internet with the shared-token mechanism as the only user/account security control.
- The chat/session flow is a development simulation and its “authenticated” conversational state is not proof of bank/customer identity.
- Add identity-aware authentication, account ownership checks, audit logging, secret rotation/revocation, rate limiting, and TLS termination before a multi-user financial deployment.

### 6. Financial, research, and UI acceptance

- Run paper-ledger persistence/idempotency/risk-boundary tests against a temporary database and include concurrent mutation tests.
- Verify option premium assumptions, fees/slippage, currency matching, realized versus unrealized P&L, and daily-risk accounting with hand-calculated fixtures.
- Verify backtests use chronological data, no look-ahead, realistic fees/slippage, and out-of-sample evaluation; do not treat synthetic safety benchmarks as evidence of profit or alpha.
- For causal discovery, calibration, SCM counterfactuals, temporal GNN and GFlowNet research, record seeds, dataset versions, chronological train/validation/test boundaries, baseline comparisons, confidence intervals, and limitations. Architecture availability alone does not establish causal identification or predictive validity.
- Exercise frontend API response schemas, loading/error states, chart interactions, retrieval provenance, paper-ledger persistence, and local-model inference.
- Confirm the UI labels all trading functionality as simulation-only and does not imply broker orders or fills.

## Current status

- Source changes above were committed to the target branch.
- [ ] Focused tests executed successfully.
- [ ] Full backend suite executed successfully.
- [ ] Frontend production build and lint executed successfully.
- [ ] Clean-clone artifact bootstrap reproduced.
- [ ] API/provider/model runtime smoke tests completed.
- [ ] Financial and causal research benchmarks independently validated.
- [ ] Multi-user production security review completed.

CI was explicitly excluded from this remediation request and is not represented as completed. No live broker execution was enabled.
