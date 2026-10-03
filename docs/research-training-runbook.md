# FinAI Research Training Runbook

This runbook is the bridge from implemented research code to measured research
results. It intentionally requires the repository owner to provide or approve
the datasets and promote trained artifacts.

## 1. Point-in-time dataset contract

Every observation must carry an event/observation timestamp. Features available
after the prediction timestamp must not enter the corresponding row.

Recommended factor groups:

- market: returns, volatility, volume, spreads
- macro: policy rates, inflation, growth, FX, commodities
- credit: credit spreads, funding indicators
- events: timestamped macro announcements and corporate events
- text: timestamped filing/news embeddings
- entities: issuers, sectors, supply-chain links
- portfolio: timestamped exposures
- microstructure: bid/ask depth, spread, imbalance

Maintain a manifest containing source, timestamp convention, license, missingness,
and transformation for every dataset.

## 2. Empirical SCM channel calibration

Collect aligned rows containing structural values:

rates, credit, oil, usd, liquidity, equity

and realized outcomes:

equity, debt, gold, portfolio, systemic_stress

Then call:

~~~powershell
$body = Get-Content .\examples\channel_calibration.json -Raw
Invoke-RestMethod -Uri http://127.0.0.1:8000/api/v1/causal-risk/risk-calibration/fit-channels -Method Post -ContentType "application/json" -Body $body
~~~

Review the returned coefficients, chronological test metrics and diagnostic
metadata.

Save the reviewed JSON bundle locally, then set:

~~~powershell
$env:FINAI_RISK_CALIBRATION_PATH="configs/causal_risk_calibration_empirical.json"
~~~

Do not overwrite the research-default configuration until the empirical bundle
has been reviewed and versioned.

## 3. Temporal GNN

Build time-sliced graph snapshots with identical node/feature dimensions.

Call:

POST /api/v1/causal-risk/temporal-gnn/train

The endpoint requires at least five snapshots and performs a chronological
future holdout.

For publication-quality experiments, use multiple rolling origin splits and
store:

- training period;
- validation period;
- future test period;
- random seed;
- model hyperparameters;
- graph construction method;
- missing-feature treatment;
- MAE/RMSE/calibration results.

## 4. Causal empirical GFlowNet

For each factor set compute:

- empirical center;
- empirical marginal scale;
- optionally the inverse correlation matrix;
- a research graph matrix representing candidate causal directions;
- portfolio relevance weights.

Call the GFlowNet training endpoint with reward_mode=causal_empirical.

The returned registry is in-memory only. For durable experiments, save:

- model state dict;
- training configuration;
- dataset fingerprint;
- graph fingerprint;
- reward specification;
- seed;
- final and rolling training diagnostics.

A trained loss alone is not evidence that generated scenarios are realistic.

## 5. Multimodal encoder

Prepare aligned matrices for any subset of:

market, macro, text, event, entity, portfolio, microstructure

with equal sample count.

Call:

POST /api/v1/causal-risk/multimodal/train

The objective is masked-modality reconstruction plus representation consistency.

Evaluate:

- complete-modality embedding;
- each single-modality-missing condition;
- multiple-missing conditions;
- downstream risk prediction;
- representation drift over time.

## 6. Tail-risk backtesting

Compare at minimum:

- independent Gaussian baseline;
- empirical-correlation Gaussian;
- Student-t copula;
- causal empirical GFlowNet.

Use the same historical test periods and compare:

VaR coverage, CVaR/expected-shortfall error, exceedance clustering,
scenario diversity, historical-support distance, and regime robustness.

## 7. Ablation protocol

Run:

A. market-only
B. market + multimodal
C. multimodal without causal constraints
D. causal graph without GFlowNet
E. GFlowNet without causal constraints
F. regime-aware model without multimodal evidence
G. full FinAI

Keep data splits, seeds and evaluation metrics identical.

## 8. OOD and adversarial evaluation

Perturb:

- feature scale;
- missing modalities;
- graph edges;
- event timing;
- noise level;
- factor correlations;
- regime boundaries.

Verify that the system either degrades gracefully or rejects invalid inputs
rather than silently producing authoritative-looking results.

## 9. Artifact promotion

Every trained artifact should have:

- model name and version;
- source commit SHA;
- dataset fingerprint;
- training timestamp;
- hyperparameters;
- seed;
- evaluation split;
- metric report;
- known limitations.

Do not commit large model weights to normal source control unless repository
policy explicitly permits them.

## 10. Final publication package

A reproducible research package should contain:

- problem statement;
- research-gap matrix;
- dataset card;
- model card;
- benchmark protocol;
- ablation table;
- robustness results;
- failure cases;
- architecture diagram;
- exact training command;
- source commit;
- artifact identifiers;
- prior-art/patent review.

Only after this package is complete should FinAI make a specific novelty claim.
