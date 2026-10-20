# Adaptive Task-Aware LLM Routing and Novelty Roadmap

## What is being added

FinAI already has a model registry, deterministic ModelRouter, resource checks,
network/privacy constraints, and provider fallback. The task-aware layer selects
a capability profile from the intent, source type, and request wording, then
delegates all model eligibility decisions to that existing policy router.

The initial task profiles are:
- Complex financial reasoning: systemic/portfolio risk, counterfactuals, stress
  tests, financial research and scenario analysis.
- Evidence-grounded document QA: retrieval evidence, KYC/document tasks.
- Financial explanation: explain/summarize requests.
- Financial QA: known finance-question intents.
- General response: other requests.

The selector is deterministic and auditable. It is not a trained model and
does not claim that any provider is empirically best. Language is recorded and
passed to the selected adapter, but does not change ranking until FinAI has
measured per-language quality. Privacy, offline mode, provider allow-lists,
hardware fit and explicit-model constraints remain owned by ModelRouter.

## Novelty candidates (ranked by research value and feasibility)

### 1. Evidence-Gated, Feasibility-Certified Counterfactual Stress Testing
**Priority: highest research candidate; validation required.** Build on the
existing EPCRP and feasibility-pruning prototypes. Generate counterfactual
financial shocks only when required evidence and graph edges meet declared
quality thresholds; certify prefix feasibility within the stated model class;
then compare the resulting stress scenarios against unconstrained generation,
static shocks, and conventional portfolio stress tests. Report false-feasible
rates, constraint violations, tail-risk coverage, calibration, runtime, and
rolling out-of-time results. Do not claim general causal discovery: current
prototypes use caller-supplied graph structure and model-class-limited checks.

### 2. Verifier-Gated Adaptive Escalation
After a first response, use FinAI's response/evidence verifiers to decide whether
to accept, retrieve more evidence, ask for clarification, or escalate to a
stronger eligible model. Optimize the escalation threshold on held-out tasks
against answer quality, unsupported-claim rate, latency, and cost. Avoid
unmeasured self-confidence as the sole signal.

### 3. Evidence Conflict and Time-Validity Graph
Represent each retrieved financial claim with source, publication/effective
time, jurisdiction, entity, and confidence metadata. Detect conflicting or
stale claims and abstain or request current authoritative evidence. Evaluate
conflict detection precision/recall and stale-answer rate on a curated benchmark.

### 4. Multilingual Financial Consistency Benchmark
Create paired English/Tamil/Telugu/Kannada/Malayalam prompts with identical
verified numerical facts. Measure semantic consistency, numeric preservation,
refusal quality, and financial terminology accuracy across supported models.
Use results to populate per-language model quality metadata and make routing
evidence-based rather than relying on model-brand assumptions.

### 5. Privacy-Budgeted Hybrid Inference
Add field-level data minimization and explicit sensitivity labels. Route restricted
data locally, redact unnecessary identifiers before cloud inference when policy
permits, and log only privacy-safe routing metadata. Test that secrets and
restricted fields never cross the provider boundary in offline/restricted modes.

### 6. Reproducible Model-Routing Arena
Replay a fixed, versioned evaluation set against eligible models; record answer
quality, verifier pass rate, cost, latency, language, and provider failures.
Use conservative thresholds and drift checks to update routing weights only
after review. Keep a deterministic fallback policy if the evaluator is down.

## Recommended sequence

1. Merge and test the task-aware routing layer only after the existing CI failures
   are understood; test privacy/offline/provider allow-list constraints first.
2. Add structured routing telemetry and a reproducible model-routing benchmark.
3. Implement verifier-gated escalation with explicit cost/latency budgets.
4. Run causal-stress baselines and ablations before making publication or patent
   claims.
5. Add multilingual and source-conflict datasets before enabling language-aware
   model rankings.

## Release gates

- No cloud call for offline or restricted-data requests.
- Explicit model requests either satisfy the requested capability and policy or
  fail clearly; they are never silently downgraded.
- Every automatic downgrade records the unavailable preferred capability.
- High/critical-risk reasoning fails closed when no eligible reasoning-capable model is available; it never silently downgrades to generic QA.
- Tests cover deterministic task classification, no eligible model, and privacy
  and network constraints.
- Performance claims require measured held-out results. A feature idea, code
  prototype, or passing unit test alone does not establish novelty or patentability.
