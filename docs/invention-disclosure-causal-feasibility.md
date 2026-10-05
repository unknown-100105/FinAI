# FinAI Invention Disclosure — Causal-Feasibility Feedback and Adaptive Search-Space Pruning

Date: 2026-10-03
Status: Research/invention disclosure draft — not a legal opinion or a patent application.

## 1. Invention concept

Working title:
Causal-Feasibility Feedback and Adaptive Search-Space Pruning for Generative Financial Stress Trajectories

Technical problem
Generative financial stress systems can produce large numbers of partial and complete candidate trajectories. Applying a full structural causal model (SCM), downstream risk propagation and tail-risk evaluation to every candidate can create unnecessary CPU/GPU computation, especially when many candidate prefixes cannot possibly reach an admissible terminal stress region under known structural bounds.

Proposed technical solution
FinAI introduces an intermediate prefix-evaluation layer between the trajectory policy and the full structural simulator.

For each partial trajectory and candidate next action:
1. represent known intervention values as fixed prefix state;
2. represent unassigned nodes as bounded intervals;
3. propagate interval bounds through the contemporaneous linear DAG;
4. compute a conservative reachable interval for a designated terminal risk variable;
5. optionally intersect candidate values with empirical marginal-support envelopes;
6. emit a machine-readable feasibility certificate;
7. mask hard-infeasible candidate actions before expensive SCM evaluation;
8. optionally apply an adaptive budget controller to already-feasible candidates;
9. generate complete surviving trajectories;
10. execute full SCM/tail validation only on selected trajectories;
11. use measured validation outcomes to evaluate the pruning policy and, in a future research extension, update the generator/controller.

## 2. Critical distinction from generic pruning

The inventive hypothesis is not merely graph pruning, trajectory pruning, action masking, or neural-network pruning. Those areas have substantial prior art.

The proposed distinction to investigate is the combination of:
partial financial stress trajectory + linear-SCM reachable-set certificate + empirical support envelope + pre-SCM candidate action masking + explicit compute-budget controller + downstream risk validation.

The certificate is conservative under its stated mathematical assumptions. A hard prune occurs only when the conservative reachable target interval cannot overlap the admissible target interval, or when a fixed intervention violates an explicit hard bound/support envelope.

Adaptive budget pruning is deliberately separated from the hard certificate because it is heuristic and must be recall-validated.

## 3. Current repository implementation

Implemented:
- causal_risk/feasibility_pruning.py: interval propagation, conservative hard-feasibility certificate, empirical support check, adaptive compute-budget controller, candidate-action screening.
- causal_risk/constrained_gfnets.py: GFlowNet-style research policy wrapper, candidate action enumeration, causal-feasibility masking, deterministic seeded generation, hard versus adaptive pruning telemetry.
- app/advanced_causal_api.py: POST /api/v1/causal-risk/research-pruning/screen and POST /api/v1/causal-risk/research-pruning/constrained-gfnets.
- tests/test_feasibility_pruning.py
- tests/test_constrained_gfnets.py

Existing FinAI components that participate:
- causal_risk/stress_objectives.py: causal-empirical reward.
- causal_risk/gfnets.py: trainable GFlowNet-style research prototype.
- causal_risk/scm.py: deterministic linear structural propagation.
- causal_risk/tail_scenarios.py: correlation-aware Gaussian and Student-t-copula research sampling.
- causal_risk/research_evaluation.py: tail backtesting, scenario quality, ablation and robustness utilities.

## 4. Proposed system sequence

Point-in-time financial state
-> GFlowNet-style policy
-> Partial trajectory prefix
-> Causal-feasibility certificate
-> interval reachability + hard intervention bounds + empirical support envelope + target overlap
-> hard-prune infeasible actions
-> optional adaptive budget filter
-> complete trajectory
-> full SCM propagation
-> tail/CVaR/ES evaluation
-> measured validation
-> experiment/controller feedback loop

## 5. Mathematical certificate

