# FinAI Remediation and Acceptance Status

## Scope

This document records remediation work after a source-level repository audit. The current target is
`feature/finai-runtime-trading-integration`. It deliberately excludes fixing or rerunning GitHub Actions,
as requested. Source inspection and commits are not substitutes for executing tests.

## Remediation completed in this branch

### Production CORS defaults
- Development retains the four localhost origins needed by the local UI.
- Production defaults to an empty browser-origin allowlist unless `FINAI_CORS_ALLOW_ORIGINS` is set.
- Explicit origins are comma-separated and normalized for whitespace/trailing slash.
- Wildcard origin is rejected because credentialed CORS is enabled.
- Methods and request headers are explicitly enumerated instead of allowing every method/header.
- `.env.example` documents the production configuration.
- Regression tests cover development defaults, production fail-closed defaults, explicit origins, and wildcard rejection.

## Acceptance checklist — status must remain evidence-based

| Area | Current state | Acceptance evidence still required |
|---|---|---|
| CI | Excluded from this remediation request | Existing runner failure remains unresolved; no successful CI result claimed |
| Clean-clone setup | Preflight and setup docs exist; generated assets are not tracked | Run preflight in a clean checkout, provision router/RAG inputs, build artifacts, and run strict preflight |
| API authentication | Shared bearer middleware and targeted tests exist | Execute auth tests; validate deployed TLS, gateway/OIDC, token rotation, rate limiting, and ownership authorization |
| CORS | Environment-aware allowlist implemented | Execute CORS tests; configure actual production HTTPS origins and verify browser preflight |
| Session authentication | Explicitly a demo/session state flow, not identity proof | Do not use as bank/customer authentication; integrate a real identity provider before deployment |
| API contracts | FastAPI schemas and frontend API clients exist | Run endpoint smoke tests and verify UI error/loading states against a running backend |
| Financial engine | Deterministic modules and tests exist | Execute numerical edge cases, boundary tests, and independent calculations for each supported instrument |
| SwarmTrade | Simulation-only planner and synthetic safety benchmark exist | Execute benchmark; review edge cases independently; do not infer profitability from safety results |
| Paper ledger | SQLite simulation ledger and regression tests exist | Execute persistence, idempotency, transaction/concurrency, currency and P&L edge cases |
| Retrieval | FTS5/FAISS implementations and setup docs exist | Build indexes from approved data; compare recall/MRR and provenance; test empty/missing/corrupt indexes |
| Causal discovery / SCM | Research implementation exists | Point-in-time data, leakage review, identification assumptions, bootstrap diagnostics, baselines and holdout tests |
| TGAT / GFlowNet / multimodal | Research prototypes and evaluation paths documented | Reproducible training, temporal holdout, ablations, calibration, regime/OOD robustness; never call them validated before results |
| Provider/local inference | Adapters exist; runtime/credentials are external | Use explicit opt-in live smoke checks; confirm no outbound requests in offline mode and verify real model inference |
| Frontend production flow | React/Vite sources and lockfile exist | Run `npm ci`, `npm run build`, `npm run lint`; test main workflows in a browser |
| Manifest consistency | Research limitations are documented across manifest/docs | Update feature claims only after corresponding evidence artifacts and test logs are retained |

## Security and deployment guardrails

1. Keep local development bound to `127.0.0.1`; use HTTPS/TLS for remote deployment.
2. Never put server-side API tokens in Vite `VITE_*` variables or frontend source.
3. Shared bearer authentication is not user identity, per-account authorization, revocation, or a complete production identity solution. Prefer an identity-aware gateway/OIDC flow.
4. Demo session authentication is not proof of bank/customer identity. Do not connect it to real account access or financial execution.
5. Keep paper ledger and SwarmTrade explicitly simulation-only. No real broker orders/fills are supported by this integration.
6. Treat evidence supplied by a client as untrusted until authenticated against authoritative sources.
7. Treat model readiness, endpoint configuration, a successful import, and a synthetic benchmark as separate facts; none proves live inference, alpha, or causal identification.


## Unified local acceptance runner

A one-command Windows acceptance runner now composes the backend suite, frontend install/build/lint, live local API contracts, provider-configuration checks, research benchmarks, SwarmTrade benchmark assertions, and a paper-ledger API round trip:

~~~powershell
powershell -ExecutionPolicy Bypass -File .\scripts\verify-finai-all.ps1
~~~

The runner starts and stops its own loopback API and Vite dev server and uses a fresh run-specific SQLite paper ledger. When Colibrì is configured it also verifies one bounded local generation without cloud fallback. It does not opt into paid provider requests or submit real orders. The report and logs are written under verification-output/<UTC timestamp>/, which is ignored by Git. See docs/FINAL_INTEGRATION_RUNBOOK.md for setup, outputs, and limitations.

This runner has been added to the branch but has not yet been executed on the user's Windows environment. Its results must be recorded from a run on the exact commit being reviewed; do not infer success from the existence of this script or from prior pytest/benchmark output.

## Local verification commands (not executed by this document)

From the repository root in PowerShell:

```powershell
python -m pytest -q
python scripts/finai_preflight.py --strict --json
cd frontend
npm ci
npm run build
npm run lint
cd ..
python benchmarks/swarmtrade_safety_benchmark.py --output swarmtrade-safety-benchmark.json --cases 500
python scripts/run_patent_mechanism_benchmark.py --output patent-benchmark.json
```

For API smoke checks, start the backend in a separate terminal and run
`powershell -ExecutionPolicy Bypass -File ./scripts/verify-finai.ps1`.
Use `$env:FINAI_SKIP_LIVE = "1"` only when intentionally skipping HTTP smoke requests; it does not skip unit tests/build/lint/benchmarks.

## Audit honesty

- No tests, frontend build, benchmark, or live provider inference are reported as passing unless their actual execution logs are available.
- Synthetic tests assess implementation invariants, not expected returns.
- A graph discovery result or counterfactual simulation alone does not identify causal effects.
- This document is a remediation tracker, not a production-readiness certificate.
