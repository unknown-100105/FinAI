# EGFC Experimental Protocol and Reproducibility Record

**Status:** protocol template; no empirical findings are implied.  
**Companion manuscript:** [EGFC_MANUSCRIPT_DRAFT.md](EGFC_MANUSCRIPT_DRAFT.md)

## A. Freeze the experimental design before viewing holdout results

- [ ] Record repository commit SHA and working-tree status.
- [ ] Record environment (OS, Python, dependency lock/package versions, CPU/GPU, memory).
- [ ] Specify target asset universe, frequency, target outcome, units, and portfolio mapping.
- [ ] Record data provider, license, extraction date, timezone, corporate-action handling, and missing-value policy.
- [ ] Choose chronological train/validation/test periods; preserve an untouched final test window.
- [ ] Specify graph source, edge weights, lags, node bounds, target interval, and their calibration source.
- [ ] Define primary/secondary metrics and uncertainty procedure before running the final holdout.
- [ ] Fix random seeds and scenario budgets for each baseline.
- [ ] Record excluded experiments and reasons, rather than silently dropping failures.

## B. Baseline matrix

| ID | Method | Evidence gate | Feasibility gate | Required control |
|---|---|---:|---:|---|
| B1 | Historical replay | No | No | Same data window and scenario budget |
| B2 | Deterministic stress suite | No | No | Fixed shocks documented before evaluation |
| B3 | Tail sampler | No | No | Same sampler, seed, and base shock as EGFC |
| B4 | SCM without evidence gate | No | Yes | Isolates evidence-gate effect |
| B5 | SCM without feasibility gate | Yes | No | Isolates feasibility-gate effect |
| B6 | Full EGFC | Yes | Yes | Proposed pipeline |

If an ablation is not technically supported by the code, implement it as a separate experimental configuration and test that it differs only in the intended gate. Do not compare unmatched settings.

## C. Primary metrics

1. **Hard-constraint violation rate** among evaluated scenarios, with the denominator defined explicitly.
2. **False-pruning rate**, measured only where an independently defined feasible set or trusted reference is available.
3. **Evidence coverage and rejection taxonomy:** missing, duplicate, stale, future-dated, invalid-confidence, low-confidence, or unmapped records.
4. **Held-out risk metrics:** use realized outcomes and suitable VaR/ES coverage, joint scoring, or backtesting where the target is correctly defined.
5. **Trace fidelity:** whether saved evidence IDs, intervention, certificate, model version, and deterministic output reproduce exactly.
6. **Efficiency:** median/p95 runtime, peak memory, number of evaluated scenarios, and cost per accepted scenario.
7. **Robustness:** rolling splits, seeds, threshold changes, graph perturbations, and missing-data perturbations.

Never treat the p95 of generated simulated impacts as realized tail-risk coverage. Simulated scenario severity and out-of-sample risk calibration are different quantities.

## D. Run sequence

### D1. Code and unit checks

From the repository root in PowerShell:

```powershell
git status
git log -1 --oneline
python -m pytest -q tests/test_evidence_gated_stress.py
python scripts/benchmark_evidence_gated_stress.py --draws 64 --seed 42
```

Confirm the test file exists on the exact branch/commit first. Save all output. These are smoke checks, not empirical validation.

### D2. Baseline/ablation evaluation

Implement or configure B1–B6 with shared input manifests. For each run save:
- configuration JSON/YAML;
- input data identifiers and hashes;
- seed and commit SHA;
- raw scenario-level results;
- accepted/rejected scenario records;
- metrics and uncertainty intervals;
- stdout/stderr and elapsed time.

### D3. Holdout evaluation

- [ ] Use only the predeclared final chronological holdout once for final reporting.
- [ ] Compute risk metrics from realized held-out outcomes, not the generated scenarios alone.
- [ ] Report sample size and tail-event count.
- [ ] Use a dependence-aware uncertainty method where justified.
- [ ] Include null/negative results and any failed runs.
- [ ] Check for look-ahead leakage in graph fitting, bounds, thresholds, and source timestamps.

## E. Results ledger

| Run ID | Commit | Data version | Split | Method | Seed | Status | Output path | Notes |
|---|---|---|---|---|---:|---|---|---|
| SMOKE-001 | [SHA] | synthetic fixture | smoke | current benchmark | 42 | [TO RUN] | [PATH] | Not empirical |
| EMP-001 | [SHA] | [version] | train/validation | B1 | [seed] | [TO RUN] | [PATH] | |
| EMP-002 | [SHA] | [version] | train/validation | B2 | [seed] | [TO RUN] | [PATH] | |
| EMP-003 | [SHA] | [version] | train/validation | B3 | [seed] | [TO RUN] | [PATH] | |
| EMP-004 | [SHA] | [version] | train/validation | B4 | [seed] | [TO RUN] | [PATH] | |
| EMP-005 | [SHA] | [version] | train/validation | B5 | [seed] | [TO RUN] | [PATH] | |
| EMP-006 | [SHA] | [version] | train/validation | B6 | [seed] | [TO RUN] | [PATH] | |
| HOLDOUT-001 | [SHA] | [version] | final test | B1–B6 | [seed set] | [TO RUN] | [PATH] | Run once after protocol freeze |

## F. Stop conditions

Stop and repair before interpreting results if:
- tests fail or API response shapes are inconsistent;
- a gate accepts malformed timestamps, non-finite values, or unknown graph nodes;
- output depends on unrecorded external state or unstable random seeds;
- data leakage is detected;
- baseline scenario budgets or input windows are not comparable;
- the result table cannot be regenerated from raw run artifacts.

## G. What this protocol does not establish

Passing these steps alone does not prove causal identification, economic validity, novelty, patentability, or acceptance by a publisher. It establishes a transparent path for testing those claims.
