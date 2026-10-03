# FinAI — Additional FinTech Patent Mechanism Landscape

Date: 2026-10-03
Status: technical research worksheet; not legal advice or a patentability determination.

## Search conclusion

The search indicates that broad FinTech AI ideas are heavily populated. The strongest strategy is to define a narrow, concrete computer-implemented mechanism and then demonstrate a measurable technical effect.

## Candidate mechanisms for FinAI

### A. Causal-feasibility prefix pruning — primary family

Mechanism:
partial stress trajectory -> conservative SCM reachable-set certificate -> action masking -> expensive SCM/tail evaluation only for survivors.

FinAI status:
implemented in causal_risk/feasibility_pruning.py and causal_risk/constrained_gfnets.py.

Prior-art pressure:
High. Generic trajectory pruning, causal graph pruning, action masking and financial risk simulation are all known. The differentiating limitation is the combination of a target-directed structural reachable-set certificate with pre-SCM action gating and measured high-risk recall.

References:
US20230082365A1
CN120688647B
CN120598700A
US20260057252A1
CN121146937A
US20260073260A1

### B. Bidirectional target-directed pruning — strongest new extension

Mechanism:
1. forward interval certificate from the current partial prefix;
2. backward necessary intervals from the desired terminal risk region through the causal DAG;
3. candidate action survives only if it intersects both the forward reachable region and the backward necessary region;
4. unrelated variables outside the target ancestor cone are removed from the expensive search state.

Why it is interesting:
This turns FinAI from generic forward pruning into target-directed search-space reduction. It can reduce both candidate dimensions and candidate values before the full SCM.

FinAI status:
prototype implemented in causal_risk/bidirectional_feasibility.py.

Research requirement:
prove soundness for the supported linear-DAG class and quantify search reduction and false-pruning behavior on exact small-state enumerations and real data.

Prior-art pressure:
Medium-high. Reachable-set methods and backward target reachability are well known outside finance, while financial causal path mining is populated. The exact combination needs focused claim-chart review.

### C. Incremental descendant-cone recomputation — compute optimization family

Mechanism:
when one candidate intervention changes, recompute interval state only over the affected descendant cone and reuse cached intervals elsewhere.

FinAI status:
prototype implemented in causal_risk/incremental_feasibility.py.

Prior-art pressure:
High-medium. Incremental graph computation and scenario caches are known, so the claim should require causal dependency signatures and exact descendant-cone invalidation tied to risk certificates.

References:
US12008009B2
US20100145875A1
CN121169421A

### D. Causal-equivalence scenario compression — candidate

Mechanism:
after cheap prefix evaluation, group trajectories that have indistinguishable bounded downstream structural-risk signatures; fully evaluate only representative trajectories and propagate multiplicity/weights when estimating tail metrics.

Potential technical effect:
fewer expensive SCM and tail calculations while preserving a controlled approximation error.

Prior-art pressure:
Medium-high. Scenario clustering and simulation memoization are known; the differentiated aspect would need an explicit causal-effect equivalence certificate and bounded tail-metric error.

References:
US12008009B2
US8924274B2
CN115827423B
CN120832507A

### E. Causal-uncertainty adaptive model precision — candidate

Mechanism:
use causal-feasibility margin and graph stability to select computation precision and model depth:
far from a decision boundary -> lower-cost path;
near boundary or unstable graph -> higher precision/deeper model;
hard-risk cases -> full evaluation.

Potential technical effect:
resource-aware risk computation.

Prior-art pressure:
High. Adaptive precision, mixed precision and hierarchical financial risk engines are already disclosed.

References:
CN121235815A
US20260093454A1
CN120929220A
US20120254011A

This should be a dependent embodiment rather than the main invention unless experiments reveal a distinct mechanism.

### F. Event-triggered causal-cone invalidation — candidate

Mechanism:
a point-in-time market/news/macro event maps to one or more causal nodes; only the downstream causal cone is invalidated and recalculated; unaffected portfolio risk state remains cached.

