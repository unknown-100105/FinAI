# FinAI causal-risk novelty and validation protocol

## Purpose and status

This document turns the proposed research contribution into a falsifiable evaluation plan. It is **not** a claim that novelty, causal validity, publication readiness, or patentability has already been established. Those conclusions require a documented prior-art search, implementation audit, and measured results.

## Candidate contribution

**Working name:** Evidence-Gated, Feasibility-Certified Counterfactual Stress Testing (EGFC).

**Research question:** Can a financial stress-testing pipeline generate portfolio-relevant counterfactual scenarios that (a) respect a declared causal model and hard domain constraints, (b) remain empirically plausible, and (c) explain the path from an intervention to portfolio impact better than correlation-only or unconstrained scenario generators?

The candidate is a *system mechanism*, not simply the use of an LLM, graph neural network, structural causal model, or generative model in isolation:

1. **Evidence gate:** Each proposed intervention and causal edge must be tied to timestamped evidence or explicitly marked as an expert/prior assumption. Evidence provenance and uncertainty are retained.
2. **Causal intervention:** Represent a scenario as an intervention on a named variable in a structural causal model (SCM), rather than changing correlated features without distinguishing intervention from observation.
3. **Feasibility certification:** Before a scenario is admitted to downstream portfolio analysis, check structural constraints, domain bounds, temporal availability, and graph consistency. Reject or label scenarios that fail; do not silently repair them.
4. **Portfolio-conditioned stress generation:** Rank or generate scenarios using an explicitly documented portfolio relevance / tail-risk objective. Keep the reward definition separate from the feasibility gate.
5. **Traceable explanation:** Return the intervention, affected causal paths, changed variables, constraint checks, evidence references, uncertainty, and portfolio outcome. The language model may verbalize this record but must not invent causal edges or numeric outcomes.

Only call this the implemented contribution if source inspection confirms each stage is wired into the actual execution path. If a stage is a planned design, label it as such.

## Hypotheses to test

- **H1 — Feasibility:** EGFC admits fewer constraint-violating scenarios than an unconstrained generator at a comparable scenario count.
- **H2 — Usefulness:** On a strictly future holdout, EGFC improves stress-loss coverage or tail-risk calibration without materially degrading plausibility.
- **H3 — Explanation fidelity:** Every displayed causal path and numeric impact can be reconstructed from the stored scenario trace and deterministic engine outputs.
- **H4 — Robustness:** The results persist across rolling time splits and reasonable perturbations to graph edges, missingness, and calibration parameters.
- **H5 — Incremental value:** Removing the evidence gate, feasibility gate, causal intervention semantics, or portfolio-conditioned objective measurably degrades at least one pre-registered metric.

A hypothesis is not supported merely because training loss decreases or a generated scenario looks realistic.

## Baselines

Run all baselines with the same point-in-time inputs, portfolio definition, evaluation windows, and scenario budget.

1. **Historical replay:** Resample historical observed windows without causal intervention.
2. **Correlation-only simulation:** Covariance / correlation-based scenario generation, with the same marginal data and portfolio objective.
3. **Unconstrained generator:** The available generative scenario model without feasibility rejection.
4. **SCM without feasibility gate:** Same causal model and interventions, but skip certification.
5. **Full EGFC:** Evidence gate + SCM intervention + feasibility certification + portfolio-conditioned objective + trace.
6. **Simple deterministic stress suite:** A small, documented set of standard shocks, used as a transparent sanity baseline.

Do not compare different baselines on different data windows or with different amounts of tuning.

## Required ablations

Run each ablation independently and report its delta against the full system:

- remove evidence provenance / gate;
- replace interventions with ordinary feature perturbations;
- disable constraint certification;
- remove portfolio relevance from the reward;
- remove temporal graph information (static graph);
- remove explanation trace generation, then measure whether the same result can still be independently reconstructed;
- replace the causal generator with correlation-only simulation.

If a component does not change outcomes or metrics, report that honestly and reconsider whether it is part of the contribution.

