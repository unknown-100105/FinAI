# FinAI Patent and Research Strategy — 2026-10-03

## Purpose

This document separates:
1. engineering implementation,
2. empirical research validation, and
3. patent-positioning work.

It is not a legal opinion or a guarantee of patentability. Patentability depends on jurisdiction-specific examination, claim drafting, prior art, disclosure timing, inventorship, and other facts.

## Current patent-position assessment

FinAI can be developed toward a patent application, but the broad idea of:
- multimodal financial data,
- causal graph construction,
- causally constrained generation,
- counterfactual validation,
- financial stress testing,
- graph pruning,
- GFlowNet constraints, or
- FPGA-based financial risk controls

is not by itself a sufficiently differentiated invention concept.

The working patent hypothesis should therefore be a specific computational mechanism with a measurable technical effect.

## High-risk prior-art overlaps identified

### 1. Causality + multimodal + constrained generation

US20260073260A1, published 2026-03-12, has a priority date of 2025-11-17 and is pending according to Google Patents. Its disclosure includes heterogeneous/multimodal ingestion, a dynamically evolving causal representation, fused latent representations, causally constrained generative reasoning, counterfactual validation, causal traceability, and financial use as one supported domain.

FinAI must not treat "causal + multimodal + generative + counterfactual" as an exclusive novelty claim.

Reference:
https://patents.google.com/patent/US20260073260A1/en

### 2. Financial generative stress testing

CN121146937A, published 2025-12-16, describes financial stress testing using heterogeneous data, an asset-relation graph, a conditional graph generative adversarial network, Bayesian parameterization, simulated financial performance, and risk indices.

Reference:
https://patents.google.com/patent/CN121146937A/en

### 3. Constrained GFlowNet optimization

WO2025067134A1 describes constrained generative-flow training, including constraint terms in the loss, flow constraints, loop penalties, and reducing sampling/training effects.

Reference:
https://patents.google.com/patent/WO2025067134A1/en

### 4. Hardware financial-risk filtering

US8751364B2 describes wire-speed monitoring/control of electronic financial transactions using reprogrammable integrated-circuit hardware to parse incoming orders, evaluate risk criteria, and permit or truncate orders.

Reference:
https://patents.google.com/patent/US8751364B2/en

### 5. Causal graph pruning for computational efficiency

CN120688647B describes causal-graph clustering/pruning followed by GNN processing to reduce computational complexity.

CN121562930A describes causal DAG pruning, weak-edge removal and lag-order limits to reduce model complexity and improve computational efficiency.

References:
https://patents.google.com/patent/CN120688647B/en
https://patents.google.com/patent/CN121562930A/en

## Refined FinAI patent hypothesis

### Working title

**Causal-Feasibility Feedback and Adaptive Search-Space Pruning for Generative Financial Stress Trajectories**

### Core technical mechanism

Instead of claiming a generic causal generative finance system, FinAI should investigate a staged computation architecture:

1. Build a point-in-time financial state from market, macro, event, text, portfolio and graph inputs.
2. Obtain a research-approved causal graph and associated intervention bounds.
3. A generative trajectory engine proposes partial stress trajectories one factor/action at a time.
4. A low-cost prefix feasibility evaluator computes a causal-feasibility certificate using:
   - currently reachable downstream bounds from the SCM,
   - graph direction constraints,
   - empirical-support distance/correlation constraints,
   - intervention-envelope constraints,
   - portfolio relevance bounds.
5. Candidate actions that cannot reach an admissible terminal stress region are masked before expensive full SCM propagation.
6. Only surviving prefixes receive full structural propagation and tail-risk evaluation.
7. The resulting causal residual / feasibility gap feeds back into the generative reward.
8. The pruning threshold is adapted from observed acceptance rate and a compute budget while preserving a configurable recall floor for high-risk admissible trajectories.
9. Every pruning decision is logged with the certificate inputs, threshold, reason, and downstream validation result.

### What makes this a research hypothesis

The proposed contribution is not the individual use of SCM, GFlowNet, graph pruning, or financial stress testing. It is the possible closed-loop interaction between:

**incremental trajectory state -> cheap causal-feasibility certificate -> action masking -> expensive SCM only for feasible prefixes -> empirical tail evaluation -> feedback reward -> adaptive pruning**

The invention hypothesis must be tested experimentally before using it as a patent novelty claim.

## Required technical-effect evidence

Measure the candidate system against an equivalent full-evaluation baseline using the same data and random seeds.

Record:

- total candidate prefixes;
- number of full SCM evaluations;
- percentage of evaluations pruned;
- wall-clock latency;
- peak CPU memory;
- peak GPU memory where applicable;
- GPU/CPU utilization;
- high-risk trajectory recall;
- false-pruning rate;
- terminal scenario diversity;
- causal-constraint violation rate;
- empirical-support violation rate;
- tail-risk metric error;
- reproducibility across seeds.

A patent-oriented experiment should demonstrate that pruning reduces computational workload while retaining an explicitly measured fraction of valid high-risk trajectories.

## Finish-Line-2 research protocol

### Dataset

Use point-in-time data with:
- market prices/returns/volatility/volume;
- macroeconomic releases and timestamps;
- credit/funding indicators;
- timestamped news/filing/event representations;
- entity/sector relationships;
- timestamped portfolio exposures;
- microstructure features when available.

No future information may enter a prediction or training row.

### Baselines

At minimum:

A. independent Gaussian scenario sampler
B. empirical-correlation Gaussian
C. Student-t copula
D. unconstrained GFlowNet-style generator
E. causal-reward GFlowNet without pruning
F. causal-reward generator with fixed pruning
G. proposed adaptive causal-feasibility pruning loop

### Primary metrics

Prediction:
- MAE
- RMSE
- calibration error

Tail risk:
- VaR coverage
- CVaR / expected-shortfall error
- exceedance clustering

Scenario quality:
- empirical-support distance
- causal-consistency rate
- regime-consistency rate
- diversity
- duplicate/degenerate trajectory rate

Technical efficiency:
- full SCM evaluations saved
- latency
- memory
- compute utilization

### Ablation

Remove exactly one mechanism at a time:

- no multimodal state;
- no causal graph;
- no empirical-support term;
- no regime conditioning;
- no causal reward;
- no prefix certificate;
- no adaptive threshold;
- full FinAI loop.

Use identical time splits and seeds.

## Patent drafting structure to investigate

The specification should describe:
- system components;
- memory and processor architecture;
- input data structures;
- time-indexing rules;
- graph representation;
- intervention envelope representation;
- prefix feasibility certificate;
- action-masking mechanism;
- adaptive threshold controller;
- feedback/reward calculation;
- logging/audit structure;
- alternative implementations;
- CPU/GPU/distributed execution;
- measured computational effects.

Potential claim categories for attorney review:
1. computer-implemented method;
2. system including processor and memory;
3. non-transitory computer-readable medium.

Do not restrict the disclosure to one programming language or one specific ML library.

## Legal-positioning notes

### United States

USPTO guidance does not establish a categorical rule that all software or business methods are unpatentable. Eligibility is claim-specific. AI guidance focuses on whether the claimed subject matter falls within an exception and, where relevant, whether it is integrated into a practical application.

### Europe

The EPO's 2026 guidance states that AI/ML models are mathematical in nature but may contribute to technical character when they are part of a technical solution to a technical problem. The EPO also recognizes further technical effects such as improvements to computer functioning or computational efficiency when properly established.

### India

India currently publishes 2025 CRI guidelines for examination of computer-related inventions. The framework addresses Section 3(k) and the distinction between excluded computer programs/algorithms and eligible technical contributions. A patent professional should map the final claim language to the current Indian CRI rules and case law.

### Filing sequence

India permits an application with a provisional specification, followed by a complete specification within 12 months.

A U.S. provisional application lasts 12 months and can establish an early U.S. filing date.

A PCT international application generally should be filed within 12 months of the earliest priority application to claim that priority.

## Disclosure control

Before publicly publishing the exact inventive mechanism, paper, source code, architecture diagram, thesis text, demo video, or detailed presentation, obtain patent counsel's advice on filing order and priority.

Keep the inventive implementation and experimental records versioned and timestamped.

## Current status

- Engineering stack: implemented and locally verified.
- Local regression: 467 passed.
- Frontend build: passed.
- Live API smoke tests: passed.
- Empirical research validation: not yet completed.
- Patent novelty: not established.
- Prior-art review: initial search completed; deeper claim-by-claim search required.
- Patent filing: requires a patent professional to review the actual invention disclosure and inventorship.

## Next execution order

1. Independent Gemini code/research audit.
2. Resolve GitHub CI failure on commit 31fd118.
3. Freeze an engineering baseline.
4. Build the point-in-time dataset and dataset card.
5. Implement/verify the prefix feasibility + adaptive pruning prototype.
6. Run baseline and ablation experiments.
7. Run tail-risk, regime and OOD evaluation.
8. Quantify computational savings and valid-scenario recall.
9. Conduct a broader patent-family and non-patent-literature search around the exact mechanism.
10. Prepare an invention disclosure for review by a qualified patent professional.