Potential technical effect:
lower recomputation latency on streaming financial data.

Prior-art pressure:
High-medium. Dynamic financial graphs and incremental risk processing already exist.

References:
CN121169421A
CN120975896A
CN121883158A
CN121638940B

This is a strong engineering feature for FinAI but probably needs a narrower technical distinction before standing alone as a patent family.

### G. Causal information-gain intervention planner — candidate

Mechanism:
select the next stress-test intervention not only by expected tail severity but by expected reduction in uncertainty between competing causal graphs, subject to feasibility and compute budget.

Potential technical effect:
fewer expensive interventions needed to resolve causal ambiguity.

Prior-art pressure:
High for the general concept because active causal discovery using informative interventions is established.

Reference:
WO2023092093A1

Possible FinAI distinction:
financial risk target + portfolio relevance + causal feasibility + compute-cost objective.

This is promising for the research paper but requires deeper prior-art analysis before any patent filing decision.

### H. Proof-carrying causal risk capsule — candidate

Mechanism:
package a risk result with hashes/fingerprints of:
dataset snapshot,
model,
causal graph,
calibration bundle,
scenario seed,
feasibility certificate,
XAI path,
and evaluation configuration,
so an independent verifier can replay and validate the exact risk computation.

Potential technical effect:
tamper-evident reproducibility and deterministic verification of research risk outputs.

Prior-art pressure:
Very high for general model/data provenance and AI attestation.

References:
US20260023828A1
US20240403493A1
EP4154196A1
US12192372B2

Use as a supporting embodiment, not the central invention.

### I. Privacy-preserving causal stress sketches — candidate

Mechanism:
each institution computes a low-dimensional causal stress-response sketch locally, then securely aggregates sketches so the network can estimate systemic stress without exchanging raw portfolios.

Potential technical effect:
communication and privacy efficiency.

Prior-art pressure:
Very high. Federated learning, homomorphic encryption, ZK proofs and financial risk aggregation are crowded.

References:
CN118229420A
CN120611985B
CN121280141A

Potentially useful product direction, but not the first patent target.

### J. Evidence-conditioned causal state admission — candidate

Mechanism:
financial text/events can affect the causal state only when source freshness, entity alignment, temporal alignment, and contradiction checks satisfy explicit gates; otherwise the evidence is quarantined without mutating the production/research state.

Potential technical effect:
prevents corrupted or stale multimodal evidence from triggering expensive downstream computation.

Prior-art pressure:
High. Financial evidence conflict resolution, timestamp alignment, confidence scoring and data-lineage systems are already disclosed.

References:
CN121833939A
CN120876037A
CN120929133A
US20250363189A1

This is valuable for FinAI reliability, but broad claims would likely overlap heavily.

## Recommended FinAI patent architecture

Primary:
A + B + C

The strongest technical story is:

point-in-time state
-> target-directed backward cone
-> partial trajectory
-> bidirectional causal-feasibility certificate
-> action masking
-> incremental descendant-cone recomputation
-> adaptive budget controller
-> full SCM/tail evaluation
-> recall/resource telemetry

Supporting dependent embodiments:
D, E, F, G, H.

Separate family only after evidence:
I or J, and only if a distinct technical mechanism emerges.

## Evidence required

For A/B/C, measure:
- candidate count;
- action-space reduction;
- full SCM calls;
- avoided SCM calls;
- interval computations;
- descendant-node recomputations;
- wall-clock latency;
- peak RAM;
- peak GPU memory;
- high-risk trajectory recall;
- false-pruning rate;
- tail-metric error;
- scenario diversity.

The patent-oriented technical effect should be established experimentally rather than asserted.

## Legal boundary

No search can establish a legal conclusion that an invention is patentable. Patentability depends on the exact claims, effective filing/priority dates, complete prior-art universe, jurisdiction, prosecution history, inventorship and statutory tests for eligibility, novelty, inventive step/non-obviousness, written description/enablement and related requirements.

This document should be treated as an invention-development and prior-art research aid for review by a qualified patent professional.
