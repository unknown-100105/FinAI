# FinAI patent candidate: intervention-aware counterfactual feasibility screening

**Status:** experimental implementation and preliminary patent hypothesis. This is not a legal opinion, patent filing, or conclusion that the method is novel.

**Working title:** Intervention-Aware Reachability Certificates for Conservative Counterfactual Risk Screening in Bounded Financial Models.

**Repository component:** finance_engine/counterfactual_screening.py.

## Why this candidate fits FinAI

The current FinAI design already has a deterministic finance engine, a policy/authority layer, a risk-capability controller, retrieval and XAI traces. An optional screening component can sit before an expensive scenario evaluator without replacing any of those components. It accepts an explicit bounded structural model and a proposed intervention, rather than pretending an LLM discovered causal truth.

## Technical problem

A counterfactual risk service may evaluate many proposed shocks, parameter changes, or portfolio interventions. Some proposals cannot reach a specified output-risk interval under the supplied structural equations and declared variable bounds. Sending every proposal into a costly simulation can waste compute. An unsound pruning rule, however, could remove a rare but important tail-risk scenario.

## Mechanism implemented in this prototype

1. Validate variable bounds, parent references and acyclicity, and compute a deterministic model fingerprint.
2. Propagate an output target interval backwards through linear structural equations to derive conservative necessary intervals for ancestor variables. Parent interactions are relaxed to their declared domains to avoid assuming unavailable dependence information.
3. Mask a proposed intervention only when its admissible interval is disjoint from an applicable necessary interval, or its forward reachable target enclosure does not intersect the target interval.
4. For interventions passing the backward gate, recompute only the intervention's descendant cone and reuse baseline interval ranges elsewhere.
5. Emit a machine-readable certificate containing graph version, reason code, target interval, reachable target enclosure, backward checks, recomputed nodes and interval-equation count.
6. Compare a screened candidate set against an exhaustive reference evaluator on a validation set; record missed feasible actions and recall. In production, fail closed or bypass the filter if model assumptions are unsupported or the measured recall gate fails.

**RETAIN means only that the inexpensive screen has not proven impossibility. It is not proof that the scenario is feasible or that a financial outcome is predicted correctly.** The current supported model is a supplied bounded linear DAG; this prototype does not discover causal edges, calibrate a portfolio loss distribution, or give investment advice.

## Candidate claim hypothesis (not yet a patent claim)

A computer-implemented method for screening candidate interventions against a target risk interval in a bounded acyclic structural model by (a) deriving backward-propagated necessary intervals, (b) generating a reason-coded, model-version-bound exclusion certificate only on interval disjointness, (c) recomputing only the intervention's forward descendant cone for actions that pass the backward gate, and (d) measuring the screened results against exhaustive candidate evaluation before enabling the filter in a controlled execution path.

Possible dependent elements for prior-art analysis include deterministic structural-model fingerprints, interval certificates, descendant-cone invalidation, bounded-model eligibility checks, and a circuit-breaker that routes unsupported models to exhaustive evaluation. These may be ordinary engineering details unless a specific new technical effect is demonstrated.

## Preliminary online prior-art scan — 13 October 2026

This is a targeted public-web search, not a literal search of every web page or a filing-grade clearance search. Patent dates, status, family members and claim scope should be checked against official registers and prosecution histories before filing.