For a linear contemporaneous DAG, X_j = sum_i w_ij X_i, and node intervals [L_i,U_i], each parent contribution is bounded by [min(w_ij L_i,w_ij U_i), max(w_ij L_i,w_ij U_i)]. Summing contribution intervals gives an outer reachable interval [L_j,U_j].

For a target interval [T_L,T_U], define margin = min(U_target - T_L, T_U - L_target).

If margin < 0, the target interval cannot overlap the conservative reachable set, so the prefix is hard-infeasible under the model and bounds used for the certificate.

This is an outer-bound screening mechanism, not a complete feasibility solver. Correlations between unresolved exogenous variables and nonlinear/latent constraints can make the interval conservative.

## 6. Adaptive controller hypothesis

The hard certificate has fixed semantics and is not relaxed by the budget controller.

The adaptive controller changes only a secondary margin for candidate filtering after hard-infeasible actions are removed.

A publication-grade version should additionally use a recall guard so aggressive heuristic pruning is automatically disabled when measured high-risk trajectory recall falls below a predefined floor.

## 7. Prior-art stress test

An initial search campaign used more than 100 distinct patent-query formulations across causal + generative finance, financial stress testing, GFlowNet/constrained generation, trajectory/prefix pruning, causal graph pruning, multimodal financial graphs, counterfactual risk, adaptive thresholds, hardware/low-latency financial risk, privacy-preserving risk, model provenance, point-in-time data, leakage control, evidence/audit systems and systemic-risk aggregation.

High-overlap documents:

1. US20260073260A1 — Causality-augmented generative intelligence. Close overlap with heterogeneous/multimodal data, causal representation, causal constraints on generation, counterfactual validation and financial-domain use. Broad architecture-level novelty is unsafe.
Reference: https://patents.google.com/patent/US20260073260A1/en

2. CN121146937A — Financial stress testing based on generative AI. Close financial use case involving multisource data, asset relationship graphs, conditional graph generation, stress scenarios and VaR/CVaR.
Reference: https://patents.google.com/patent/CN121146937A/en

3. US20230082365A1 — Simulated trajectories using parallel beam search. Discloses generation and pruning of partial trajectories based on scores. Key generic trajectory-pruning reference.
Reference: https://patents.google.com/patent/US20230082365A1/en

4. CN120688647B — Causal-graph clustering and pruning. Discloses causal graph pruning to reduce GNN computation.
Reference: https://patents.google.com/patent/CN120688647B/en

5. CN120598700A — Financial-document reinforcement-learning action sequence pruning. Discloses financial workflow action-space search and pruning using Monte-Carlo prediction.
Reference: https://patents.google.com/patent/CN120598700A/en

6. CN121562930A — Causal DAG pruning and lag restriction. Discloses cycle removal, weak-edge pruning and lag-order limits for computational efficiency.
Reference: https://patents.google.com/patent/CN121562930A/en

7. US12014606B2 — AI market microstructure. Includes causal structures and financial stress-testing concepts.
Reference: https://patents.google.com/patent/US12014606B2/en

Other crowded areas include dynamic financial risk thresholds, multimodal causal graphs, counterfactual financial risk systems, cryptographic AI provenance/audit trails, FPGA pre-trade risk assessment, adaptive model retraining, and privacy-preserving financial analytics.

## 8. Claim differentiation target

The research claim should not be a generic financial AI system using causal graphs and a GFlowNet.

The invention disclosure should instead test claims centered on:
1. constructing a partial financial stress trajectory;
2. deriving a conservative reachable terminal interval from an explicitly represented structural causal DAG;
3. producing a feasibility certificate before expensive downstream simulation;
4. masking candidate actions according to that certificate;
5. separately applying an adaptive compute-budget controller to feasible candidates;
6. performing full structural/tail evaluation only for surviving candidates;
7. recording certificate and downstream-validation telemetry.

The exact legal claim language must be drafted by patent counsel after the final implementation and prior-art search.

## 9. Experiments required to support the technical contribution

Compare on the same data, splits and seeds:
A. full SCM evaluation for all candidate actions;
B. hard certificate pruning;
C. hard certificate + fixed heuristic pruning;
D. hard certificate + adaptive budget pruning;
E. full proposed loop with causal-empirical reward.

