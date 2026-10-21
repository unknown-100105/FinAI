# Evidence-Gated, Feasibility-Certified Counterfactual Stress Testing for Financial Risk Analysis

**Manuscript status:** working draft for author review; not submission-ready.  
**Target format:** IEEE-style journal/conference manuscript.  
**Author and affiliation:** to be completed by the actual authors.  
**Data/results status:** no empirical result is asserted in this draft. Replace every `[TO REPORT]` field only after executing and independently checking the experiments.

## Abstract

Financial stress-testing systems must construct severe scenarios without confusing unsupported assumptions with observed evidence or admitting scenarios that violate declared model constraints. Existing causal stress-testing research demonstrates the value of representing financial dependencies as causal structures, but the presence of a causal graph alone does not establish evidence quality, scenario feasibility, or empirical calibration. This paper studies an evidence-gated, feasibility-certified counterfactual stress-testing pipeline (EGFC) that separates three decisions: whether a proposed intervention has sufficient timestamped evidence coverage, whether the intervention is feasible under an explicitly declared structural model and bounds, and what portfolio impact follows from the accepted intervention under a deterministic structural causal model (SCM). The implementation checks source attribution, evidence identifiers, timestamp freshness, confidence thresholds, and claim coverage; it then computes a counterfactual impact and screens generated tail scenarios with interval-based feasibility certificates. The framework is designed to fail closed when evidence coverage or feasibility checks fail and to retain rejection reasons for audit. We define a chronological evaluation protocol comparing historical replay, deterministic shocks, unconstrained scenario generation, an SCM without gates, and the full EGFC pipeline, including ablations of each gate. The central empirical question is whether the gates reduce unsupported or constraint-violating scenarios without materially degrading tail-risk coverage, scenario diversity, or explanatory traceability. **The current repository implementation and synthetic smoke benchmark establish a testable mechanism, not empirical superiority or causal identification.** Real-data results, uncertainty estimates, calibrated bounds, and baseline comparisons must be completed before any performance conclusion is drawn.

**Index Terms—** financial stress testing, counterfactual reasoning, structural causal models, evidence provenance, feasibility certification, tail risk, explainable AI, reproducible evaluation.

## 1. Introduction

Stress testing asks how a financial system or portfolio might respond under adverse conditions that may be rare or absent from recent observations. A scenario generator must therefore balance severity with plausibility and make its assumptions inspectable. A scenario that is extreme but structurally impossible is not useful; a scenario supported only by stale or untraceable inputs can also mislead downstream decision-makers.

Prior research has applied causal networks to financial stress testing. Gao, Mishra, and Ramazzotti combine Suppes–Bayes causal networks with machine-learning methods to generate stress scenarios [1]. This line of work establishes that causal structure can be useful for scenario construction, but it does not remove the need to distinguish (i) evidence about an intervention, (ii) assumptions encoded in a supplied graph, and (iii) feasibility of the resulting scenario. Counterfactual outputs are conditional on the model and identification assumptions; a software check cannot, by itself, prove those assumptions true.

This work examines EGFC, a pipeline intended to make these decisions explicit. It uses a provenance/freshness/confidence gate before scenario evaluation and a feasibility certificate before admitting generated shocks. The system records gate decisions and rejection reasons, then calls a deterministic counterfactual engine for accepted scenarios. The gates are deliberately separated from the causal engine: passing a gate means that the declared mechanical criteria passed, not that the underlying causal graph has been identified from data.

### 1.1 Research questions

- **RQ1 — Constraint control:** Does EGFC reduce the rate of scenarios violating predeclared hard constraints relative to unconstrained generation?
- **RQ2 — Risk utility:** At a matched scenario budget, does EGFC preserve or improve out-of-sample tail-loss coverage and calibration?
- **RQ3 — Evidence value:** Does removing the evidence gate increase the proportion of scenarios whose required intervention/edge claims lack acceptable point-in-time support?
- **RQ4 — Traceability:** Can each accepted result be reconstructed from the stored shock, evidence references, feasibility certificate, model version, and deterministic engine output?
- **RQ5 — Cost:** What are the additional runtime and memory costs of evidence checks and feasibility screening?

### 1.2 Contributions claimed for evaluation

This paper makes the following *candidate* contributions, to be retained as claims only if source inspection and experiments support them:

