# FinAI invention candidate: causal-feasibility-certified stress search

**Status:** research candidate/prototype, not a patentability opinion or proof of novelty.

## Technical problem

Stress-search procedures can spend compute on intervention prefixes that cannot reach a defined downstream risk interval. Aggressive pruning can also remove feasible scenarios. The research question is whether conservative necessary-interval certificates can reduce search cost while preserving feasible-scenario recall.

## Existing prototype

- `causal_risk/feasibility_pruning.py`: forward feasibility screening.
- `causal_risk/bidirectional_feasibility.py`: backward target-cone / necessary-interval screening.
- `causal_risk/incremental_feasibility.py`: incremental interval propagation.
- `causal_risk/constrained_gfnets.py`: GFlowNet-style action masking.
- `causal_risk/patent_benchmark.py`: small finite-state benchmark.

These artifacts do not establish novelty, inventive step, legal eligibility or market-scale effectiveness.

## Required experiments

Compare exhaustive search, forward-only, backward-only, combined bidirectional, incremental, unpruned GFlowNet and constrained GFlowNet on identical seeded finite-state inputs. Vary graph size/sparsity, edge signs, intervention counts, target intervals and parameter regimes. Record wall-clock time, peak memory, exact completion evaluations, retained/pruned prefixes, false-prune rate, feasible/high-risk scenario recall, accepted samples and uncertainty across seeds. Verify every claimed safe hard-prune against exhaustive enumeration on tractable fixtures. Separate conservative certificates from heuristic/adaptive pruning.

## Acceptance gates

- No false pruning on exhaustive finite fixtures for any prune labelled mathematically safe.
- Raw results include seeds, graph parameters and software versions.
- No real-market claim without time-ordered held-out data and realistic constraints.
- Report negative results and regimes where overhead exceeds benefit.

## Prior-art and disclosure workflow

Search patent databases and scientific literature for interval propagation, branch-and-bound, causal stress testing, constrained GFlowNets, robust optimization, counterfactual risk and scenario generation. Create a claim chart, specify the exact technical combination and effect, and obtain a qualified patent professional's assessment before filing. In India, analyze Section 3(k) and current computer-related invention guidelines. Seek filing advice before public disclosure.

## Honest current claim

FinAI contains a prototype combining forward/backward causal-feasibility reasoning, incremental interval propagation and constrained stress-search generation. Whether the combination is novel, inventive, patent-eligible or superior to baselines remains unestablished.