| Reference | What is close | Implication |
|---|---|---|
| Gao, Mishra & Ramazzotti, “Causal data science for financial stress testing” (2018) | Uses causal networks for financial stress scenarios and classifier-based branch pruning to reduce computation versus Monte Carlo approaches. [ScienceDirect](https://www.sciencedirect.com/science/article/pii/S1877750317311377) | Generic causal finance plus pruning is not a defensible novelty point by itself. |
| CN121146937A, “A method and apparatus for financial stress testing based on generative artificial intelligence” | Asset-relation graphs, hierarchical Bayesian parameterization, graph-generative scenario generation, simulation and risk reporting. [Google Patents](https://patents.google.com/patent/CN121146937A/en) | Avoid broad claims to graph-based or generative financial stress testing. |
| US20260073260A1, “Causality-augmented generative intelligence…” | Heterogeneous data, causal representations, counterfactual assessment, dynamic causal graphs and explanations. [Google Patents](https://patents.google.com/patent/US20260073260A1/en) | Avoid claiming the broad combination of causal discovery, counterfactual validation and explanations. |
| US20260057252A1, “Task variable causal graph construction method…” | LLM priors, independence tests, Monte Carlo tree search and branch pruning in causal graph construction. [Google Patents](https://patents.google.com/patent/US20260057252A1/en) | Avoid generic causal graph search/pruning claims. |
| CN121146043A, “Intelligent information decision-making system based on reinforcement learning” | Dynamic causal graph, policy-generated actions and counterfactual inference. [Google Patents](https://patents.google.com/patent/CN121146043A/en) | Avoid broad claims to action selection over causal graphs. |
| WO2025067134A1, “Generative flow model training method…” | Sequential graph/state/action generation in a GFlowNet-family approach. [Google Patents](https://patents.google.com/patent/WO2025067134A1/en) | GFlowNets or graph action generation are not the proposed inventive center. |
| US20250335998A1, “System and method for validating LLM report content in regulated financial environments” | Compares generated financial metrics against retrieved values to check report content. [Google Patents](https://patents.google.com/patent/US20250335998A1/en) | Avoid broad claims to validating financial narratives against retrieved evidence. |

## Patentability and Indian context

WIPO's PCT guidance treats prior art broadly as information made public anywhere before the relevant date, and distinguishes novelty (whether all claim elements are disclosed) from inventive step (whether the claim as a whole would have been obvious). See [WIPO prior art](https://www.wipo.int/en/web/pct-system/texts/ispe/11_01), [novelty](https://www.wipo.int/en/web/pct-system/texts/ispe/12_01_02), and [inventive step](https://www.wipo.int/pct/en/texts/ispe/13_01_02.html).

India's Patents Act Section 3(k) excludes mathematical or business methods, computer programmes per se and algorithms. IP India's [CRI guidance page](https://ipindia.gov.in/resource/patents-resources-guidelines) lists the CRI 2025 guidance. A registered patent agent needs to assess the actual technical contribution, disclosure, current rules, claim scope and filing plan. Calling a method “AI”, “causal” or “GNN” does not make it patentable.

## Initial synthetic result

The included smoke benchmark uses eight synthetic interest-rate shock bands and a fixed-seed sampling oracle for a toy four-node chain. In that one setup, the filter masked four candidates, retained four, and retained all four candidates that the reference oracle marked feasible. The reported candidate-evaluation reduction is 50% (4 of 8); the validation benchmark uses extra oracle calls for the comparison. This is not real-market validation, proof of completeness for every possible model, or a guarantee of no false negatives.

## Required next experiments

1. Compare combined forward/backward intervals against exhaustive evaluation, forward-only pruning and backward-only pruning.
2. Expand randomized testing across graph sizes, fan-out, multi-parent/reconvergent paths, negative coefficients, wide domains and noisy equations.
3. Test rare tail events, bounded-variable changes, model version changes and automatic bypass for unsupported structural forms.
4. Record wall-clock time, evaluation count, recall, false-prune count and bypass rate across many published seeds.
5. Replace toy bounds with documented, calibrated inputs only after the underlying risk model is validated.
6. Have a registered patent agent conduct a filing-grade search across patent families and non-patent literature, and review office actions/prosecution histories before preparing a filing.

## Current limitations

- Supports bounded linear acyclic structural equations only.
- The causal graph and equations are assumed inputs, not automatically discovered ground truth.
- Sampled reference tests are not a mathematical proof of completeness.
- Synthetic results cannot support claims about actual financial accuracy or real-world risk reduction.
- No novelty, inventive-step, enforceability, infringement, freedom-to-operate or patent-grant conclusion is made.
