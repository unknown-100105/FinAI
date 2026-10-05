# FinAI Audit Evidence Index — 2026-10-04

## Repository target

- Repository: `unknown-100105/FinAI`
- PR: #5
- Base: `feature/end-to-end-finai`
- Head: `feature/professional-token-lab-ui`
- PR remains open and unmerged.
- Final audited branch tip is tracked by the PR's current `head_sha`.

## Software evidence

Owner-reported immediately prior to this audit:
- targeted research tests: 31 passed;
- full pytest suite: 500 passed;
- frontend production build: passed;
- live API smoke checks: passed.

These results predate the final intervention-semantics and benchmark hardening
commits made during the audit. They must be rerun locally on the current head
before claiming the post-change branch is fully verified.

## Current research implementation

The branch now contains:
- forward causal-feasibility interval certificate;
- backward target-cone necessary-interval certificate;
- future-intervention-aware semantics in both directions;
- constrained GFlowNet action masking using both certificate directions;
- persistent incremental descendant-cone recomputation;
- exhaustive-vs-pruned finite-state benchmark;
- CI benchmark artifact generation;
- non-patent literature cross-check;
- duplicate unused research control-plane removal.

## Remote CI

GitHub Actions run #534 currently reports failure for Backend, Frontend, and
Patent mechanism benchmark jobs, with empty step lists. The connected
GitHub job-log endpoint also has no retrievable log blob.

Do not convert this into a claim that the code failed its tests. The precise
statement is: "Remote CI is failing before usable step/log evidence is available."

## Patent/research evidence boundary

The current repository establishes an implemented technical hypothesis and a
controlled finite-state benchmark design. It does not establish:
- novelty;
- inventive step;
- freedom to operate;
- real-market performance;
- causal identification;
- production readiness of research models.

The filing-grade process still requires a professional patent search covering
patent families, non-patent literature, prosecution histories, and the relevant
jurisdiction.

## Required owner-side final commands

Run on the current head:

`git pull origin feature/professional-token-lab-ui`

`pytest -q`

`cd frontend; npm run build; cd ..`

`python scripts/run_patent_mechanism_benchmark.py --output patent-benchmark.json`

Then repeat live API smoke checks through `scripts/verify-finai.ps1` with the
backend running.

## Audit rule

Never present a synthetic or finite-state benchmark as real-financial
validation. Never present a passing software suite as evidence of causal
identification or patent novelty.
