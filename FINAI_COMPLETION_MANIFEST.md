# FinAI Completion Manifest

This manifest describes the repository state intended for the final local pull-and-verify cycle.

## Primary branch

`ai/finai-completion`

## Implemented research stack

### Causal discovery
- Linear NOTEARS research implementation
- Lagged temporal ridge screening baseline
- Rolling discovery stability
- Direction conflict detection
- Consensus graph construction
- Explicit research approval gate
- Empirical chronological calibration with moving-block bootstrap
- Bounded API input sizes

### Counterfactual risk
- Linear SCM with `do(X=x)` intervention semantics
- Intrinsic causal path explanation
- Versioned risk-parameter configuration
- Research-only counterfactual execution for explicitly approved graphs
- Deterministic symbolic safety checks

### Tail risk
- Reproducible Monte-Carlo baseline
- Correlation-aware Gaussian sampling
- Student-t copula research sampler
- Empirical market correlation extraction
- SCM evaluation of generated tail scenarios
- GFlowNet-style tail trajectory research prototype

### Temporal graph learning
- TGAT-style continuous-time attention layer
- Trainable temporal risk model
- Reproducible training routine
- Explicit temporal out-of-sample validation boundary

### Multimodal intelligence
- Typed graph node/edge primitives
- Market/macro/text/event/entity/portfolio modalities
- Provenance tracking
- Deterministic modality fusion
- Document/event/portfolio ingestion adapters
- Text-to-graph embedding alignment utility

### Neuro-symbolic safety
- Allocation and shock constraints
- Unknown intervention rejection
- Explicit research-gate requirement
- Deterministic hard-rule semantics

### Research evaluation
- Regime assignment utilities
- Regime-conditioned prediction metrics
- Research status endpoint
- Architecture and limitation documentation
- Gemini read-only audit contract

## Main API additions

- `POST /api/v1/causal-risk/risk-calibration`
- `POST /api/v1/causal-risk/gfnets/train`
- `POST /api/v1/causal-risk/gfnets/generate`
- `POST /api/v1/causal-risk/multimodal/encode`
- `POST /api/v1/causal-risk/regime-benchmark`
- `GET /api/v1/causal-risk/research-status`
- `GET /api/v1/system/brain-status` (secret-safe local readiness diagnostics)
- `POST /api/v1/causal-risk/research-counterfactual`
- Advanced tail-dependence options on the causal-risk tail/counterfactual APIs

## FinAI Brain and user-facing tools

- The Assistant workspace displays the request's capability-plan diagnostics and local Brain readiness indicators.
- The plan models policy, market-data dispatch, deterministic finance, structured knowledge, hybrid retrieval, resource planning, generation, and verification; it remains diagnostic and does not replace existing authorization or dispatch paths.
- Trade View includes browser-local watchlists, quote-threshold alert conditions, and long/short-aware position sizing/reward-risk estimates. It does not submit broker orders or send push notifications.
- The local inference adapters and model artifacts must be provisioned separately. A configured endpoint or credential is not evidence of successful live inference.

## Research honesty rules

The repository must never claim that:
- NOTEARS establishes identified causal effects by itself;
- correlation-aware Gaussian sampling is a complete tail model;
- the Student-t copula is a trained GFlowNet;
- a TGAT architecture is empirically validated simply because it can train;
- embedding similarity establishes factual or causal relations.

## Final local verification

Run from the repository root:

```powershell
git pull origin ai/finai-completion
pytest -q
```

Then verify backend, frontend, live API contracts, provider configuration, and deterministic research benchmarks:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
cd frontend
npm ci
npm run build
npm run lint
cd ..
.\.venv\Scripts\python.exe scripts\finai_preflight.py
.\.venv\Scripts\python.exe scripts\smoke_llm_providers.py
.\.venv\Scripts\python.exe scripts\run_patent_mechanism_benchmark.py --output patent-benchmark.json
.\.venv\Scripts\python.exe benchmarks\counterfactual_screening_benchmark.py
```

For the expanded live API checks, start the API first and run:

```powershell
.\scripts\verify-finai.ps1
```

Provider smoke calls are not sent by default. To deliberately test configured cloud
providers with a synthetic prompt (may incur charges), set
`$env:FINAI_RUN_LIVE_PROVIDER_SMOKE = "1"` before running the verification script.

For live API checks, start the backend and run `$env:FINAI_SKIP_LIVE = $null` before rerunning `scripts/verify-finai.ps1`.

Then start the backend and smoke-test:

```powershell
uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Verify:
- `/health`
- `/api/v1/causal-risk/graph`
- `/api/v1/causal-risk/architecture`
- `/api/v1/causal-risk/research-status`
- `/api/v1/causal-risk/tail-scenarios`
- `/api/v1/causal-risk/discover/market-graph/calibration`

