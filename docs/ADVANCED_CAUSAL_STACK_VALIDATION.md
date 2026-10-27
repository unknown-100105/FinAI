# Advanced causal stack: validation and completion gates

This document describes the advanced research modules in FinAI and the checks
required before treating them as reliable financial analytics.

## Run the deterministic smoke validator

From the repository root, in the configured FinAI virtual environment:

```powershell
python scripts/validate_advanced_causal_stack.py
```

The script emits a JSON report and exits non-zero if any check fails. It covers:

- risk-target calibration with a chronological holdout;
- the end-to-end causal research pipeline;
- a small temporal risk GNN training smoke test;
- GFlowNet training and scenario sampling;
- Student-t copula scenario reproducibility with a fixed seed.

The input data is generated synthetically with fixed seeds. The report deliberately
sets `causal_identification_established`, `market_prediction_validated`, and
`production_eligible` to false. A successful smoke test demonstrates executable
software paths, not financial validity.

## Existing API surface

The advanced research router is mounted from `app/advanced_causal_api.py` under
`/api/v1/causal-risk`. Relevant operations include:

- `POST /risk-calibration`
- `POST /risk-calibration/fit-channels`
- `POST /gfnets/train` and `POST /gfnets/generate`
- `POST /multimodal/train`, `POST /multimodal/encode`, and multimodal ingestion
- temporal GNN training and the broader causal-risk research endpoints

Use `GET /docs` on the running local API to inspect the schemas actually exposed
by the selected branch. Training operations may use in-memory models; a successful
training response must not be interpreted as a persisted, deployable model.

## Required gates before using real market data

1. **Data lineage:** retain source, timestamp, units, frequency, timezone,
   transformations, missing-value handling and revision policy for each input.
2. **Leakage control:** split strictly by time; fit preprocessing and calibration
   on training data only; never use future labels/features to construct past states.
3. **Baseline comparison:** compare against naive, linear and non-causal baselines
   on identical chronological splits.
4. **Causal assumptions:** document the graph, confounders, intervention semantics,
   lag assumptions, graph stability and limits of identification.
5. **Evaluation:** report out-of-sample MAE/RMSE where appropriate, calibration,
   tail-event precision/recall, regime-specific metrics, confidence intervals and
   baseline deltas. Do not report a single aggregate score without its sample count.
6. **Ablations and robustness:** remove modalities/edges, perturb inputs, vary seeds,
   evaluate stress periods and test sensitivity to missing or stale data.
7. **Reproducibility:** archive the code commit, dependency versions, exact input
   snapshot or dataset hash, config, seed, command, report and model artifact hash.
8. **Safety boundary:** label synthetic scenarios and research outputs; do not
   present them as forecasts, investment advice or causal effects established by
   observational data alone.
9. **Artifact lifecycle:** version models, validate loading in a clean process,
   define retention and rollback, and avoid trusting an in-memory registry as
   durable storage.
10. **Deployment gate:** require review of authentication/authorization, rate limits,
    resource ceilings, timeouts, observability, failure handling and security before
    exposing expensive training endpoints beyond a trusted research environment.

## Definition of done

The advanced research stack is ready for a research demonstration only when the
smoke validator passes and the output report is retained. It is ready for empirical
research only after gates 1-7 are completed with real, timestamped data and an
independent reproducible evaluation. It is not production-ready until gates 8-10
and the applicable organization/security review are complete.

Passing unit tests or synthetic smoke checks alone does not establish patent novelty,
causal identification, investment alpha, regulatory compliance or production readiness.
