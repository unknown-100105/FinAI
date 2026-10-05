# FinAI Patent Hypothesis — Non-Patent Literature Cross-Check

Date: 2026-10-04

This document records non-patent literature relevant to the technical
combination being investigated. It is not a novelty opinion.

## Directly relevant technical literature

### GFlowNet sequential generation

Bengio, E. et al. (2021), "Flow Network based Generative Models for
Non-Iterative Diverse Candidate Generation," NeurIPS 34.

Relevance: establishes the core idea of learning a stochastic policy that builds
objects through sequences of actions and targets diverse high-reward samples.
FinAI's candidate stress trajectory generation uses the same broad sequential
generation pattern, so GFlowNet itself is not a differentiator.

Reference:
https://proceedings.neurips.cc/paper/2021/hash/e614f646836aaed9f89ce58e837e2310-Abstract.html

### Trajectory balance

Malkin, N. et al. (2022), "Trajectory balance: Improved credit assignment in
GFlowNets."

Relevance: provides an alternative GFlowNet objective for long compositional
action sequences. This further supports treating "GFlowNet generation" as a
known component rather than the inventive core.

Reference:
https://arxiv.org/abs/2201.13259

### GFlowNet graph pruning

Chen, R. et al. (2025), "Proxy-Free GFlowNet."

Relevance: describes pruning a DAG using learned edge-level rewards and using
the pruned structure to guide backward trajectory sampling. This is particularly
important prior art for any claim that simply says "use GFlowNet plus pruning."
FinAI's hypothesis therefore needs to remain tied to a financial stress state,
a causal reachable/necessary interval certificate, pre-expensive-SCM action
screening, and explicit compute/recall accounting rather than generic GFlowNet
pruning.

Reference:
https://arxiv.org/abs/2505.20110

### Causal DAG discovery

Zheng, X. et al. (2018), "DAGs with NO TEARS: Continuous Optimization for
Structure Learning," NeurIPS 31.

Relevance: establishes a continuous optimization formulation for DAG structure
learning. FinAI uses a NOTEARS-style research component, but DAG discovery is
not itself the inventive core of the proposed pruning loop.

Reference:
https://proceedings.neurips.cc/paper_files/paper/2018/hash/e347c51419ffb23ca3fd5050202f9c3d-Abstract.html

## Technical differentiation that still needs evidence

The research hypothesis should be phrased as the end-to-end computational
mechanism:

1. create a point-in-time financial state and partial stress trajectory;
2. apply explicit structural-DAG bounds;
3. compute a conservative forward reachable interval;
4. compute backward necessary intervals through the target ancestor cone;
5. reject actions before expensive structural/tail evaluation when the
   candidate is provably inconsistent with either certificate;
6. optionally use a separate adaptive compute controller for candidates that
   remain hard-feasible;
7. record avoided expensive evaluations and high-risk recall against an
   exhaustive baseline;
8. validate surviving trajectories with the full structural/tail evaluator.

The literature above means no novelty should be asserted merely from:
- GFlowNet generation;
- DAG/causal graph construction;
- graph pruning;
- action-space reduction;
- counterfactual simulation;
- generic financial stress testing.

## Required next literature/search work

Before a filing decision, search additional non-patent literature for:
- interval and zonotope reachability in DAGs;
- abstract interpretation and conservative state-space pruning;
- causal convex/linear reachable-set analysis;
- branch-and-bound for constrained trajectory generation;
- safe action masking under known dynamics;
- risk-constrained generative planning;
- computational resource reduction with recall guarantees.

Also record publication dates relative to the intended priority date and preserve
the source URLs, version/DOI, and exact passages relied upon.

## Boundary

This document is a research cross-check, not legal advice. WIPO's search
guidance states that relevant prior art can include public disclosures by any
means and recommends broadening to non-patent literature when needed. Indian
patentability also has separate statutory treatment of mathematical methods,
business methods, computer programmes per se and algorithms, so claim drafting
must be reviewed by qualified patent counsel for the chosen jurisdiction.
