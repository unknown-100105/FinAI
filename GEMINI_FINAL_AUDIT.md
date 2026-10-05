# FinAI — Final Gemini Independent Audit

## Role

Gemini is an independent, read-only reviewer for the FinAI repository.

It must not:
- modify, create, delete, rename, or move files;
- execute shell or git commands;
- create commits or push changes;
- use MCP tools that mutate repository state.

The human repository owner and ChatGPT are the change authorities.

## Audit target

Branch: `feature/professional-token-lab-ui`

Audit the complete repository after the implementation phase. Do not assume that passing tests prove statistical correctness.

## Required audit areas

### 1. Causal discovery
- NOTEARS objective, acyclicity constraint, optimization diagnostics.
- Input validation and numerical stability.
- Temporal discovery lag alignment and leakage.
- Stability windows and consensus selection.
- Direction conflicts and cycle handling.

### 2. Empirical calibration
- Chronological train/test separation.
- Standardization and leakage.
- Regularization and multicollinearity.
- Moving-block bootstrap logic.
- Confidence-interval interpretation.
- Clear distinction between association and identified causal effects.

### 3. Tail-risk modeling
- Dependence model and correlation handling.
- Shock scaling and dimensional consistency.
- Tail thresholding.
- Scenario reproducibility.
- Comparison with future t-Copula/GFlowNet extensions.

### 4. Structural counterfactuals
- SCM intervention semantics.
- Downstream propagation.
- Explicit risk-calibration provenance.
- Research graph approval boundary.
- Production decision isolation.

### 5. Temporal GNN
- Architecture correctness.
- Training/inference implementation.
- Device handling.
- Determinism.
- Evaluation metrics.
- Overfitting and temporal leakage.

### 6. GFlowNet research prototype
- Objective and flow consistency.
- Sampling validity.
- Constraint handling.
- Reproducibility.
- Distinction between prototype and production-ready generative model.

### 7. Multimodal graph
- Typed node/edge representation.
- Fusion of numerical, textual, event, and entity modalities.
- Provenance.
- Missing-modality behavior.
- Graph consistency.

### 8. Neuro-symbolic layer
- Rule validation.
- Hard constraints vs soft model suggestions.
- Deterministic rejection semantics.
- Auditability.

### 9. API/security
- Request-size limits.
- NaN/Inf validation.
- Error handling and information leakage.
- Expensive-computation controls.
- Endpoint consistency.
- Research-only boundaries.

### 10. Frontend
- API contract compatibility.
- Honest display of research/training status.
- Loading/error states.
- No false claims such as trained TGAT/GFlowNet when not verified.

## Evidence standard

For every finding provide:

- Severity: CRITICAL / HIGH / MEDIUM / LOW
- File
- Function/class
- Exact issue
- Why it matters
- Minimal evidence
- Recommended fix
- Regression test

Also identify:
- verified strengths
- statistical/research limitations
- security/API risks
- missing tests
- dead or misleading code

Do not provide an overall score or ranking.

## Final acceptance checklist

The final audit should explicitly check:

- [ ] full test suite
- [ ] backend API smoke tests
- [ ] frontend production build
- [ ] causal discovery validation
- [ ] empirical calibration
- [ ] correlation-aware tail scenarios
- [ ] counterfactual engine
- [ ] approval gate
- [ ] temporal GNN training/inference
- [ ] GFlowNet prototype
- [ ] multimodal graph
- [ ] neuro-symbolic rules
- [ ] regime-shift benchmark
- [ ] documentation consistency
- [ ] no untracked or undeclared production-only claims

## Important limitation

A passing implementation is not evidence of causal identification. The audit must distinguish engineering correctness, empirical predictive validity, and causal identification.
