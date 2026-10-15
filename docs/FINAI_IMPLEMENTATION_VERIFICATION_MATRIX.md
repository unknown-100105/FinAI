# FinAI implementation and verification matrix

This is a source-level handoff for the current ai/finai-completion branch. It separates code present from behavior still requiring runtime verification. Do not interpret a source file or synthetic test as proof of a live integration.

## Components added in this completion pass

| Area | Change | What still needs verification |
|---|---|---|
| Trade View | Browser-local watchlist, quote-threshold conditions, position-sizing and reward/risk calculator; responsive styling | TypeScript build, browser selection flow, local-storage persistence, mobile layout, market API failure states |
| Counterfactual stability | Version/evidence/regime-aware directional stability assessment and replay digest | Unit/API tests, auth boundary in the running API, robustness against duplicate or correlated runs, benchmark against baselines |
| API research controls | Stability endpoint stays behind the opt-in research router and its bearer token dependency | Confirm opt-in mount and token behavior in a full app process; never expose publicly without review |
| CI | Added stability unit/API tests to artifact-independent regression list | Hosted runner must execute actual steps; latest code has not been demonstrated green |

## Existing FinAI Brain layers

The branch contains routing, policy/authority/risk controls, deterministic finance tools, hybrid FTS5/FAISS/RRF retrieval, model gateway/provider adapters, response and claim verification, XAI traces, resource/capability planning, and causal-risk research modules.

The capability execution plan currently records request-path diagnostics; it is not a replacement for policy/authority enforcement and is not a standalone tool dispatcher. The existing legacy enforcement paths remain authoritative. End-to-end ordering, failure handling, and per-intent integration must be exercised against a running backend and configured assets.

## Provider and data dependencies

- Cloud model adapters are code paths, not evidence that credentials, quotas, provider availability, latency, or fallback have been verified.
- The local rLLM/embedding paths require their model files and supported hardware/runtime. Optional Colibrì requires a separately installed loopback-compatible server and model; FinAI does not bundle the engine or implement its model-weight streaming.
- RAG builders exist, but source chunks and generated FAISS/SQLite assets must be provisioned for a clean clone.
- Market history/news depend on provider availability and data freshness; a timestamp is not a real-time guarantee.
- ResilientPay remains a local payment-intent journal with a simulation adapter, not live bank settlement or Hyperledger Fabric deployment.

## Causal-risk and patent research

- Bounded linear-DAG feasibility screening and counterfactual directional stability are experimental components.
- The stability gate evaluates repeated estimates supplied by the caller; it does not discover a true causal graph or validate the underlying structural model.
- Synthetic benchmarks are for reproducibility and regression only. They do not establish out-of-distribution performance, real-market utility, novelty, inventive step, or patentability.

## Release checks to run from a clean Windows checkout

1. Pull the current branch and confirm git status is clean before running tests.
2. Install backend dependencies and run the complete Python suite, including the two new counterfactual stability test files.
3. Run scripts/finai_preflight.py and confirm which router/RAG/model artifacts are missing.
4. Run frontend npm ci, npm run build, and npm run lint.
5. Start the API and frontend; run the Trade View manual checklist in docs/TRADE_VIEW_TOOLS.md and test multilingual assistant requests, model fallback, RAG evidence, XAI traces, and research endpoints.
6. Run scripts/run_patent_mechanism_benchmark.py and benchmarks/counterfactual_screening_benchmark.py.
7. Review all warnings, failures, missing credentials, stale-data conditions, and security assumptions. Do not merge to main until these are resolved or explicitly accepted.

## Non-goals of this branch

No live brokerage/order execution, bank settlement, production user identity/RBAC, tenant isolation, OS-level outbound network sandbox, bundled local model weights, or filing-grade patent opinion is claimed.


## Additional Brain integration

- `GET /api/v1/system/brain-status` exposes a secret-safe local readiness view for routing, policy/authority, deterministic finance, retrieval assets, model credential presence, verification/XAI, adaptive orchestration, and experimental causal research.
- The Assistant UI fetches this endpoint and replaces hard-coded positive RAG/evidence indicators with status labels derived from the API response.
- Each assistant request can also display its backend-generated `capability_execution_plan`, including planned stages, dependencies, and explanations. The plan remains diagnostic and does not authorize tools or guarantee stage success.


- The capability plan now attaches observed outcomes per planned step (policy, finance, retrieval, generation, and verification) plus the top-level observed request outcome/stage. These fields are retrospective diagnostics; they do not cause the planner to dispatch or authorize tools.

- The readiness endpoint also distinguishes offline-mode configuration and Colibrì adapter configuration from actual local model-weight presence, server reachability, and successful inference; those runtime checks remain explicitly unverified.
