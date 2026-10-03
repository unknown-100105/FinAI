# FinAI Final Research Architecture

## Unified system

```
Market / Macro / News / Filings / Events / Entities / Portfolio
                         |
                         v
              Typed Multimodal Graph
                         |
             +-----------+-----------+
             |                       |
      Causal Discovery        Temporal GNN
      NOTEARS + lagged            |
             |                       |
             +-----------+-----------+
                         v
                 Consensus Graph
                         |
                 Empirical Calibration
                         |
                  Explicit Gate
                         |
               Structural Causal Model
                         |
             +-----------+-----------+
             |                       |
       Correlation-aware        GFlowNet
       tail sampler             prototype
             |                       |
             +-----------+-----------+
                         v
                 Counterfactual Engine
                         |
               Neuro-symbolic Rules
                         |
                    Causal XAI
                         |
               Risk / Portfolio UI
```

## Research-status semantics

A component may be implemented without being statistically validated. FinAI must distinguish:

- implemented
- research baseline
- research prototype
- trained
- empirically validated
- production eligible

No language-model response is allowed to override a failed symbolic constraint or an unapproved research graph.

## Validation requirements

Every learned component must preserve chronological evaluation, deterministic seeds where practical, explicit provenance, and a clear distinction between prediction, association, and causal identification.
