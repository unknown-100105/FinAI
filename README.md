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

Gemini is the primary configured cloud response provider. OpenRouter is implemented as an automatic provider fallback and defaults to `openrouter/auto` when its environment variables are configured.

The fallback path is used only for automatic model selection. Passing an explicit `model_id` remains deterministic.

## Verification model

Financial calculations and tool results are treated as system-owned authoritative results. The language model is used as an explanation layer and is subject to the response/claim verification paths that are applicable to the intent.

## Development notes

Large model weights, generated datasets, RAG indexes, caches, and XAI trace outputs are excluded from normal source control. For reproducible deployment, keep the source-code commit and the separately versioned model/data artifacts together.

Before production deployment, replace the demo/session authentication flow with real identity and session validation, provision required data/model artifacts, configure CI, and run external provider smoke tests with real credentials.
