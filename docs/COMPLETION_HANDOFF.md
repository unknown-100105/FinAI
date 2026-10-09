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
- The planner does not perform policy authorization, execute tools, guarantee a model
  is actually reachable, or persist state. The caller must re-check authorization at
  execution time and provide a durable store if persistence is required.

Regression coverage lives in `tests/test_execution_plan.py`. These tests are included
in the artifact-independent CI test command.

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
