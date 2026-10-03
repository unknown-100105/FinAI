# FinAI Finish Line 2 — Experimental Execution Plan

Status: implementation-ready research protocol.

## Objective

Demonstrate, using point-in-time data and future-only evaluation, whether FinAI's full causal-regime-constrained stress-generation loop improves scenario validity and/or computational efficiency relative to defined baselines.

## Phase A — Dataset

Required columns should include timestamped versions of available factors and outcomes.

Minimum metadata:
- source;
- observation timestamp;
- publication/event timestamp where applicable;
- timezone convention;
- license;
- missingness;
- transformation;
- data-freeze/fingerprint.

Hard rule: no information published after the prediction timestamp may enter that row.

## Phase B — Chronological splits

Use fixed:
- training interval;
- validation interval;
- future test interval.

Then repeat with rolling-origin windows.

Record:
- split boundaries;
- random seed;
- model/configuration version;
- graph-construction version.

## Phase C — Causal discovery

Run:
- NOTEARS;
- lagged discovery;
- stability windows;
- consensus.

Evaluate:
- edge stability;
- sign consistency;
- synthetic graph recovery where ground truth exists;
- scale sensitivity;
- omitted-variable perturbation;
- lag sensitivity.

Do not interpret discovery as causal identification without assumptions.

## Phase D — Empirical calibration

Fit channel coefficients only on earlier observations.

Evaluate on later observations.

Record:
- coefficient bundle version;
- train/test metrics;
- condition number;
- bootstrap intervals;
- leakage checks.

## Phase E — Temporal model

Run rolling future-holdout temporal GNN/TGAT experiments.

Compare against simpler baselines.

Report:
- MAE;
- RMSE;
- calibration where defined;
- performance by regime;
- temporal drift.

## Phase F — Tail generation

Compare:
A. independent Gaussian;
B. empirical-correlation Gaussian;
C. Student-t copula;
D. unconstrained GFlowNet-style generator;
E. causal empirical reward generator;
F. causal-feasibility constrained generator;
G. adaptive causal-feasibility generator.

Use identical test periods.

## Phase G — Scenario quality

Measure:
- historical-support distance;
- causal-consistency rate;
- regime consistency;
- diversity;
- duplicate/degenerate rate;
- tail coverage.

## Phase H — Patent mechanism benchmark

Primary comparison:

### Baseline
Every candidate prefix is expanded and subjected to full structural/tail evaluation.

### Proposed
Every candidate next action receives:
1. hard bound check;
2. conservative causal reachable-set certificate;
3. optional empirical-support check;
4. optional adaptive budget filtering;
5. full structural/tail evaluation only after survival.

Measure:
- candidate prefixes;
- full SCM evaluations;
- avoided evaluations;
- wall-clock runtime;
- peak memory;
- compute utilization;
- high-risk recall;
- false-pruning rate.

## Phase I — Incremental certificate benchmark

Compare:
A. full interval propagation after every action;
B. descendant-cone incremental interval update.

Measure:
- node interval evaluations;
- runtime;
- exact-match rate between implementations.

## Phase J — Ablation

Run the following with identical splits/seeds:

1. market-only;
2. multimodal without causal constraints;
3. causal without GFlowNet;
4. GFlowNet without causal constraints;
5. regime-aware without multimodal;
6. hard certificate only;
7. hard certificate + adaptive pruning;
8. incremental certificate + adaptive pruning;
9. full FinAI.

## Phase K — Robustness/OOD

Perturb:
- feature scale;
- noise;
- missing modalities;
- graph edges;
- correlation;
- event timing;
- regime boundary.

Record graceful degradation or deterministic rejection.

## Phase L — Acceptance criteria

A result can be called empirically supported only when:

1. the dataset is point-in-time and frozen;
2. future-only test intervals are used;
3. all baselines are evaluated on identical test periods;
4. uncertainty/statistical procedures are specified;
5. no-pruning and pruning systems are compared;
6. false-pruning/high-risk recall are quantified;
7. ablations identify which mechanisms contribute;
8. failure cases are documented;
9. experiment artifacts are reproducible from a source commit and dataset fingerprint.

## Patent-specific decision gate

Proceed to a formal invention disclosure review only when the pruning mechanism demonstrates:

- reproducible reduction in expensive computation;
- measurable resource effect;
- quantified high-risk trajectory recall;
- low and documented false-pruning rate;
- a specific technical difference from the closest prior-art disclosures.

No performance threshold should be invented in advance. The threshold must be selected in the study design and reported before the result is interpreted.