Measure candidate actions, full SCM evaluations, avoided evaluations, wall-clock latency, CPU memory, GPU memory, compute utilization, accepted trajectory count, high-risk trajectory recall, false-pruning rate, causal-constraint violation rate, empirical-support violation rate, tail-risk metric error, and scenario diversity.

The strongest technical-effect evidence would be a reproducible reduction in expensive computation without unacceptable loss of valid high-risk trajectories. A second supporting effect is reduction in interval-propagation work through descendant-cone incremental recomputation. No invented performance number should appear in a patent or paper.

## 10. Research experiments

Minimum Finish-Line-2 protocol:
1. construct a point-in-time dataset;
2. build dataset/source/timestamp manifest;
3. create fixed future-only evaluation windows;
4. calibrate empirical SCM channels;
5. train and evaluate the temporal model;
6. train the causal-empirical GFlowNet;
7. generate baseline and constrained trajectories;
8. measure tail-risk calibration;
9. perform regime/OOD tests;
10. run component ablations;
11. run the pruning compute/recall experiment;
12. document failures and sensitivity.

## 11. Patent jurisdictions

India: a patent route is technically worth investigating only with claim language and specification that establish a qualifying technical contribution under the current CRI framework. The Indian Patent Act defines invention and inventive step and provides examination/opposition mechanisms addressing prior publication and obviousness.

United States: the mechanism has a possible technical-computation framing, but subject-matter eligibility is only one issue; novelty, non-obviousness, written description and enablement remain separate.

Europe: the EPO 2026 Guidelines state that AI/ML methods are mathematical in nature but may contribute to technical character when they contribute to a technical solution to a technical problem. Demonstrated computational efficiency can matter when properly established.

PCT: an international application route, not a single worldwide patent. The priority period is generally 12 months from the earlier application.

## 12. Filing/disclosure control

Do not publicly disclose the exact inventive mechanism, detailed claim strategy, or experimental implementation before discussing filing order with qualified patent counsel. WIPO notes that pre-filing public disclosure can destroy novelty in many jurisdictions.

For India, a provisional specification can be followed by a complete specification within 12 months. A PCT filing normally uses the 12-month priority period when claiming the first application's priority.

## 13. Current patentability conclusion

This research does not establish that the invention is patentable.

Current evidence supports a narrower conclusion:
- The broad FinAI architecture has substantial prior-art overlap.
- Generic causal graph pruning has prior art.
- Generic trajectory pruning has prior art.
- Financial generative stress testing has prior art.
- Causal + multimodal + counterfactual financial AI has prior art.
- The specific combination of a conservative linear-SCM reachable-set prefix certificate, pre-SCM action masking, separately controlled adaptive compute pruning, and measured downstream high-risk recall is a materially more specific invention hypothesis.
- No exact anticipatory reference was identified in this initial search campaign for that complete combination, but this is not a legal novelty opinion and does not rule out unpublished, foreign, non-patent, or differently worded prior art.

## 14. Recommended filing architecture

Prepare one main invention disclosure around the causal-feasibility computation and include dependent embodiments for GFlowNet-style generators, beam search, Monte-Carlo search, multimodal financial state construction, regime-conditioned bounds, portfolio-specific target regions, correlation-aware empirical support, CPU/GPU/distributed execution, audit telemetry, and hardware acceleration where genuinely implemented.

Do not create a second application merely because a different ML model is added. A second application should be considered only if experiments reveal a distinct inventive concept with a separate technical mechanism and supporting prior-art differentiation.

## 15. Current maturity

Engineering: locally verified 467 tests passed; frontend production build passed; live API smoke checks passed.

Patent-oriented engineering: causal-feasibility module implemented; constrained GFlowNet research wrapper implemented; incremental reachability-state module implemented; API exposure implemented; exact-small-state pruning benchmark implemented; regression tests implemented.

Still required: empirical dataset; real training; compute/recall benchmark; full ablation; broader non-patent literature search; claim-chart review against closest patent families; professional patent drafting and filing decision.