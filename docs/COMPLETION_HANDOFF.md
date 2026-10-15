# FinAI completion branch: handoff and validation

This document distinguishes code that exists from behavior that has actually been
verified. A GitHub commit or successful TypeScript build is not proof that cloud
credentials, data corpora, hardware-specific model loading, banking rails, or
production security controls work in a live deployment.

## New capability-aware execution planner

`orchestrator/execution_plan.py` introduces a dependency-free planning primitive:

- `CapabilityStateGraph` records capability availability, supported execution modes,
  prerequisite relationships, metadata, and reasons for unavailability.
- `FinAIExecutionPlan` serializes an ordered set of stages with explicit dependencies.
- `build_execution_plan` produces a conservative plan for policy, deterministic
  finance, retrieval, model generation, claim verification, and response verification.
- Prerequisite cycles are rejected. Missing required capabilities block the plan.
- `FinAIHybridEngine.process` now attaches a `capability_execution_plan`
  diagnostic to each returned result. This is separate from the legacy `execution_plan`
  authority/controller contract and records the observed stage and status.
- `XAISessionOrchestrator` writes this diagnostic into a separate XAI trace field
  (`capability_execution_plan`); it does not overwrite the recorded authority decision.
- This is request-path observability, **not an authorization or execution gate**. The
  existing router, policy, authority, and risk-control layers remain authoritative.
  The capability graph object is still in-memory; only the resulting diagnostic is
  recorded with the existing XAI trace. Full policy-gated execution-plan dispatch,
  durable graph-state storage, and enforced offline/degraded mode remain incomplete.

Regression coverage lives in `tests/test_execution_plan.py` and
`tests/test_capability_plan_integration.py`; both are listed in the artifact-independent
CI command. Local and hosted test runs must be repeated against the current branch.

## Offline and clean-checkout safeguards

- `policy/network_mode.py` is the shared policy for `online`, `degraded`, and
  `offline`. The current explicit guards cover provider generation through the model
  gateway, constrained LLM fallback selection, Yahoo Finance market/news lookups,
  live CCXT market requests, and mempool.space requests.
- These guards do not form a process/OS-level network sandbox. Audit new outbound HTTP
  clients and do not label the entire service offline-safe until every external path is
  covered.
- The local rLLM adapter uses `local_files_only=True`; the Qwen embedding adapter
  resolves only a cached Hugging Face snapshot when `FINAI_NETWORK_MODE=offline`.
  The current rLLM model adapter is GPU-only 4-bit quantization, not NVMe model-weight
  streaming.
- `scripts/finai_preflight.py` checks packages and required/generated artifact presence
  without exposing secret values or contacting providers. See `docs/OFFLINE_AND_PREFLIGHT.md`.
- `llm/colibri_adapter.py` is an opt-in, loopback-only adapter for a separately installed Colibrì OpenAI-compatible server. It is registered as `colibri-local` only when `FINAI_COLIBRI_BASE_URL` is set. The external engine and weights remain separately provisioned; the FinAI adapter does not implement expert streaming itself. See `docs/OFFLINE_AND_PREFLIGHT.md`.
- `scripts/build_rag_faiss.py` validates saved index/ID/checkpoint alignment and fails
  closed for ambiguous indexes. Approved source chunks and large derived artifacts
  still need to be supplied/provisioned in each clean clone.




## API bearer guard (15 October 2026)

`app/api_security.py` provides a configurable shared-token boundary, registered in
`app/main.py`. Development mode remains open for local UI work. When
`FINAI_API_AUTH_MODE=bearer`, requests other than `/health` and CORS OPTIONS
preflight require `Authorization: Bearer ...`. When `FINAI_ENV=production`, the
guard fails closed unless `FINAI_API_BEARER_TOKEN` is configured with at least
32 characters, even if the mode was mistakenly left at development. Invalid mode
configuration also returns a service-unavailable response.

This is not full production identity: there are no per-user identities, roles,
tenant isolation, session ownership, refresh/revocation, MFA, or rate limiting in
this middleware. Do not embed a shared token in a browser bundle. Use a private
network and an identity-aware reverse proxy/OIDC gateway for browser deployments.
Regression coverage is in `tests/test_api_security.py`; the artifact-independent
CI test list includes it and `tests/test_finite_api_inputs.py`.

`scripts/verify-finai.ps1` now prefers the repository virtualenv interpreter,
runs the full Python suite, performs `npm ci`, frontend build and lint, checks
the local API when `FINAI_SKIP_LIVE` is not set, and runs both deterministic
research benchmark scripts. Review every output and warning; the script is not
evidence that external provider credentials, real market-data reachability, or
bank/DLT integrations work.

## Fresh Windows checkout

Run in PowerShell from the repository root:

```powershell
git status --short
git switch ai/finai-completion
git pull
py -3.11 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m pytest -q
```

If PyTorch installation is unsuitable for the machine's CUDA/CPU setup, use the
official PyTorch selector to install the correct build, then install the remaining
requirements. Do not install dependencies into a different interpreter and then
invoke a global `pytest`.

Frontend:

```powershell
cd frontend
npm ci
npm run build
npm run lint
```

Start API and UI in separate terminals:

```powershell
# repository root
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

```powershell
# frontend directory
npm run dev
```

The XAI API, where needed, is started separately with
`python -m uvicorn app.xai_api:app --host 127.0.0.1 --port 8001`.

## Generated assets and external services

- The TF-IDF router model at `router/models/finai_router_tfidf.joblib` is generated
  and not tracked. Use the repository's router training script and inspect its
  arguments before generating it; the exact source training JSONL must be present.
- RAG builders require source JSONL files under `data/domain_chunks/`. Obtain data
  only from approved sources and record source URLs, licenses, retrieval dates, and
  transformation steps. Generated SQLite/FAISS indexes are not a substitute for
  the original licensed source data.
- Copy `.env.example` to `.env` and configure only the provider credentials you
  actually use. Never commit `.env`, API keys, user financial data, or real account
  credentials.
- A passing unit suite does not prove that provider IDs are current, credentials are
  valid, or external market/banking services are reachable. Run explicitly labelled
  live smoke tests only when credentials and network access are available.
- Offline mode must be verified with networking disabled. Do not call a mode
  "offline" merely because a local fallback is configured.

## Features not certified as complete by this branch

These require environment-specific execution or further engineering; they must not
be represented as finished based on this planning module:

1. Persistent capability graph storage and orchestration wired into every request path.
2. Actual expert/weight streaming between GPU VRAM, RAM, and NVMe, with measured
   latency, peak memory, throughput, and correctness versus a baseline.
3. End-to-end network-loss operation for local inference, retrieval, deterministic
   calculations, verification, and safe fallbacks.
4. Live validation of every provider/model ID and failover path.
5. Production identity, authorization, encrypted session storage, rate limits, audit
   retention, and transaction approval controls.
6. Real bank/payment/DLT settlement and recovery. Mock tools must remain clearly marked.
7. Research evidence from broader financial scenarios and independently reviewed
   patentability. A benchmark is not a legal novelty opinion.

## Handoff evidence to collect

Attach the exact commit SHA and record the following from a clean checkout:

- Python version, OS, CPU/GPU, CUDA/runtime, dependency install output.
- Full backend pytest summary and failed test names (if any).
- Frontend `npm ci`, `npm run build`, and `npm run lint` output.
- API smoke checks for health, chat, model registry, causal-risk, and XAI endpoints.
- Provider name/model ID and redacted status for each live-provider smoke test.
- Router and RAG artifact checksums and source-data provenance.
- Patent benchmark JSON, scenario configuration, false-prune count/rate, exact
  completion evaluations, certificate evaluations, runtime, and limitations.
- Screenshots of the actual running UI at desktop and narrow viewport widths.

Never report an unrun test as passing. Record unavailable external dependencies as
blocked rather than silently skipping them.


## Research prototype additions (13 October 2026)

The completion branch now carries two separate experimental causal-risk prototypes:
- **EPCRP:** evidence-gated paired-world deltas with regime/time-scope checks and evidence-linked output lineage (finance_engine/epcrp.py).
- **Intervention feasibility screening:** conservative interval screening for bounded linear DAG interventions (finance_engine/counterfactual_screening.py).

Both are opt-in research components. Neither is a causal discovery engine or a validated production risk model. The linear-DAG assumptions, financial calibration, temporal modeling, production API/orchestrator integration, and claim-focused legal review remain open. Synthetic benchmarks must not be presented as proof of financial accuracy, novelty, or patentability.


## ResilientPay settlement seam

The completion branch includes the experimental local-first payment journal in resilient_pay/ledger.py. It deliberately stops at a payment-intent/adapter contract and a simulation-only adapter. It must not be represented as live banking or Fabric settlement. The external gateway, channel/chaincode, credentials/identities, reconciliation protocol, and independent security review remain deployment-specific.


## Updates added after the 15 October handoff

### Trade View planning workspace

- Added `frontend/src/components/TradeToolsPanel.tsx` to the market terminal with a browser-local watchlist, above/below price-alert conditions, and a position-sizing / reward-risk calculator.
- Added responsive styling in `frontend/src/components/MarketTerminal.css` and a manual smoke checklist in `docs/TRADE_VIEW_TOOLS.md`.
- Watchlist selection dispatches a local browser event consumed by MarketTerminal.
- These tools do not place orders, provide broker connectivity, or deliver background/push alerts. The browser checklist still needs to be run.

### Counterfactual directional stability

- Added `finance_engine/counterfactual_stability.py`, unit/API tests, and a protected opt-in endpoint at `/api/v1/research/patent-mechanisms/counterfactual-stability`.
- The endpoint is included in the existing research router, which is mounted only when `FINAI_ENABLE_RESEARCH_PATENT_ENDPOINTS=true`; the router requires `FINAI_RESEARCH_API_TOKEN` with at least 32 characters.
- The endpoint compares repeated approved runs and produces a replay digest. It is a research robustness gate, not causal proof, a production investment decision, or evidence of patentability.
- Added the focused tests to artifact-independent CI. The latest commits still need local/hosted execution; no passing status is claimed.

### Current review requirement

Run the complete backend suite, frontend build/lint, research tests/benchmarks, and browser smoke checklist from a fresh checkout of `ai/finai-completion`. Verify the CI runner issue separately. Do not merge to `main` or describe this branch as production-ready until those checks are reviewed.


## FinAI Brain integration pass

- The assistant UI now renders the backend's per-request `capability_execution_plan` as a diagnostic stage list, including required/optional stages, dependencies, observed backend stage/status, and block explanations. It is explicitly labeled as a plan, not proof that every stage ran successfully.
- Added `GET /api/v1/system/brain-status` and tests. The endpoint reports source/artifact presence and provider credential *names* only; it does not contact providers, expose secrets, prove model inference, or validate causal claims.
- The Assistant workspace now loads and can refresh the Brain layer readiness diagnostics instead of showing hard-coded green checks for retrieval and evidence grounding.
- Added `tests/test_brain_status_api.py` to artifact-independent CI.
- Still required: run backend tests, frontend build/lint, browser smoke tests, and verify that the latest hosted Actions runner executes job steps. This change set has not yet been runtime-validated.
