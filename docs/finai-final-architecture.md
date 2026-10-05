# FinAI Research Architecture v2

## Unified causal stress-intelligence loop

~~~text
Market / Macro / News / Filings / Events / Entities / Portfolio
                         |
                         v
                Multimodal State Encoder
             /       |       |       |      \
        market    macro    text   events   graph/microstructure
                         |
                         v
              Time-Indexed Financial Graph
                         |
              +----------+----------+
              |                     |
       Causal Discovery       Temporal GNN
       NOTEARS + lags        regime-aware encoder
              |                     |
              +----------+----------+
                         v
              Stability + Consensus
                         |
                   Research Gate
                         |
                         v
             Causal Empirical GFlowNet
                         |
             constrained stress paths
                         |
                         v
              Structural Causal Model
                   do(X=x)
                         |
             +-----------+-----------+
             |                       |
       Tail / CVaR / ES          Causal XAI
             |                       |
             +-----------+-----------+
                         v
             Neuro-Symbolic Validator
                         |
             +-----------+-----------+
             |                       |
        Accepted path            Rejected path
             |
             v
         Research metrics
   temporal / regime / OOD / ablation
~~~

## Research contribution hypothesis

FinAI investigates whether **causal-regime-constrained stress generation** can
produce more empirically supported, causally consistent and regime-consistent
financial stress trajectories than unconstrained generative scenario search.

This is a hypothesis to be tested, not a claim of prior-art exclusivity.

## Model maturity semantics

Every learned component has separate states:

- implemented
- trainable
- trained
- future-holdout evaluated
- empirically validated
- production eligible

Training alone never upgrades a model to empirically validated.

## Core upgrades

### Empirical channel calibration

The repository now contains a calibration path that can estimate the exact
coefficient schema consumed by the structural risk engine from chronological,
externally observed channel outcomes.

The resulting bundle is explicitly marked empirical_fit and can be selected
through FINAI_RISK_CALIBRATION_PATH after human review.

### Causal empirical GFlowNet

The GFlowNet objective can now be replaced with an explicit research reward
combining:

- tail severity;
- empirical-support proximity;
- causal-direction alignment;
- portfolio relevance.

The generator remains a research generative model until trained and
benchmarked on a real point-in-time financial dataset.

### Temporal holdout training

TemporalRiskGNN now has a sequence training path that fits only on earlier
snapshots and evaluates on future snapshots. The implementation exposes CPU,
CUDA and automatic device selection with deterministic seeds.

### Learned multimodal encoder

A trainable multimodal financial encoder now supports:

- modality-specific projections;
- learned modality tokens;
- missing-modality embeddings;
- Transformer fusion;
- masked-modality self-supervision;
- embedding inference.

This is a research-scale encoder, not a claim of foundation-model pretraining.

## Scientific boundaries

- Observational causal discovery is not causal identification by itself.
- GFlowNet reward is not a calibrated probability distribution.
- Student-t copula generation is not a GFlowNet.
- Temporal holdout performance is not evidence of causal identification.
- Embedding similarity is not factual or causal proof.
- Real production deployment requires point-in-time data, artifact versioning,
  security hardening and external validation.

## Required final experiments

1. Historical point-in-time dataset construction.
2. Walk-forward TGAT evaluation.
3. Empirical channel calibration.
4. Causal-empirical GFlowNet training.
5. Multimodal masked-modality pretraining.
6. Tail-risk backtesting.
7. Crisis/regime robustness.
8. Ablation study.
9. Out-of-distribution perturbation testing.
10. Prior-art and patent review.

See docs/research-gap-and-novelty.md and
docs/research-training-runbook.md.

## Multi-cloud model intelligence layer

The language-model layer is provider-agnostic. FinAI currently supports Google Gemini, OpenAI, OpenRouter, Anthropic and Mistral adapters plus local/research models. A deterministic ModelRouter selects an eligible model by capability and risk-aware policy metadata and records an auditable fallback chain.

This layer sits below the financial authority/policy boundary and above the response verification/XAI boundary. Cloud LLMs generate explanations around system-owned calculations, retrieved evidence and other verified results; they do not become the authority for transactions or financial calculations.

The frontend Model Intelligence workspace exposes the model registry, credential configuration state and route preview without invoking a paid model call.

The routing policy is intentionally labeled as a heuristic. It is not a learned benchmark and requires empirical provider evaluation before any model is declared universally best.
