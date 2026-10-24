# FinAI

FinAI is a financial-domain assistant with a staged pipeline for routing, policy/authority control, deterministic execution, retrieval, model response generation, verification, and XAI tracing.

## Repository layout

- `app/` — FastAPI application and API routes
- `router/` — intent and domain routing
- `policy/` — policy and authority contracts
- `orchestrator/` — session and hybrid execution orchestration
- `finance_engine/` — deterministic financial calculations
- `market_data/` — market-data providers and dispatch
- `rag/` — hybrid lexical/semantic retrieval
- `llm/` — model gateway, adapters, and cloud providers
- `xai/` — claims, verification, and trace generation
- `frontend/` — React/Vite frontend
- `scripts/` — training, RAG, validation, and audit utilities
- `tests/` — regression and integration tests

## Backend setup

Create and activate a virtual environment, then install:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

For a GPU-specific PyTorch build, install the appropriate PyTorch package for the local CUDA/runtime combination before running the model or embedding workloads.

Copy `.env.example` to `.env` and populate only the keys needed by the configured providers.

## Run the API

```powershell
uvicorn app.main:app --host 127.0.0.1 --port 8000
```

The main API is available at `http://127.0.0.1:8000`.

The XAI trace API can be run separately:

```powershell
uvicorn app.xai_api:app --host 127.0.0.1 --port 8001
```

## Frontend

```powershell
cd frontend
npm ci
npm run dev
```

Production build:

```powershell
npm run build
```

## Tests

Run the backend regression suite:

```powershell
python -m pytest -q
```

For the full Windows verification flow (backend tests, frontend install/build/lint, local API smoke checks, and the deterministic research/SwarmTrade benchmarks), start the backend in one terminal:

```powershell
uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Then run from the repository root in another PowerShell terminal:

```powershell
powershell -ExecutionPolicy Bypass -File ./scripts/verify-finai.ps1
```

The verifier writes `patent-benchmark.json` and `swarmtrade-safety-benchmark.json`; these generated outputs are ignored by Git. It does not place orders. Set `$env:FINAI_SKIP_LIVE = "1"` to skip HTTP smoke checks when the backend is not running, but the regression suite, frontend checks and benchmarks still run.

Do not treat a passing test suite as proof that external services, generated model artifacts, or production credentials are available.

The dedicated TF-IDF router model at
`router/models/finai_router_tfidf.joblib` is a generated artifact and is not
tracked in Git. Build or restore that artifact before running the complete
end-to-end regression suite. GitHub CI runs the full suite when the artifact is
available; otherwise it runs the artifact-independent regression coverage.

## RAG setup

The repository contains the RAG builders, but large source corpora and generated FAISS/SQLite artifacts are intentionally not tracked.

Build the lexical database:

```powershell
python scripts/build_rag_index.py
```

Then build the semantic index:

```powershell
python scripts/build_rag_faiss.py
```

The current builders expect the domain chunk files under `data/domain_chunks/`. Those source datasets must be obtained or generated separately. A fresh clone therefore does not contain a ready-to-query production RAG index until these assets are prepared.

Before running end-to-end tests on a fresh clone, run the local preflight and review offline-mode behavior:

```powershell
python scripts/finai_preflight.py
python scripts/finai_preflight.py --json
```

See [Offline mode and preflight guide](docs/OFFLINE_AND_PREFLIGHT.md) for the network-policy contract, local model requirements, artifact prerequisites, and tests. Offline checks cover the currently guarded provider paths, not arbitrary direct network calls from future modules.

## Financial data ingestion and FinAI training

Read-only Financial Datasets and Longbridge adapters can collect historical prices, statements and optional news metadata into a local, source-attributed JSONL corpus. The existing Sarvam QLoRA trainer accepts curated extra JSONL training files with --extra-train-file; provider disagreements are excluded by the SFT builder. No brokerage orders are placed.

See [Financial data connector runbook](docs/FINANCIAL_DATA_CONNECTORS.md) for environment setup, ingestion commands, data manifests, the SFT builder, bounded smoke training and provider limitations. Provider terms and training/redistribution rights must be checked before data is used; secrets, raw provider records and generated training files must not be committed.

## Retrieval Lab

The interface includes a **Retrieval Lab** that compares the embedding-free SQLite FTS5/BM25 retriever with the existing FTS5 + FAISS hybrid path on the same query. It displays source text and provenance, per-mode availability, ranking diagnostics and latency. The lab retrieves evidence only; it does not generate answers, and scores are not probabilities or proof of correctness.

API: `POST /api/v1/retrieval-lab/search` with `query`, `mode` (`vectorless`, `hybrid`, or `compare`) and optional `top_k` (1–10). Vectorless retrieval needs the SQLite database and FTS5 index; hybrid additionally needs the FAISS index, document-ID map and embedding runtime/model assets. Missing hybrid assets do not hide vectorless results in comparison mode.

See [Retrieval Lab setup and evaluation guide](docs/RETRIEVAL_LAB.md) for build instructions, limitations, and a defensible Recall@k/MRR/latency benchmark protocol.

## Optional local Colibrì inference

FinAI can optionally route response generation to a separately installed
[Colibrì inference engine](https://github.com/JustVugg/colibri) through its
OpenAI-compatible local API. FinAI does **not** bundle the third-party engine or
its model weights, and this adapter does not implement Colibrì's GPU/RAM/NVMe
weight streaming itself.

Follow the upstream [Windows guide](https://github.com/JustVugg/colibri/blob/main/docs/windows.md)
and [API guide](https://github.com/JustVugg/colibri/blob/main/docs/api.md) to
install a supported runtime/model and bind its server to `127.0.0.1`. Then
set these values in the PowerShell session that launches FinAI (or in your
local `.env` file, which must not be committed):

```powershell
$env:FINAI_COLIBRI_BASE_URL = "http://127.0.0.1:8010/v1" # separate from FinAI API on port 8000; use the actual local server port
$env:FINAI_COLIBRI_MODEL = "olmoe-colibri" # must match the server's configured model ID
$env:FINAI_COLIBRI_API_KEY = "local-finetoken"
$env:FINAI_NETWORK_MODE = "offline"
$env:FINAI_DATA_SENSITIVITY = "restricted"
```

The adapter is disabled while `FINAI_COLIBRI_BASE_URL` is blank, accepts only
loopback endpoints, and refuses redirects. Keep the Colibrì server on a different
port from FinAI's API (FinAI defaults to `127.0.0.1:8000`; the example local
model port above is `8010`). These variables must be set in the backend
process environment before starting FinAI.

After starting both services, run a real local generation smoke test from the
repository root:

```powershell
.\\.venv\\Scripts\\python.exe scripts\\smoke_local_model.py
```

The script requires the backend Brain diagnostics to report offline mode, probes
the configured model ID through the loopback model-list endpoint, and sends a
synthetic, non-sensitive request through FinAI's ordinary chat route with
`colibri-local` explicitly selected. It does not call cloud providers directly.
A successful smoke test proves only one request completed; it is not an evaluation
of financial accuracy or model quality. See [Local model status](docs/LOCAL_MODEL_STATUS.md)
and [Offline mode and preflight](docs/OFFLINE_AND_PREFLIGHT.md) for setup and limitations.

## Cloud response providers

FinAI now exposes a provider-agnostic response layer with Google Gemini, OpenAI, OpenRouter, Anthropic and Mistral adapters, plus local/research models. Providers remain server-side behind the ModelGateway; credentials are never sent to the browser.

The ModelRouter performs deterministic capability/risk-aware policy selection and produces an auditable fallback chain. Provider quality, latency and cost tiers are configuration metadata, not proof of model superiority. Passing an explicit `model_id` remains deterministic and does not silently fail over.

The frontend Model Intelligence workspace shows provider configuration state, model capabilities and route previews without making generation calls.

See `docs/multi-cloud-model-routing.md` for the provider matrix and environment variables.

## Verification model

Financial calculations and tool results are treated as system-owned authoritative results. The language model is used as an explanation layer and is subject to the response/claim verification paths that are applicable to the intent.

The local FinAI Brain readiness endpoint is `GET /api/v1/system/brain-status`. It reports file/configuration evidence only; it does not contact providers or claim successful live inference.

## Development notes

Large model weights, generated datasets, RAG indexes, caches, and XAI trace outputs are excluded from normal source control. For reproducible deployment, keep the source-code commit and the separately versioned model/data artifacts together.

Before production deployment, replace the demo/session authentication flow with real identity and session validation, provision required data/model artifacts, configure CI, and run external provider smoke tests with real credentials.

## Professional market intelligence

The market workspace now includes an interactive candlestick terminal with wheel zoom, drag-to-pan, vertical/horizontal crosshair inspection, reset and fullscreen controls. It supports selectable SMA 20, EMA 20 and Bollinger Band overlays, a volume toggle, and per-instrument browser-local horizontal levels and two-anchor trendlines. A historical SMA crossover lab simulates next-bar-open execution with configurable fee/slippage assumptions, an equity curve and a buy-and-hold comparator; it does not place orders. The Market Analyst adds a chronological model arena with Logistic Regression, Random Forest, Extra Trees, Gradient Boosting, HistGradientBoosting and MLP, plus ensemble probability, validation metrics and feature attribution. The terminal also includes browser-local watchlists, above/below quote alert conditions, individual candle explanations, and a position-sizing/reward-risk calculator. These are planning tools only: alerts are not push notifications, and the UI does not place broker orders. See docs/TRADE_VIEW_TOOLS.md.

The Global Markets workspace provides a research registry across major regions and asset classes including equities, ETFs, government bonds, corporate bonds, deposits/FDs, funds, REITs, commodities and currencies. For an Indian resident, the eligibility workflow explicitly checks the areas that must be verified: FEMA/LRS, local foreign-investor rules, KYC, currency/repatriation, withholding and Indian tax/reporting.

Prediction outputs are historical model benchmarks, not guaranteed forecasts or a claim of a universally best market-prediction model. Global eligibility is instrument-specific and conditional where current regulatory/product verification is required.

### New intelligence APIs

- `GET /api/v1/intelligence/prediction`
- `GET /api/v1/intelligence/global-assets`
- `GET /api/v1/intelligence/eligibility`


### Research-stage causal stress intelligence

The Causal Risk Lab now includes a second-stage research path for empirical
calibration, causal-empirical GFlowNet reward training, chronological temporal
GNN holdout evaluation, and a trainable masked-modality financial encoder.

Research endpoints include:

- `POST /api/v1/causal-risk/risk-calibration/fit-channels`
- `POST /api/v1/causal-risk/temporal-gnn/train`
- `POST /api/v1/causal-risk/multimodal/train`
- `POST /api/v1/causal-risk/gfnets/train` with
  `reward_mode=causal_empirical`

Research documentation:

- `docs/research-gap-and-novelty.md`
- `docs/research-training-runbook.md`
- `docs/finai-final-architecture.md`

The research stack distinguishes implementation, training, future-holdout
evaluation, empirical validation and production eligibility. No prototype is
automatically promoted to production status by virtue of passing software tests.


## Consolidated investment knowledge scope

FinAI's investment-knowledge layer covers the complete non-real-estate scope requested for the platform.

### Resident Indians
- Domestic equities: listed/unlisted direct shares, equity/debt/index/hybrid/liquid mutual funds, ETFs, F&O, PMS and AIFs.
- Fixed income: bank FDs/RDs, corporate bonds, NCDs, Commercial Paper, G-Secs, T-Bills and SDLs.
- Government savings/retirement: PPF, EPF, NPS, SCSS, SSY, NSC and KVP.
- Precious metals: Digital Gold, Gold funds/ETFs, SGB secondary-market exposure and Silver ETFs.
- VDAs: buying, selling, holding, staking, trading and the applicable Indian AML/FIU/tax framework.
- Overseas: foreign equities, global funds/ETFs, eligible foreign-currency deposits, ODI and IFSC/GIFT City routes. RBI's LRS ceiling for resident individuals is USD 250,000 per financial year for permitted transactions.

### NRIs / OCIs
The registry covers NRE/NRO, NRE/FCNR(B)/NRO deposits, Indian capital markets, mutual funds/ETFs, PMS, AIFs, G-Secs/T-Bills, corporate bonds, NPS where eligible, and IFSC/GIFT City products. NRI restrictions are represented as product- and rule-specific rather than hard-coded blanket claims.

### Regulatory framework
SEBI/capital markets; RBI/FEMA/foreign exchange; banking and government savings; Income Tax/Black Money/CGST; PFRDA/IRDAI/EPFO; and PMLA/BUDS/consumer-safety domains are represented as first-class knowledge categories.

### VDA knowledge
FinAI covers coins vs tokens, PoW, PoS, spot holding, staking, mining, DeFi AMMs, lending, perpetual/leveraged pools, crypto ETFs, ERC-20 contracts, multi-hop swaps, rug pulls, honeypots and hidden minting. Current Indian VDA tax knowledge records Section 115BBH's 30% rate plus applicable surcharge/cess and Schedule VDA reporting; FIU-IND AML/VDA guidance is treated as a live regulatory source.

### Global investment universe
The registry includes major markets across North America, Europe, Asia-Pacific, Middle East, Latin America and Africa, with equities, ETFs, indices, government bonds, corporate bonds, deposits, funds, REITs, commodities and FX. Argentina is explicitly represented as a conditional example for foreign fixed-term deposits; FinAI requires bank-level eligibility, FX/repatriation, KYC, FEMA/LRS and tax verification before presenting it as investable.

**Important:** FinAI stores regulatory knowledge with source metadata and verification status. It should not present stale, jurisdiction-specific or instrument-specific rules as unconditional investment permission.

Investment knowledge API endpoints:
- `/api/v1/investments/scope`
- `/api/v1/investments/global-markets`


## Experimental causal-risk research prototypes

The research branch includes two explicitly experimental mechanisms:

- **Evidence-Gated Paired-World Causal Risk Propagation (EPCRP):** finance_engine/epcrp.py compares baseline and intervention worlds and records edge acceptance/rejection plus evidence lineage. See docs/EPCRP_EVIDENCE_GATED_CAUSAL_RISK.md.
- **Intervention feasibility screening:** finance_engine/counterfactual_screening.py screens bounded linear-DAG interventions using conservative interval bounds. RETAIN means only that infeasibility was not proven.
- **Counterfactual directional stability gate:** finance_engine/counterfactual_stability.py compares repeated, approved estimates across model versions, graph/evidence fingerprints and regimes. It flags intervals crossing zero or directional disagreement and emits a deterministic replay digest. It is a robustness diagnostic, not causal identification or a forecast guarantee.

Run python -m pytest -q tests/test_epcrp.py tests/test_counterfactual_screening.py tests/test_counterfactual_stability.py tests/test_counterfactual_stability_api.py and python benchmarks/counterfactual_screening_benchmark.py from the repository root. These are research prototypes and synthetic benchmarks, not real-market validation, causal discovery, or proof of patentability. They are not enabled as production decision paths by default.


### Running the experimental research endpoints (local only)

The EPCRP, feasibility-screen, and counterfactual-stability HTTP routes are disabled by default. To mount them in a local development server, set the environment variables before starting the API process:

PowerShell:

    $env:FINAI_ENABLE_RESEARCH_PATENT_ENDPOINTS = "true"
    $env:FINAI_RESEARCH_API_TOKEN = "<unique-random-secret-at-least-32-characters>"

Then start FinAI using the normal API command for this checkout. Restart the process after changing the variable. The router requires this bearer token on every research request. Do not expose these research-only endpoints to public clients without a separately reviewed deployment boundary, rate limiting, and monitoring. The API token is not user identity or tenant isolation. Never commit actual credentials.


## ResilientPay bridge status

The branch includes a local-first payment-intent journal and adapter contract in resilient_pay/ledger.py. It supports idempotency conflict checks, confirmed/authenticated adapter dispatch, state transitions, reconciliation-required handling for ambiguous outcomes, and an integrity-checkable hash-chained journal. LocalSimulationAdapter is a sandbox-only simulator. This is not a live bank or Hyperledger Fabric settlement integration; see docs/RESILIENTPAY_SETTLEMENT_BRIDGE.md.

Run the local-only ResilientPay simulation with `python scripts/demo_resilient_pay.py`. It uses an in-memory journal and a SIM-prefixed adapter; no external payment service is called and no real funds are moved.


## SwarmTrade deterministic planning baseline

The integration branch now includes a deterministic, simulation-only SwarmTrade planner in the Market Terminal. It uses 5–500 logical votes in multiples of five, requires protective levels, applies a hard 1% single-trade risk cap and 3% aggregate open-risk cap, checks the daily loss threshold, and includes explicit cost assumptions. The frontend computes transparent trend, momentum, mean-reversion and breakout features from the selected chart bars; sentiment defaults to neutral.

API:
- `GET /api/v1/swarmtrade/status`
- `POST /api/v1/swarmtrade/plan`

For options, callers must supply a per-contract maximum-loss assumption. Futures require verified tick size, tick value and margin per contract. Forex requires pip size, pip value in the account currency and margin per configured unit or lot. The planner does not execute orders, connect brokers, compute complete option Greeks/payoffs, or provide venue-specific margin/rollover/FX conversion logic.

Details and a manual verification checklist are in [docs/SWARMTRADE_SAFE_EXECUTION.md](docs/SWARMTRADE_SAFE_EXECUTION.md). Run:

```powershell
python -m pytest -q tests/test_swarmtrade_engine.py
python benchmarks/swarmtrade_safety_benchmark.py --output swarmtrade-safety-benchmark.json --cases 500
```

The benchmark is synthetic implementation-safety testing, not evidence of investment performance or real-market prediction quality.


### Persistent SwarmTrade paper ledger

A separate opt-in SQLite ledger records simulated positions and P&L. To enable it for trusted local verification, set `FINAI_ENABLE_SWARMTRADE_PAPER_LEDGER=1` in `.env`; `FINAI_SWARMTRADE_PAPER_DB` sets the file path. It is disabled by default. The API requires explicit simulation acknowledgement, records idempotent open/close events, enforces paper-account current equity and aggregate risk limits, and never sends a live order. Account equity excludes unrealized P&L; manual exits use caller-supplied prices.

See [docs/SWARMTRADE_PAPER_LEDGER.md](docs/SWARMTRADE_PAPER_LEDGER.md). Run `python -m pytest -q tests/test_swarmtrade_paper_ledger.py` for the focused tests.
