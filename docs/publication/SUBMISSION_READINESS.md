# FinAI Publication Submission Readiness

**Paper:** Evidence-Gated, Feasibility-Certified Counterfactual Stress Testing for Financial Risk Analysis  
**Status:** preparation package; not ready for submission until all blocking items are closed.

## 1. Current evidence-based status

| Area | Status | Why |
|---|---|---|
| Candidate research question | Drafted | Needs narrowing after systematic related-work review |
| Manuscript structure | Drafted | Results are intentionally blank |
| Existing code mechanism | Present on feature branch | Exact commit requires test and integration validation |
| Synthetic smoke benchmark | Implemented | It is not empirical evidence |
| Real-data evaluation | Not verified | No recorded chronological holdout results supplied |
| Baselines/ablations | Protocol drafted | Need execution and result artifacts |
| Calibration and false-pruning analysis | Not verified | Need ground-truth/held-out evaluation |
| Prior-art review | Preliminary | Not complete; no novelty conclusion |
| Author list/affiliations/approvals | Pending | Must be completed by the actual contributors |
| Publisher formatting and disclosure | Pending | Depends on final venue and author contribution |

## 2. Technical release gate

- [ ] Identify the exact commit used for experiments.
- [ ] Run the repository preflight and full backend tests.
- [ ] Run focused tests for evidence gate, feasibility, stress endpoint, and deterministic engine.
- [ ] Run frontend production build and integration checks for the complete application.
- [ ] Run the smoke benchmark with fixed seed and archive output.
- [ ] Inspect CI results and preserve logs for failures.
- [ ] Confirm no secrets, licensed data, or personal financial data are accidentally committed.
- [ ] Confirm endpoint schemas and returned fields match the documented API.
- [ ] Test invalid inputs, non-finite numbers, malformed timestamps, empty evidence, duplicate IDs, and extreme bounds.
- [ ] Review model assumptions and units with a domain-qualified reviewer.

## 3. Empirical release gate

- [ ] Select and document a legally usable real dataset.
- [ ] Freeze graph, bounds, metrics, splits, and baselines before final holdout evaluation.
- [ ] Run matched baseline and ablation experiments.
- [ ] Report hard-constraint violation and false-pruning rates.
- [ ] Report realized held-out risk calibration/coverage only where the outcome and metric are valid.
- [ ] Report runtime, memory, uncertainty, sample size, and tail-event count.
- [ ] Provide complete reproducibility manifests and raw machine-readable outputs.
- [ ] Explain all failures and negative results.
- [ ] Replace manuscript placeholders only with verified outputs.

## 4. Manuscript and ethics gate

- [ ] Finish the systematic related-work and patent prior-art search.
- [ ] Verify every citation, DOI, title, authorship, year, and publication status.
- [ ] Narrow claims to what the evidence supports.
- [ ] Include limitations about supplied graph assumptions, evidence mapping, default bounds, and synthetic evaluation.
- [ ] Confirm every author meets authorship requirements and approves the final manuscript.
- [ ] Complete affiliations, acknowledgements, funding/conflict statements, and data/code availability statements.
- [ ] Follow the selected venue's template and current author policies.
- [ ] Disclose AI-generated article content when required by the selected publisher; IEEE guidance requires identifying AI-generated content and affected sections in the acknowledgements.
- [ ] Produce matching source manuscript and PDF according to the target venue's submission requirements.
- [ ] Have a human domain expert and language reviewer inspect the final draft.
- [ ] Submit to one journal at a time and avoid simultaneous duplicate submissions.

## 5. IEEE Access requirements to re-check before submission

Official pages:
- Preparing an article: https://ieeeaccess.ieee.org/authors/preparing-your-article/
- Submission guidelines: https://ieeeaccess.ieee.org/authors/submission-guidelines/
- Reproducibility program: https://ieeeaccess.ieee.org/authors/reproducibility/

The official guidance says submissions require the prescribed template and matching source/PDF files; it also states that AI-generated article content must be disclosed with the system and affected sections identified. Check the live requirements and fees immediately before submission.

## 6. Final decision rule

**Do not submit** if the results section contains placeholders, benchmark results are synthetic but described as empirical, citations are unverified, the baseline comparison is incomplete, or the paper claims causal identification without an adequate identification argument.

**Ready for advisor review** means the manuscript and protocol are coherent, assumptions are visible, and remaining empirical gaps are explicit.  
**Ready for submission** requires the empirical, technical, authorship, ethics, and venue-specific gates above to be complete.
