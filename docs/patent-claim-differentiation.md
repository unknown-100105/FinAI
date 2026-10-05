# FinAI Patent Claim-Differentiation Worksheet

Status: working technical worksheet for patent counsel; not legal advice.

## Candidate independent-claim concept

A computer-implemented process that:

1. receives a point-in-time financial state and an incrementally generated partial stress trajectory;
2. represents a research-approved structural causal DAG with explicit node/intervention bounds;
3. evaluates each candidate next action by propagating interval bounds through the DAG to obtain a conservative reachable interval for a target risk variable;
4. emits a feasibility certificate for the candidate next action;
5. masks a candidate action before full structural simulation when the certificate establishes hard infeasibility;
6. optionally applies a separate adaptive compute-budget threshold to hard-feasible candidates;
7. performs expensive structural/tail evaluation only for surviving candidates;
8. records certificate data, compute avoided, and downstream validation outcomes;
9. uses downstream validation to measure or update the candidate-generation controller.

## Claim-element comparison

| Candidate element | Generic prior-art exposure | FinAI differentiation target |
| --- | --- | --- |
| Financial stress testing | High | Not claimed by itself |
| Multimodal financial inputs | High | Supporting state-construction embodiment |
| Causal graph | High | Explicit interval-reachability computation |
| Counterfactual SCM | High | Used after certificate-based screening |
| Candidate action generation | High | Any incremental generator may be used |
| Generic trajectory pruning | High | Pruning is driven by causal reachable-set certificate |
| Causal graph pruning | High | Candidate action pruning, not topology pruning |
| Adaptive compute budget | High | Applied after hard certificate, coupled to recall validation |
| Empirical support | High | Used as an additional hard/support envelope in prefix screening |
| Incremental recomputation | Medium-high | Descendant-cone interval cache for candidate updates |
| Full SCM/tail evaluation | High | Explicitly deferred until certificate screening |
| Compute/recall telemetry | Medium | Evidence mechanism for measured technical effect |
| GFlowNet | High | Optional embodiment, not the core claim |
| Hardware acceleration | High | Optional embodiment only if genuinely implemented |

## Closest disclosed areas

### US20260073260A1

Broadly discloses heterogeneous/multimodal ingestion, causal representation, causally constrained generation, counterfactual validation and financial application.

Claim strategy: do not claim the architecture as a whole. Require the specific prefix certificate + action masking + pre-SCM evaluation ordering.

### CN121146937A

Financial generative stress testing with graph and VaR/CVaR components.

Claim strategy: do not claim “generative financial stress testing”. Claim the compute-saving candidate-screening mechanism.

### CN121146043A

Candidate decision actions are generated, evaluated against a dynamic causal graph, and counterfactual results are produced with feedback.

Claim strategy: require the conservative reachable-set certificate and the fact that it occurs before expensive structural evaluation.

### US20230082365A1

Partial trajectory generation/pruning is disclosed.

Claim strategy: causal interval reachability must be the source of the pruning certificate.

### US20260057252A1

Causal graph search includes candidate-action pruning and DAG-constraint checking.

Claim strategy: financial stress state + structural-risk target reachability + full SCM deferral.

### CN120688647B / CN121562930A

Causal-graph pruning for computational efficiency is disclosed.

Claim strategy: candidate trajectory pruning rather than merely removing graph edges.

### CN120598700A

Financial action-sequence search and pruning is disclosed.

Claim strategy: structural causal reachable-set certificate rather than return/reward ranking alone.

## Important drafting principle

Do not rely on the words:

- AI
- machine learning
- GFlowNet
- causal
- multimodal
- financial

as the source of novelty.

The technical disclosure should be concrete enough that the examiner can identify:

- input representation;
- data structures;
- certificate computation;
- interval propagation;
- action masking;
- evaluation ordering;
- incremental update behavior;
- compute-budget controller;
- instrumentation;
- measurable resource effect.

## Required evidence package before filing

1. exact algorithm flow diagram;
2. pseudo-code;
3. mathematical definitions;
4. implementation commit history;
5. controlled synthetic correctness benchmark;
6. real point-in-time financial benchmark;
7. no-pruning versus pruning resource measurements;
8. high-risk trajectory recall;
9. false-pruning rate;
10. ablation results;
11. broader patent/non-patent literature search;
12. inventorship record.

## Legal caution

This worksheet does not determine novelty, inventive step, subject-matter eligibility, or enforceability. A patent attorney/agent should convert the technical disclosure into jurisdiction-specific claims after a current prior-art search.