## Gemini audit

After the repository has been pulled locally, give Gemini the contents of `GEMINI_FINAL_AUDIT.md` and instruct it to perform the final independent read-only audit.

Gemini must report findings only. It must not modify this repository.

## Final acceptance

Do not mark the project fully verified until:
1. the complete local test suite passes;
2. the frontend build passes;
3. the live causal-risk APIs return the expected research statuses;
4. the Gemini final audit has been reviewed;
5. all genuine audit findings have been fixed and re-tested.


## Research-completion upgrade

The implementation now includes a second-stage research path:

- Empirical SCM channel calibration with chronological Ridge fitting and
  versioned bundle selection through FINAI_RISK_CALIBRATION_PATH.
- Adaptive NOTEARS augmented-Lagrangian penalty growth and convergence history.
- Causal empirical GFlowNet reward combining tail severity, empirical support,
  causal-direction alignment and portfolio relevance.
- Chronological multi-snapshot TGAT training with future-only holdout evaluation,
  deterministic seeding and CPU/CUDA device handling.
- Trainable masked-modality multimodal financial encoder with missing-modality
  support.
- Additional API collection-size limits and research training endpoints.
- Research-gap, novelty, competitive-landscape and training runbook documents.

## New research endpoints

- POST /api/v1/causal-risk/risk-calibration/fit-channels
- POST /api/v1/causal-risk/temporal-gnn/train
- POST /api/v1/causal-risk/multimodal/train
- Existing POST /api/v1/causal-risk/gfnets/train now supports
  reward_mode=causal_empirical.

## What remains data-dependent

The repository now contains the mechanisms needed to perform the stronger
experiments, but the following cannot honestly be marked empirically validated
until the owner supplies/approves a point-in-time dataset and runs the
experiments:

- empirical SCM coefficient promotion;
- future-held-out TGAT validation;
- causal empirical GFlowNet training and backtesting;
- masked-modality multimodal pretraining;
- tail-risk backtesting;
- regime/OOD robustness;
- ablations;
- prior-art/patent novelty confirmation.

See docs/research-gap-and-novelty.md and
docs/research-training-runbook.md.


## Patent-mechanism verification additions

The final verification cycle now also runs:
`python scripts/run_patent_mechanism_benchmark.py --output patent-benchmark.json`.

The benchmark compares exhaustive completion evaluation with forward
certificate and bidirectional necessary-interval screening and records
incremental interval-evaluation accounting. It is deterministic in its logical
metrics; wall-clock measurements are environment-dependent.

The previously added `causal_risk/finai_control_plane.py` was found to be
unreferenced by the PR diff and has been removed to avoid maintaining two
overlapping research control-plane implementations. The retained
`causal_risk/research_control_plane.py` is explicitly research-only.


## Integration and verification status

For the runtime/trading integration branch, see
[docs/REMEDIATION_AND_ACCEPTANCE.md](docs/REMEDIATION_AND_ACCEPTANCE.md).
The shared bearer middleware is not a substitute for user identity and per-account
authorization. The demo session flow is not bank/customer identity verification.
CORS production defaults now deny browser origins unless
`FINAI_CORS_ALLOW_ORIGINS` is explicitly configured.

Do not mark the integration complete until the full regression suite, frontend
build/lint, local API smoke checks, and deterministic benchmarks have actually
run and their logs have been reviewed. The latest recorded CI failure had no
assigned runner and no steps, so it is not evidence of passing or failing
application tests. CI repair is tracked separately.
