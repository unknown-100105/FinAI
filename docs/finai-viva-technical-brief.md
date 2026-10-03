# FinAI — Viva Technical Brief

## 1. What FinAI is

FinAI is a financial-domain assistant that separates language understanding from
authoritative computation and verification.

The high-level path is:

`user request -> domain/intent router -> policy/authority checks ->
orchestration -> deterministic finance/market tools or research components ->
response generation -> claim/response verification -> XAI trace`.

The language model is not treated as the source of truth for deterministic
financial calculations or verified tool results.

## 2. Model and training foundation

The project uses Sarvam-1 as the domain-language model foundation described by
the project training workflow. QLoRA is used to adapt a quantized base model
with low-rank trainable adapters instead of updating every base parameter.

QLoRA means Quantized Low-Rank Adaptation:
- the base model is quantized to reduce memory;
- low-rank adapter matrices are trained;
- the base weights remain mostly frozen;
- the adapter captures task-specific behavior at much lower memory cost.

The project also uses a multilingual finance router and Qwen3-Embedding-0.6B
for semantic embedding work where configured.

Important boundary: benchmark accuracy or model loading does not by itself prove
real-world financial correctness.

## 3. Reliability architecture

### Router
Maps a user request to a domain/intent. The route is tested independently
because routing errors can send the request into the wrong authority path.

### Policy / authority
Defines what the system may calculate, retrieve, explain or expose. This is
separate from the language model's free-form output.

### Deterministic finance engine
Handles formulas such as EMI, SIP and interest calculations through explicit
code rather than asking the language model to perform arithmetic implicitly.

### Model gateway / registry
Separates provider/model selection from application orchestration and allows
fallback handling without silently changing an explicitly requested model.

### Claim verification and XAI
The system extracts claims from generated responses, verifies them against
available authoritative/evidence paths, and records trace information.

## 4. Causal Risk Lab

The causal stack is explicitly research-stage.

### Causal discovery
NOTEARS-style continuous optimization learns an acyclic graph candidate under
research assumptions. Lagged temporal screening, stability checks, direction
conflict handling and consensus are additional validation layers.

NOTEARS output is a graph candidate, not automatically an identified causal
effect.

### Structural causal model
The SCM uses explicit intervention semantics. In Pearl-style notation,
`do(X=x)` means X is fixed to x and its incoming structural relationship is
cut for that intervention. Downstream variables are then evaluated through the
structural equations.

### Tail scenarios
Monte Carlo, dependence-aware sampling and GFlowNet-style sequential generation
are research mechanisms for producing candidate stress trajectories.

### Temporal GNN
The project contains a TGAT-style architecture and training/evaluation path.
The architecture being trainable does not mean the model is validated for
future production use.

### Multimodal graph
Numerical market state, text/events/entities and portfolio information are
represented as typed graph components with provenance and missing-modality
handling.

## 5. The patent-oriented mechanism

The most defensible technical hypothesis is not "AI for finance" or
"GFlowNet for finance".

It is:

`partial stress state
 -> forward reachable-interval certificate
 -> backward necessary-interval certificate
 -> candidate action masking
 -> incremental descendant-cone update
 -> expensive SCM/tail evaluation only for survivors
 -> compute/recall telemetry`.

### Forward certificate
Given a partial intervention and explicit node bounds, interval propagation
calculates an outer bound on the target variable.

If the reachable interval does not intersect the admissible target interval,
the candidate is hard-infeasible under the stated linear-DAG assumptions.

### Backward certificate
Starting from the target interval, necessary intervals are propagated backward
through the target's ancestor cone.

A candidate outside a necessary interval cannot reach the target under the stated
bounds, so it may be masked before expensive simulation.

### Intervention-aware semantics
Future generator actions are themselves interventions. When a node will be
intervened later, its incoming structural dependence is not incorrectly used to
constrain an earlier action.

This is critical for avoiding false pruning.

### Incremental computation
When one candidate action changes, only its descendant cone is recomputed instead
of rebuilding every interval in the graph.

### Adaptive pruning
The hard structural certificate and the secondary compute-budget heuristic are
kept separate. Recall protection can override aggressive heuristic pruning.

## 6. Benchmark design

The repository now contains a deterministic finite-state benchmark with:
- exhaustive completion evaluation;
- forward certificate screening;
- backward necessary-interval screening;
- persistent incremental interval updates;
- false-prune accounting;
- high-risk prefix recall;
- estimated expensive evaluations avoided.

The benchmark is intentionally small and controlled. It is not real-market
evidence.

## 7. Patent landscape

Known crowded areas include:
- causal financial stress testing;
- generative financial stress testing;
- causal graph construction and search;
- reinforcement-learning candidate-action generation;
- GFlowNet sequential generation;
- generic pruning of search spaces.

Therefore the invention disclosure should center on the concrete computation and
evaluation order, not on brand names such as "AI", "GFlowNet" or "causal".

## 8. Patent vocabulary to use carefully

**Novelty:** whether every claim element is disclosed in qualifying prior art.

**Inventive step / non-obviousness:** whether the claimed invention as a whole
would have been obvious to a skilled person in view of the relevant prior art.

**Prior art:** public disclosures before the relevant date.

**Technical effect:** a measurable computational/technical consequence that can
support the technical contribution analysis where applicable.

**Enablement:** whether the disclosure is sufficiently enabling for the claimed
subject matter.

## 9. India-specific caution

Computer-related inventions need jurisdiction-specific claim analysis.
FinAI's patent hypothesis must therefore be framed around a concrete technical
mechanism and technical contribution rather than merely a financial business
method or an abstract algorithm.

## 10. Questions likely to appear in viva

### Why not let the LLM generate the final financial answer directly?
Because deterministic calculations and verified evidence are more controllable
when represented as authoritative system results, with the LLM acting as an
explanation layer.

### Why use causal discovery?
Correlation describes association. A structural causal graph provides a way to
represent directional intervention assumptions and downstream propagation. The
learned graph still requires empirical validation and should not automatically
be interpreted as identified causality.

### Why use intervals?
An interval certificate can reject some candidate actions without running an
expensive structural simulation. Its safety comes from being an outer bound
under stated assumptions.

### Why both forward and backward pruning?
Forward reasoning asks "what target states are reachable from this prefix?"
Backward reasoning asks "what parent states are necessary for the target?"
Using both can remove candidates that violate either condition.

### Why is future intervention handling important?
Because a later intervention changes the structural equation for that node.
Ignoring this can incorrectly propagate an earlier cause through a node whose
value will later be set directly.

### What proves the patent mechanism works?
A reproducible benchmark must show reduced expensive computation while preserving
high-risk trajectories, with measured false-pruning, recall, ablations and
future-only real-data validation.

## 11. What FinAI does NOT currently claim

- trained production TGAT;
- validated production GFlowNet;
- identified causal effects from NOTEARS alone;
- real-market validation of the patent mechanism;
- patent novelty or inventive step;
- production authorization/execution based solely on research components.

## 12. One-sentence explanation

"FinAI is a guarded financial AI system that separates language generation from
authoritative financial computation and verification, while its research Causal
Risk Lab adds an intervention-aware forward/backward feasibility certificate to
prune expensive generative stress trajectories before full structural evaluation."