1. A modular stress-testing control flow that separates evidence coverage, model-conditional feasibility, and deterministic counterfactual evaluation.
2. An auditable rejection record for evidence failures and infeasible generated scenarios.
3. A preregisterable evaluation protocol that tests the gates independently using chronological holdouts and matched scenario budgets.
4. An implementation and benchmark artifact designed to make the assumptions and missing empirical validation visible.

The paper does **not** claim that the graph is causally identified, that the default bounds are calibrated, that the tail sampler is a trained GFlowNet, or that synthetic smoke tests establish financial predictive performance.

## 2. Related Work and Research Positioning

Causal modelling has been proposed as a basis for more plausible and interpretable financial stress scenarios. Gao et al. [1] use Suppes–Bayes causal networks for stress testing. EGFC is not distinguished merely by using a causal graph or counterfactual simulation. Its testable design focus is the explicit coupling of evidence coverage and model-conditional feasibility checks with traceable acceptance/rejection decisions.

Counterfactual inference is inherently conditional on a structural model and its assumptions [2]. In EGFC, the graph is supplied by the configured research model; the gate does not discover causal edges, estimate confounding, or establish identification. Any paper claim about causal effects must therefore be supported by a separate identification argument and empirical diagnostics.

Tail-risk evaluation also requires care. Value-at-Risk and Expected Shortfall cannot be validated by looking only at generated scenario severity; out-of-sample realized outcomes and appropriate scoring/backtesting are needed. Recent work studies uncertainty-aware VaR estimation and calibration under dependent financial time series [3]. EGFC must therefore report realized holdout metrics separately from synthetic scenario summaries.

The literature review is preliminary. Before submission, authors must search IEEE Xplore, ACM Digital Library, Scopus/Web of Science, Google Scholar, Crossref, and relevant patent databases for closely related evidence-aware scenario generation, constrained counterfactual search, financial stress testing, and feasibility certificates. The absence of a matching item in this short list is not evidence of novelty.

## 3. Method

### 3.1 Pipeline overview

Let an intervention be (s), the portfolio allocation be (w), a supplied directed graph be (G), a set of evidence records be (E), and declared node/target bounds be (B). The pipeline is:

1. **Evidence gate:** evaluate whether required claims associated with the intervention and relevant graph paths have acceptable source attribution, unique identifiers, timestamps, confidence, and freshness.
2. **Base counterfactual:** if the evidence gate passes, run the deterministic SCM engine for the base intervention.
3. **Feasibility certificate:** check the base shock against declared bounds and the target interval.
4. **Tail scenario generation:** optionally sample seeded tail shocks from the configured distribution.
5. **Per-scenario screening:** compute a feasibility certificate for each generated shock; reject failing scenarios with reasons.
6. **Impact and audit output:** run the deterministic engine for accepted scenarios and return the shock, impact, systemic-stress summary, explanation trace, gate results, and aggregate counts.

The present implementation uses the configured default graph and an interval-propagation feasibility routine. Its default bounds are broad engineering guards and must not be interpreted as empirically calibrated market limits.

### 3.2 Evidence coverage

Represent evidence record (e_i) as
[
e_i=(id_i, source_i, t_i, c_i, S_i),
]
where (id_i) is a unique identifier, (source_i) is provenance, (t_i) is the observation timestamp, (c_iin[0,1]) is the supplied confidence, and (S_i) is the set of claims the record is declared to support.

For a cutoff time (t_0), minimum confidence (	au), and maximum age (d_{max}), an individual record is mechanically eligible when its identifier and source are nonempty and unique, its timestamp parses and is not in the future, (0leq t_0-t_ileq d_{max}), and (c_igeq	au). Let (C(s,G)) be the required intervention and graph-edge claims computed by the implementation. The gate passes only if every required claim has at least one eligible record mapped to it:
[
operatorname{EvidencePass}(s,E,G)=
mathbb{1}left[orall qin C(s,G),;exists e_i:qin S_iland operatorname{Eligible}(e_i)ight].
]

This is a coverage/provenance rule, not semantic source verification. A declared mapping (qin S_i) may be wrong or overconfident. The research evaluation must independently review source-to-claim mappings and must never generate evidence labels solely to force the gate to pass.

### 3.3 Model-conditional feasibility

