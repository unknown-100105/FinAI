# EGFC Related Work and Prior-Art Search Map

**Status:** preliminary search notes, not a novelty opinion or a complete systematic review.  
**Last reviewed:** 2026-10-20. Search and verify each citation again before submission.

## 1. Directly relevant work found

### Causal stress testing

Gao, Mishra, and Ramazzotti, “Causal data science for financial stress testing,” *Journal of Computational Science*, vol. 26, pp. 294–304 (2018), DOI [10.1016/j.jocs.2018.04.003](https://doi.org/10.1016/j.jocs.2018.04.003).

Why it matters: the paper already applies causal networks to financial stress scenario generation. Therefore, FinAI cannot claim novelty merely for combining causal graphs, machine learning, and financial stress testing.

### Counterfactual causal reasoning

J. Pearl, *Causality: Models, Reasoning, and Inference*, 2nd ed., Cambridge University Press (2009).

Why it matters: counterfactual reasoning is established methodology. The paper must state its structural assumptions and avoid equating a programmatically generated counterfactual with an identified causal effect.

### Risk calibration and uncertainty

M. Ivancevic, K. A. Nguyen, and Z. Luo, “Reliable value at risk estimation with conformal prediction,” *Risk Management*, vol. 28, article 59 (2026), DOI [10.1057/s41283-026-00243-6](https://doi.org/10.1057/s41283-026-00243-6).

Why it matters: risk estimates need uncertainty/calibration analysis; scenario severity alone is insufficient. Verify the final bibliographic record, publication status, and methodological relevance before citing.

## 2. Candidate gap to test, not assume

The candidate gap is an auditable *control-flow composition*: (i) evidence provenance/freshness/confidence/claim coverage, (ii) model-conditional feasibility certification, (iii) fail-closed scenario admission, and (iv) stored rejection/trace records, evaluated with matched baselines and gate ablations.

This is only a search hypothesis. It must be narrowed or abandoned if prior work already provides the same mechanism. A combination of known components is not automatically novel or patentable.

## 3. Search queries to execute

Search IEEE Xplore, ACM Digital Library, Scopus/Web of Science, Google Scholar, Crossref, arXiv, SSRN, and relevant patent databases:

- “evidence-aware financial stress testing”
- “provenance constrained counterfactual generation”
- “causal feasibility certificate stress scenario”
- “constraint-aware counterfactual financial risk”
- “causal graph feasibility pruning tail risk”
- “evidence-gated scenario generation”
- “financial stress testing evidence provenance”
- “counterfactual scenario validation causal graph”
- “constrained generative stress testing finance”
- “risk scenario rejection false pruning calibration”

For each search, record the exact query, date, database, number of results screened, and inclusion/exclusion rationale.

## 4. Prior-art comparison table

Complete this from the full text, not abstracts alone.

| Reference | Domain | Evidence provenance gate | Feasibility certificate | Fail-closed rejection | Scenario-level audit trace | Realized holdout validation |
|---|---|---|---|---|---|---|
| Gao et al. (2018) | Financial causal stress testing | [VERIFY] | [VERIFY] | [VERIFY] | [VERIFY] | [VERIFY] |
| Pearl (2009) | General causal inference | Not a stress-testing pipeline | Not applicable | Not applicable | General theory | Not applicable |
| Additional papers/patents | [TO FILL] | [TO FILL] | [TO FILL] | [TO FILL] | [TO FILL] | [TO FILL] |

Do not fill a cell with “no” unless the full paper/patent has been checked. Use “not established from available text” where appropriate.

## 5. Patent search and publication ethics

- Search patent databases by mechanism and claim language, not only the project name.
- Record jurisdictions, application/publication numbers, family members, filing dates, and claim scope.
- Ask qualified patent counsel to assess claimability and filing strategy before public disclosure if a patent filing is genuinely contemplated.
- Do not state “first,” “unique,” “novel,” or “patentable” solely from this preliminary search.
- Keep publication and patent disclosure timelines coordinated with the institution's IP policy.