## Data and leakage controls

- Use only information available at each scenario's timestamp; store source timestamp, observation timestamp, retrieval timestamp when applicable, and transformation version.
- Split chronologically. Use rolling-origin evaluation and preserve a final untouched test window.
- Fit scalers, imputers, graph discovery, thresholds, and calibration only on the training period of each split.
- Prevent overlapping target windows from crossing split boundaries.
- Record data licensing, coverage, survivorship bias, corporate-action handling, and missingness.
- Keep generated scenarios, training rows, and held-out realized outcomes separately fingerprinted.
- Compare against naive forecasts and simple historical baselines; use block bootstrap or another time-series-aware uncertainty method where appropriate.
- Avoid claiming causal identification from observational correlation alone. Mark assumptions, unidentifiable edges, and sensitivity analyses explicitly.

## Metrics

Report sample counts and confidence intervals, not only a single point estimate.

| Dimension | Required measurements |
|---|---|
| Feasibility | constraint violation rate; rejection rate by reason; rate of invalid / non-finite scenarios |
| Plausibility | marginal and joint distribution distance; tail quantile comparison; temporal dependence diagnostics |
| Risk utility | VaR / expected shortfall coverage and calibration; stress-loss coverage; portfolio loss ranking where outcomes are observed |
| Forecast quality | MAE / RMSE only for genuinely predictive targets; compare to naive baselines |
| Explanation fidelity | fraction of paths reproducible from stored graph and SCM; numerical trace consistency; unsupported-claim rate |
| Robustness | metric spread across rolling splits, seeds, graph perturbations, and missing-data regimes |
| Cost | latency, peak memory, scenario throughput, and cost per accepted scenario |

Metrics must match the task. For example, MAE alone does not establish tail-risk usefulness, and constraint rejection alone does not establish that the accepted scenarios are realistic.

## Minimum reproducibility package

For every experiment, save:

- dataset manifest and cryptographic fingerprint;
- split dates, seeds, code commit, dependency lock / environment;
- model and graph configuration;
- calibration bundle and intervention specification;
- baseline and ablation configuration;
- raw per-split metrics and uncertainty estimates;
- scenario-level outputs, rejection reasons, and trace records;
- exact command / API request used to reproduce the run.

A trained registry that exists only in process memory is not a reproducible artifact. Do not overwrite research defaults with empirical calibration until reviewed and versioned.

## Release gates

Do not describe the method as empirically validated until all are complete:

- [ ] Confirm the full mechanism exists in the executed code path; map each stage to file, function, and test.
- [ ] Define the primary outcome and metrics before inspecting the final holdout.
- [ ] Run all baselines and ablations on identical rolling splits.
- [ ] Demonstrate no timestamp leakage and inspect all rejected/accepted scenario classes.
- [ ] Reproduce explanation traces from stored numerical records.
- [ ] Publish configuration, data provenance, limitations, and failed/negative results.
- [ ] Conduct a documented prior-art search and compare claims against papers, patents, open-source implementations, and financial risk platforms.
- [ ] Have a qualified patent professional review any proposed claims before filing; this document is not legal advice.

## Prior-art and patent discipline

Potentially crowded areas include structural causal models, causal discovery, counterfactual explanations, graph neural networks, generative scenario generation, financial stress testing, and explainable AI. Combining known components does not automatically establish an inventive step. The defensible claim, if any, must be the specific, technically detailed interaction and measurable effect of the mechanism, supported by the implementation and prior-art analysis.

Maintain a claim chart with columns for: proposed claim element, exact implementation location, closest prior-art reference, difference, measured technical effect, and unresolved risk. Do not state “patentable” or “novel” as a conclusion until this chart has been reviewed.

## Current evidence boundary

The repository's research runbook already describes empirical SCM channel calibration, temporal GNN training, causal empirical GFlowNet training, chronological holdouts, and saved diagnostics. These are research workflows, not proof that the hypotheses above pass. The full protocol remains open until fresh experiments, source-to-test mapping, and prior-art review are recorded.
