# FinAI Patent Prior-Art Matrix — Initial 100+ Query Stress Test

Date: 2026-10-03

This matrix records an initial patent-landscape stress test using 100+ distinct query formulations plus targeted follow-up searches. It is a research aid, not a legal opinion and not a guarantee that no additional prior art exists.

## Core invention hypothesis

**Causal-Feasibility Feedback and Adaptive Search-Space Pruning for Generative Financial Stress Trajectories**

The target mechanism is:

partial financial stress prefix
-> conservative linear-SCM reachable-set certificate
-> pre-SCM action masking
-> optional adaptive compute-budget pruning
-> full SCM/tail validation only for survivors
-> validation telemetry
-> generator/controller feedback

## Prior-art overlap matrix

| Reference | Main overlap | Risk to broad FinAI claim | Differentiation target |
| --- | --- | --- | --- |
| US20260073260A1 | multimodal ingestion, causal representation, causally constrained generation, counterfactual validation, financial domain | Very high | Prefix-level reachable-set certificate and pre-SCM compute pruning |
| CN121146937A | financial stress testing, graphs, generative scenario engine, VaR/CVaR | Very high | Specific computational screening mechanism |
| CN121146043A | candidate actions + causal graph + do-intervention + reward feedback | Very high | Reachability certificate before expensive downstream evaluation |
| US20230082365A1 | partial trajectory generation and pruning | High | Causal-financial certificate rather than generic score pruning |
| US20260057252A1 | candidate-action pruning in causal graph search, MCTS, DAG constraints | High | Financial stress trajectory + SCM reachable interval + downstream risk validation |
| CN120688647B | causal graph pruning for GNN computation | High | Pruning candidate trajectories before SCM, not only graph topology |
| CN121562930A | causal DAG pruning, weak-edge filtering, lag limits | High | Prefix feasibility certificate and compute/recall measurements |
| CN120598700A | financial action-sequence search/pruning | High | Structural causal reachability instead of action return score alone |
| CN120563259A | financial counterfactual simulation and graph-edge perturbation | High | Formal prefix screening before structural simulation |
| CN120952184A | multimodal causal graph and counterfactual reliability | High | Explicit conservative reachable target interval + candidate masking |
| CN121561509A | multimodal causal graph, temporal causality, dynamic gating | High | Compute-saving prefix certificate and downstream SCM selection |
| WO2025067134A1 | constrained GFlowNet training/flow constraints | High | Financial causal-feasibility screening as an external action gate |
| CN114666204B | causal RL candidate action-space reduction | High | Reachability certificate from financial SCM bounds |
| CN121169421A | dynamic financial/supply-chain risk graph, incremental graph computation | Medium-high | Candidate trajectory feasibility rather than graph update alone |
| US12014606B2 | AI market microstructure and causal/stress concepts | Medium-high | Prefix-level causal feasibility and compute accounting |
| US20160371777A1 / US11367136B2 | low-latency hardware financial risk filtering | Medium for hardware embodiment | Do not rely on generic FPGA speed; use measurable certificate-driven reduction |
| US20240104521A1 | privacy-preserving financial aggregation | Medium for privacy embodiment | Privacy is supporting embodiment, not the main inventive core |
| US20210089899A1 / US12045716B2 | federated financial-risk learning | Medium | Avoid generic federated-risk claim |
| CN118093715A | blockchain + ZKP + financial data + ML | Medium | Avoid generic blockchain/ZKP embodiment |
| CN121767088A | ZKP financial credit verification + federated learning + feedback | High for ZKP branch | Avoid ZKP as separate novelty core without a new mechanism |

## Interpretation

### Broad concepts that should not be claimed alone

Avoid claims centered only on:

- AI financial risk scoring;
- financial stress testing with generative models;
- multimodal financial causal graphs;
- causal counterfactual finance;
- GFlowNet-based finance;
- trajectory pruning;
- causal graph pruning;
- federated financial risk;
- zero-knowledge financial risk;
- hardware pre-trade risk filtering.

The search found substantial prior-art density around all of these.

### Narrow mechanism to investigate

The more differentiated hypothesis is:

1. candidate stress trajectories are generated incrementally;
2. every candidate next action is transformed into a partial financial state;
3. a conservative reachable interval for a target risk node is calculated from a structural causal DAG and explicit node/intervention bounds;
4. a machine-readable certificate determines hard infeasibility before full structural simulation;
5. feasible candidates may optionally be subjected to a separate adaptive compute-budget threshold;
6. only surviving candidates enter expensive structural/tail evaluation;
7. the system records avoided evaluations and high-risk trajectory recall against a no-pruning baseline.

The search did not locate an exact reference during the initial 100+ query campaign that expressly combines all of these limitations in one disclosed financial system.

That statement does **not** establish novelty. It only identifies a narrower search target.

## Search families covered

The query campaign covered variants of:

- causal feasibility + financial stress;
- structural causal model + trajectory pruning;
- partial trajectory + financial risk;
- action masking + causal graph + finance;
- reachable interval + causal DAG + finance;
- counterfactual + candidate action pruning;
- GFlowNet + financial stress;
- constrained GFlowNet + causal risk;
- adaptive compute budget + trajectory generation;
- empirical support + causal candidate screening;
- multimodal financial graph + stress generation;
- temporal financial graph + pruning;
- causal graph incremental computation;
- low-latency financial risk;
- FPGA financial risk;
- privacy-preserving financial risk;
- ZKP financial analytics;
- federated systemic risk.

## Recommended patent-family architecture

Use one main invention disclosure around the certificate-driven computational loop.

Dependent embodiments can cover:

- GFlowNet-style trajectory generation;
- beam/MCTS/Monte-Carlo generators;
- multimodal financial state construction;
- regime-conditioned bounds;
- empirical-support envelopes;
- incremental certificate caching;
- CPU/GPU/distributed execution;
- audit telemetry;
- optional hardware acceleration.

A second patent family should be considered only if research demonstrates a separate technical mechanism with distinct prior-art separation.


## Non-patent literature cross-check

The patent search is supplemented by non-patent literature because the
underlying components are established independently:

- GFlowNet sequential generation (Bengio et al., NeurIPS 2021).
- Trajectory-balance training for GFlowNets (Malkin et al., 2022).
- GFlowNet DAG pruning / backward trajectory guidance (Chen et al., 2025).
- NOTEARS continuous DAG structure learning (Zheng et al., NeurIPS 2018).

The strongest implication is that the candidate invention cannot rely on
"GFlowNet + pruning" or "causal DAG + generation" alone. The narrower research
target remains the financial prefix-feasibility certificate loop, including
forward reachable intervals, backward necessary intervals, pre-expensive-SCM
action masking, and measured compute/recall effects.

See `docs/non-patent-literature-landscape.md` for the full cross-check.
