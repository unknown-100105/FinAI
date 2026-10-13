# FinAI: Remaining Layers and Research Novelty Plan

## Repository-grounded assessment

This plan is based on the accessible `ai/finai-completion` branch. It is not a claim that every feature is production-ready.

### Existing foundation to preserve
- Multilingual intent routing, policy/authority checks, deterministic finance tools.
- Hybrid retrieval (FTS5/FAISS) and response/claim verification.
- Model gateway/provider fallback, local model adapters and resource-aware execution planning.
- Causal-risk research stack: NOTEARS research baseline, linear SCM interventions, tail samplers, trainable TGAT-style model, multimodal graph/encoder, GFlowNet-style stress generation.
- Experimental EPCRP evidence-gated paired-world propagation.
- Bounded linear-DAG counterfactual feasibility screening with forward/backward interval checks and certificates.
- Session authentication/confirmation for sensitive chat actions.

### Integration and verification gaps
1. The execution plan is currently diagnostic/planning infrastructure; verify that the real request path consistently enforces its required stages rather than merely reporting a plan.
2. Shared API authentication and authorization are not equivalent to chat-session authentication. Audit every non-health route, then add a default-deny production access policy with an explicit local-development mode.
3. Validate end-to-end Trade View with provider timestamps, freshness labels, market/news evidence provenance, and graceful handling of unavailable data.
4. Run the entire test suite, frontend build/lint, and live API smoke tests on the exact final branch. The latest hosted CI run reported failure before any steps were recorded; its cause remains unresolved and should not be treated as a code-test failure.
5. Real-data causal calibration, strict point-in-time leakage checks, rolling future-only evaluation, crisis/OOD tests, and ablations remain data-dependent.
6. Colibrì is an optional compatibility adapter; do not describe it as native weight streaming or a validated runtime without a live provisioned server test.
7. ResilientPay still requires separate validation for distributed/offline double-spend safety, real Fabric/bank settlement, production identity/session controls, and failure recovery.

## New research layer added in this branch

### Counterfactual Directional Stability Gate (CDSG)

The gate compares repeated estimates for the *same intervention and metric* across approved model versions, causal-graph fingerprints, evidence snapshots, and regimes.

It returns one of:
- `DIRECTION_STABLE`: every approved run has an interval strictly on the same side of zero.
- `MODEL_OR_EVIDENCE_SENSITIVE`: decisive runs disagree in direction or do not meet the configured agreement threshold.
- `INDETERMINATE_INTERVALS`: at least one approved interval touches or crosses zero.
- `INSUFFICIENT_APPROVED_RUNS`: too few approved runs are available.

It records a deterministic replay digest and provenance fingerprints. Unapproved runs are excluded from support for a conclusion. The layer is research-only and must not turn stability into a claim of causal identification or investment advice.

### Novelty hypothesis—not a novelty claim

A potentially publishable contribution is a *counterfactual stability gate that conditions downstream financial explanations on directional robustness across versioned causal graphs, evidence snapshots, and regimes*, with explicit abstention states and a replayable provenance manifest.

The hypothesis must be compared against:
- single-model/single-graph counterfactual estimates;
- simple sign-voting ensembles;
- uncertainty-interval-only abstention;
- evidence freshness/conflict filters without stability gating.

Measure false-stability rate on synthetic ground-truth SCMs, abstention/coverage trade-off, directional error, sensitivity to graph perturbation and stale/missing evidence, and added latency. Use multiple graph sizes and realistic time-series-derived scenarios. The gate is useful only if it reduces confidently wrong directional conclusions at a tolerable abstention rate.

Do not claim this is novel or patentable until a targeted literature and patent search compares the exact mechanism with prior art.

## Recommended implementation order

1. **Security:** shared API auth and route-by-route authorization audit; retain health checks as explicitly public.
2. **Brain integration:** make capability-state, policy, risk, tool selection, retrieval, verification and resource planning a tested decision path—not a parallel diagnostic.
3. **Counterfactual stability gate:** added here as a research-only primitive; next integrate into the causal-risk research API and XAI explanation contract after local tests.
4. **Trade View:** add timestamp/freshness-aware data, news provenance, indicators, watchlists, alerts and AI analysis backed by actual providers.
5. **Research validation:** point-in-time datasets, rolling-origin evaluation, baselines, ablations, OOD/crisis tests, calibration and cost/latency benchmarks.
6. **Release validation:** resolve hosted CI availability, run full backend tests and frontend build/lint, then smoke-test live APIs.

## Acceptance criteria

- Every stability result includes its status, run count, provenance fingerprints and replay digest.
- An interval crossing zero can never be labelled directionally stable.
- Unapproved runs cannot support a stable result.
- Repeated input order does not change the replay digest.
- The feature is clearly marked experimental and is not wired to live order execution.
- No patent, novelty, or real-market performance claim is made without the corresponding search and empirical evidence.
