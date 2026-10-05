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

## Cloud response providers

FinAI now exposes a provider-agnostic response layer with Google Gemini, OpenAI, OpenRouter, Anthropic and Mistral adapters, plus local/research models. Providers remain server-side behind the ModelGateway; credentials are never sent to the browser.

The ModelRouter performs deterministic capability/risk-aware policy selection and produces an auditable fallback chain. Provider quality, latency and cost tiers are configuration metadata, not proof of model superiority. Passing an explicit `model_id` remains deterministic and does not silently fail over.

The frontend Model Intelligence workspace shows provider configuration state, model capabilities and route previews without making generation calls.

See `docs/multi-cloud-model-routing.md` for the provider matrix and environment variables.

## Verification model

Financial calculations and tool results are treated as system-owned authoritative results. The language model is used as an explanation layer and is subject to the response/claim verification paths that are applicable to the intent.

## Development notes

Large model weights, generated datasets, RAG indexes, caches, and XAI trace outputs are excluded from normal source control. For reproducible deployment, keep the source-code commit and the separately versioned model/data artifacts together.

Before production deployment, replace the demo/session authentication flow with real identity and session validation, provision required data/model artifacts, configure CI, and run external provider smoke tests with real credentials.

## Professional market intelligence

The market workspace now includes an interactive candlestick terminal with wheel zoom, drag-to-pan, crosshair/inspection, reset and fullscreen controls. The Market Analyst adds a chronological model arena with Logistic Regression, Random Forest, Extra Trees, Gradient Boosting, HistGradientBoosting and MLP, plus ensemble probability, validation metrics and feature attribution.

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
