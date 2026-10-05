# FinAI Independent Static Audit — 2026-10-04

## Scope

Read-only review of the current PR branch covering the causal-risk research
stack, patent-mechanism implementation, API contracts, regression strategy,
documentation boundaries, and repository hygiene.

This is an engineering/research audit, not legal advice and not a statistical
validation study.

## Findings

### HIGH — Remote CI is not currently usable as verification evidence

**Evidence**
- GitHub Actions run series repeatedly reports Backend, Frontend, and Patent
  mechanism jobs as `failure`.
- The connected API exposes empty step lists for those jobs and the job-log
  endpoint returns no retrievable log blob.
- Therefore the remote workflow does not currently provide test/build evidence.

**Impact**
The repository cannot be described as having a green remote CI gate until the
GitHub Actions environment produces executable step/log evidence.

**Action**
Retain the native GitHub Actions run URL in the audit record, inspect the
failure in the GitHub UI, and rerun after the runner/environment issue is
resolved.

**Regression**
The repository-owner local verification cycle remains the fallback engineering
evidence, but it must be rerun on the final branch after these audit edits.

### MEDIUM — Real-data empirical validation remains outstanding

The repository provides chronological split utilities, causal discovery,
calibration, temporal-model evaluation, tail-risk metrics, OOD perturbation,
ablation infrastructure, and the finite-state patent benchmark.

The current branch does not itself contain an approved point-in-time financial
dataset plus publication/event timestamps sufficient to establish real-market
future-only validation. This is intentionally disclosed rather than simulated
as completed.

### MEDIUM — Patent novelty/inventive-step evidence remains incomplete

The repository now contains:
- a defined claim hypothesis;
- a prior-art matrix;
- non-patent literature cross-check;
- an executable finite-state mechanism benchmark;
- implementation-level claim differentiation.

This is not enough to establish novelty, inventive step, freedom to operate,
or filing readiness. The relevant-date analysis and professional search must
still cover patent families, non-patent literature, prosecution histories and
the selected jurisdiction.

### LOW — Wall-clock benchmark values are environment-dependent

The benchmark deliberately separates deterministic correctness metrics from
runtime measurements. A CI artifact can provide environment-specific latency,
but those timings should not be generalized to hardware-independent claims.

## Verified strengths

### Causal-feasibility mechanism

The hard screen is based on a conservative interval outer bound under stated
linear-DAG and explicit-bound assumptions.

The backward screen computes necessary intervals through the target cone. Failure
to intersect a necessary interval is a pruning certificate; intersection is not
a proof of feasibility.

### Correct intervention semantics

Both forward and backward screening now accept `intervened_nodes`.

A future intervention severs incoming structural edges for the purposes of
screening that future node. This prevents the common error of treating an
upstream cause as still determining a downstream variable that the generator
will later intervene on.

### Incremental update path

`IncrementalIntervalState.apply_change()` persists each candidate intervention
and recomputes only its descendant cone. The patent benchmark compares its
interval-node accounting with full propagation and checks exact interval-map
agreement.

### Research-only separation

The retained control-plane module is explicitly research-only and is covered by
tests for evidence freshness/conflict, uncertainty states, state-bound leases,
safe-mode degradation, and deterministic proof artifacts.

The previously duplicated unused `finai_control_plane.py` implementation was
removed.

### Repository hygiene

A static PR-diff sweep found no added TODO/FIXME/NotImplemented markers,
wildcard CORS configuration, disabled TLS verification, or obvious hardcoded
secrets in the changed diff.

## Missing evidence before a filing-grade patent decision

1. frozen point-in-time dataset;
2. real future-only benchmark;
3. exhaustive no-pruning versus pruning resource measurements;
4. high-risk recall and false-pruning intervals;
5. ablation and OOD results;
6. broader patent-family and prosecution-history search;
7. broader non-patent literature search;
8. inventorship record and priority-date decision;
9. jurisdiction-specific patent counsel review.

## Final audit position

The implementation is materially stronger and more defensible than the original
broad "AI + finance + causal graph + GFlowNet" concept because the repository
now isolates a concrete computational mechanism and measures the quantities
needed to test its technical effect.

The correct evidence labels are:
- engineering implementation: implemented;
- software regression: previously locally verified by the owner, but must be
  rerun on the final audit head;
- remote CI: unresolved;
- controlled synthetic/finite-state mechanism benchmark: executable;
- real financial validation: not yet established;
- patent novelty/inventive step: not established;
- production authorization/execution impact: intentionally not claimed.
