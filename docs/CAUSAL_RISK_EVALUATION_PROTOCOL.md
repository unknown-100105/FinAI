# Causal-risk / feasibility-pruning evaluation protocol

## Purpose and scope

FinAI contains an executable finite-action benchmark for a research hypothesis:
causal interval certificates can eliminate some action prefixes before exhaustive
completion enumeration. The current benchmark is a small-state correctness and
work-count experiment. It is not evidence of investment alpha, market-risk prediction
quality, regulatory fitness, or patent novelty.

## Minimum experiment matrix

For each scenario, retain the exact input graph, edge weights/lags, factor order,
action levels, center values, node bounds, target node/interval, prefix depth, and
scale. Run the following comparisons against the same inputs:

1. Exhaustive completion enumeration (ground-truth finite baseline).
2. Forward causal interval feasibility.
3. Backward target-cone necessary intervals.
4. Incremental interval propagation.
5. A no-pruning baseline and a simple bound-only baseline where applicable.

Vary independently:
- graph size and density;
- action-space cardinality and number of intervention factors;
- prefix depth;
- positive, negative, and near-zero edge weights;
- narrow, broad, and infeasible target intervals;
- node bounds that bind and bounds that do not bind;
- disconnected nodes, lagged edges, and target nodes outside the intervention cone.

Use fixed scenario IDs and deterministic input generation. If random graph generation
is introduced, record every seed and the generated graph itself. A seed alone is not
a reproducibility artifact.

## Required metrics

Report separately:
- number of candidate prefixes;
- exact completion evaluations;
- certificate/interval evaluations;
- false-prune count and false-prune rate over prefixes with at least one feasible
  completion;
- recall of prefixes with a feasible/high-risk completion;
- number of retained prefixes and reduction in evaluations;
- wall-clock runtime and peak memory for each method;
- correctness disagreements, exceptions, and unsupported graph assumptions.

Do not combine runtime and evaluation count into a single score. Run timing experiments
after warm-up, repeat each case, and report median plus spread. Small deterministic
unit tests should assert soundness; larger benchmarks should report empirical behavior.

## Soundness gates before claiming a pruning guarantee

- Compare every hard-pruned prefix against exhaustive completions for small action
  spaces.
- Include boundary values and numerical-tolerance tests.
- Check graph directionality, cycles, lags, and assumptions of the structural causal
  model explicitly.
- Verify that the certificate uses conservative bounds; unknown/unbounded cases must
  retain the prefix rather than prune it.
- Include adversarial counterexamples and regression tests for every discovered defect.
- Independent review should reproduce the outputs from the committed inputs.

## Publication and patent diligence

Archive benchmark JSON, source commit SHA, Python/dependency versions, machine
specification, command line, inputs, outputs, and limitations. Compare the mechanism
with relevant prior art and existing patent claims before describing any element as
novel. Patentability is a legal determination; a positive benchmark does not establish
novelty, inventive step, eligibility, or freedom to operate.
