# FinAI Audit Readiness — 2026-10-04

## Verified software checkpoint

The current PR head is `feature/professional-token-lab-ui`.

The owner-reported local verification immediately before this audit is:
- backend: 500 passed;
- targeted research tests: 31 passed;
- frontend production build: passed;
- live API smoke checks: passed.

These local results are separate from GitHub Actions and should be retained as the local acceptance evidence.

## GitHub CI status

PR #5 has an open state and is not merged.

The latest visible GitHub Actions run currently attached to the final branch
head is run #520 (and subsequent runs in the same series) and its Backend,
Frontend, and Patent mechanism jobs complete with `failure` while exposing
empty step lists. The connector cannot retrieve a failure log because the job
log blob is unavailable. Therefore remote CI is **not green**, but the available
metadata also does not provide evidence that repository test steps executed.
This is an unresolved CI-environment/runner issue and must be disclosed as such
until the repository owner can rerun the workflow in GitHub and inspect the native
Actions logs.

## Research mechanism boundary

The patent-oriented mechanism is a research path, not a transaction
authorization mechanism:

`partial state -> cheap causal-feasibility certificate -> action masking ->
optional adaptive pruning -> expensive structural/tail evaluation of survivors`.

The bidirectional extension adds a second necessary-condition screen derived by
backward propagation from the target interval through the target's ancestor cone.

The certificate is conservative only under its stated linear-DAG assumptions and
explicit bounds. A surviving candidate is not proven feasible; it is only not
proven infeasible by the certificate.

## Patent evidence boundary

Current documentation supports a working patent hypothesis and an initial
prior-art stress test. It does not establish novelty, inventive step, or
freedom to operate.

A filing-grade opinion still requires a professional patent search covering
patent families, non-patent literature, prosecution histories, and the relevant
jurisdiction.

## Data-dependent work that remains

The repository can now execute the controlled benchmark and the future-holdout
research infrastructure, but real-data validation still requires:
- a point-in-time frozen financial dataset with publication/event timestamps;
- chronological train/validation/test splits;
- empirical calibration and stability analysis;
- real high-risk trajectory recall and false-pruning measurement;
- ablations and OOD tests;
- independent patent counsel review.

## Audit conclusion

The correct audit position is:
- software regression: locally verified;
- frontend build: locally verified;
- causal-feasibility implementation: implemented and tested;
- bidirectional mechanism: implemented as a research-screening extension and
  integrated into constrained generation;
- controlled patent-mechanism benchmark: executable and included in CI/final local verification;
- forward + backward certificates: intervention-aware so future generator actions
  do not incorrectly constrain upstream causes;
- incremental interval benchmark: persistent descendant-cone update path tested;
- real financial evidence: pending;
- legal patentability conclusion: pending professional search/counsel.