Let (G) define a linear structural propagation model with declared node bounds. Interval propagation produces a reachable interval ([L_y,U_y]) for the target node. Let the admissible target interval be ([a_y,b_y]). A scenario is hard-infeasible under this certificate when the reachable interval cannot overlap the admissible interval, or when a fixed intervention violates its declared hard bounds.

The certificate is conditional on the supplied graph, edge weights, interval arithmetic, and bounds. It is not a proof that a scenario is economically plausible, statistically likely, or causally identified. The certificate type and rejection reason must be retained in outputs. The current code uses the configured default graph and bounds; domain-specific calibration is an open research requirement.

### 3.4 Counterfactual evaluation

For accepted intervention (s) and allocation (w), the configured deterministic engine returns a portfolio-impact quantity and explanation trace:
[
Delta y = f_{mathrm{SCM}}(s,w;G,	heta),
]
where (	heta) denotes the implementation's structural parameters. This notation is descriptive, not a claim that the model parameters are estimated consistently from observed financial data. The paper must document the units, sign conventions, node definitions, edge weights, and parameter provenance used in experiments.

### 3.5 Tail generation and rejection

A seeded sampler produces candidate scenarios (s_1,dots,s_N). For each candidate, the feasibility procedure either admits the scenario to the deterministic engine or records a rejection. The seed, sampler name, requested draws, accepted count, rejected count, and rejection reasons must be saved. The current implementation identifies the tail sampler as a seeded sampler and explicitly reports `gflownet_trained=false`; no claim of trained GFlowNet generation is made.

### 3.6 Failure behavior

Evidence-gate failure stops the pipeline before the counterfactual engine runs. Base-intervention feasibility failure stops tail-scenario evaluation. Invalid or infeasible generated scenarios are rejected and recorded. The implementation's fail-closed behavior must be verified by tests and endpoint-level tests before the paper describes it as a validated property.

## 4. Experimental Design

### 4.1 Data and temporal separation

Use point-in-time, timestamped, legally usable market/financial data. Record provider, symbol/variable definitions, frequency, timezone, adjustment methodology, missing-value policy, licensing terms, and retrieval date. Do not use future information to construct the graph, calibrate thresholds, set bounds, select scenarios, or tune models for an earlier test period.

Use rolling-origin evaluation with chronologically ordered train, calibration/validation, and untouched test periods. Choose split dates and metrics before inspecting test outcomes. Where a real financial target cannot be mapped to the implementation's portfolio output, report the mismatch and do not present proxy metrics as realized financial-risk validation.

### 4.2 Baselines

Run the following with the same point-in-time inputs and comparable scenario budgets:

- **B1 — Historical replay:** resample historical stress windows.
- **B2 — Deterministic stress suite:** fixed, documented shocks.
- **B3 — Unconstrained tail sampler:** same seeded generator without feasibility rejection.
- **B4 — SCM without evidence gate:** counterfactual engine and scenario generator with the evidence gate disabled for the ablation.
- **B5 — SCM without feasibility gate:** same setup without feasibility rejection.
- **B6 — Full EGFC:** evidence gate plus feasibility certificate plus deterministic counterfactual engine.

Document any baseline that cannot be implemented fairly. Do not compare results that use different input data, graph versions, or scenario budgets without explaining the difference.

### 4.3 Metrics

**Evidence and feasibility:** evidence-gate pass/fail rate; missing/stale/future/low-confidence record counts; accepted scenario count; hard-constraint violation rate; rejection reasons; false-pruning rate where ground-truth feasible scenarios can be defined.

**Risk utility:** realized loss coverage on held-out outcomes; VaR exceedance frequency; appropriate joint VaR/ES scoring or backtests where the output supports them; tail-loss ranking quality; stress-window detection; calibration error. Generated p95 impact alone is not a measure of predictive accuracy.

**Traceability:** percentage of results with complete evidence IDs, model version, shock, certificate, and reproducible deterministic output; explanation-to-engine consistency; missing-field rate.

**Efficiency:** median and p95 runtime, peak memory, number of model-engine calls, and incremental cost per accepted scenario.

**Uncertainty:** report confidence intervals or block-bootstrap intervals appropriate to serial dependence, as well as sample counts. Include negative results and failures.

### 4.4 Ablations and sensitivity analysis

