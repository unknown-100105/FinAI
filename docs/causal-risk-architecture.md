# FinAI Causal Risk & Counterfactual Architecture

## Purpose

FinAI's causal-risk layer adds a research workspace for directed systemic-risk propagation and portfolio counterfactuals. It complements the existing RAG, model, policy and market-analysis layers rather than replacing them.

## Current implementation

### Structural causal graph

The repository contains an explicit directed graph covering:

`rates -> credit -> liquidity -> equity -> portfolio`

with additional USD/INR, energy and supply-chain pathways.

### Intervention semantics

Counterfactual runs use an explicit intervention contract:

`P(Y | do(X=x))`

Intervened variables are fixed and downstream effects are propagated through structural equations.

### Causal discovery

`causal_risk/discovery.py` contains a compact NOTEARS-linear augmented-Lagrangian implementation.

`causal_risk/dynamic_discovery.py` contains a lagged temporal discovery baseline for time-series data.

These components are research implementations and require empirical validation before being used as authoritative causal claims.

### Temporal GNN

`causal_risk/temporal_gnn.py` provides a compact TGAT-style temporal attention architecture. It is an architecture module, not a trained production model.

### Tail scenarios

`causal_risk/tail_scenarios.py` provides a reproducible Monte-Carlo tail-scenario baseline and an explicit GFlowNet-ready interface. A trained GFlowNet is not currently claimed.

### Explainability

Causal XAI reports structural paths and edge contributions. This is intentionally distinct from post-hoc feature attribution.

## API

- `GET /api/v1/causal-risk/graph`
- `GET /api/v1/causal-risk/architecture`
- `POST /api/v1/causal-risk/counterfactual`
- `POST /api/v1/causal-risk/discover/notears`
- `POST /api/v1/causal-risk/discover/dynamic`
- `POST /api/v1/causal-risk/tail-scenarios`

## Research progression

1. Empirical data contract for macro, market, news and supply-chain modalities.
2. Constrained DAG discovery with domain priors and stability selection.
3. Temporal graph training and walk-forward validation.
4. Structural causal estimation and uncertainty intervals.
5. Calibrated synthetic tail generation.
6. Knowledge-graph relation extraction and evidence provenance.
7. Neuro-symbolic constraint evaluation.
8. OOD, counterfactual-consistency and stress-test benchmarks.

## Evaluation principles

Do not treat a high predictive score as proof of causality. Every learned edge should expose:

- training population and time window
- data source
- discovery method
- regularization
- stability across resamples/windows
- evidence links where available
- uncertainty / sensitivity
- whether the result is observational or interventionally identified
