# FinAI Completion Manifest

This manifest describes the repository state intended for the final local pull-and-verify cycle.

## Primary branch

`feature/professional-token-lab-ui`

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
- `POST /api/v1/causal-risk/research-counterfactual`
- Advanced tail-dependence options on the causal-risk tail/counterfactual APIs

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
git pull origin feature/professional-token-lab-ui
pytest -q
```

Then rebuild the frontend:

```powershell
cd frontend
npm run build
cd ..
```

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