Remove the evidence gate and feasibility gate separately. Vary evidence freshness and confidence thresholds, graph edge weights, node bounds, target intervals, tail distributions, seeds, and scenario budgets. Measure both beneficial rejection and false pruning. A gate that rejects many scenarios is not automatically useful: it may also reject scenarios needed to capture genuine tail losses.

### 4.5 Reproducibility

Record the repository commit, Python/package versions, operating system, random seeds, data version and hashes, graph/configuration, experiment commands, stdout/stderr, and generated machine-readable outputs. The benchmark currently uses synthetic evidence fixtures and is a wiring/repeatability smoke test only. Its output must not be used as the paper's empirical result table.

## 5. Results

**Do not fill this section with invented values.** Populate it only after running the protocol.

| Result | EGFC | Baseline | Uncertainty / notes |
|---|---:|---:|---|
| Constraint-violation rate | [TO REPORT] | [TO REPORT] | [TO REPORT] |
| False-pruning rate | [TO REPORT] | [TO REPORT] | [TO REPORT] |
| Held-out VaR/ES metric | [TO REPORT] | [TO REPORT] | [TO REPORT] |
| Tail-window detection metric | [TO REPORT] | [TO REPORT] | [TO REPORT] |
| Complete trace rate | [TO REPORT] | [TO REPORT] | [TO REPORT] |
| Median / p95 runtime | [TO REPORT] | [TO REPORT] | [TO REPORT] |
| Peak memory | [TO REPORT] | [TO REPORT] | [TO REPORT] |

Interpret each metric in terms of the predeclared hypothesis. If no appropriate realized outcome is available, mark that metric **not evaluated** rather than substituting simulated severity.

## 6. Threats to Validity and Limitations

1. **Supplied graph:** evidence coverage does not identify causal edges or control unobserved confounding.
2. **Evidence mapping:** claim mappings and confidence values can be incorrect; source truthfulness and semantic entailment are not established by the current mechanical gate.
3. **Bounds:** default bounds are broad engineering guards, not calibrated market constraints. Incorrect bounds can produce false rejection or false acceptance.
4. **Interval model:** certificates depend on the declared linear-DAG assumptions and implementation semantics; they do not establish full economic plausibility.
5. **Synthetic smoke tests:** synthetic fixtures establish neither out-of-sample performance nor realized tail coverage.
6. **Tail sampler:** the current code does not claim a trained GFlowNet; distributional quality must be evaluated separately.
7. **External validity:** results from a particular graph, asset universe, time period, or data source may not generalize.
8. **Implementation status:** tests, API behavior, numerical edge cases, and end-to-end integration must be checked at the exact commit used for the experiments.

## 7. Conclusion

EGFC formalizes a research pipeline in which evidence coverage and model-conditional feasibility are explicit gates before downstream counterfactual stress analysis. Its value is an empirical question, not a conclusion from implementation alone. The next stage is a preregistered, chronological evaluation with real point-in-time data, matched baselines, gate ablations, calibration/coverage analysis, and transparent reporting of false pruning and computational cost. Only results that survive this evaluation should be used to support claims about practical benefit.

## References

[1] G. Gao, B. Mishra, and D. Ramazzotti, “Causal data science for financial stress testing,” *Journal of Computational Science*, vol. 26, pp. 294–304, 2018, doi: [10.1016/j.jocs.2018.04.003](https://doi.org/10.1016/j.jocs.2018.04.003).

[2] J. Pearl, *Causality: Models, Reasoning, and Inference*, 2nd ed. Cambridge, U.K.: Cambridge University Press, 2009.

[3] M. Ivancevic, K. A. Nguyen, and Z. Luo, “Reliable value at risk estimation with conformal prediction,” *Risk Management*, vol. 28, article 59, 2026, doi: [10.1057/s41283-026-00243-6](https://doi.org/10.1057/s41283-026-00243-6). Verify the final bibliographic record and applicability before submission.

## Author and submission notes

- Add only authors who meet the target venue's authorship criteria; obtain their approval.
- Verify every reference, DOI, page range, and current publication status.
- Record the final repository commit and artifact version after all experiments.
- Follow the target publisher's current rules for AI-assisted writing and code disclosure. IEEE publication guidance requires disclosure of AI-generated article content in the acknowledgements and identification of the relevant sections; check the current policy before submission.
