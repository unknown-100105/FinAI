# FinAI repository agent instructions

## Mission
Make small, testable, auditable changes to FinAI. Preserve deterministic financial calculations and policy/safety boundaries. Do not claim a feature works unless code and tests demonstrate it.

## Required workflow
1. Inspect the relevant implementation, tests, configuration, and callers before editing.
2. State assumptions and identify files that will change.
3. Add or update focused tests for every behaviour change.
4. Run targeted tests first, then relevant regression tests and frontend build where applicable.
5. Inspect the final diff for secrets, generated artifacts, unrelated edits, and unsupported claims.
6. Report exact commands and results. If a command was not run, say so.

## Financial safety invariants
- Deterministic finance/portfolio engines remain authoritative for calculations.
- Models explain verified results; they must not invent or silently change numeric results.
- Preserve evidence provenance and run response/claim verification.
- Never route restricted data to cloud providers or bypass offline/provider allow-list rules.
- Explicit model selection must not silently fall back to a different model.
- Treat causal discovery as research evidence, not identified causation by default.
- Label experimental risk models, calibration and patent hypotheses honestly.

## Data, secrets, and dependencies
- Never commit API keys, personal data, downloaded model weights, full RAG corpora, or local environment files.
- Keep credentials in environment variables and redact them from logs.
- Pin or constrain new dependencies; avoid adding heavyweight packages for optional features without a demonstrated need.
- Do not change Python versions or core dependency constraints without compatibility checks.
- Do not silently enable a model just because its registry entry exists.

## Testing and completion claims
- Add deterministic tests and mocked provider tests; keep live API tests opt-in.
- Benchmark competing algorithms on identical data, seeds, and evaluation splits.
- Use chronological/walk-forward splits for financial time series.
- Never describe a prototype, mock, registry entry, or small synthetic benchmark as production validation.
- Never state patentability or novelty as fact without qualified prior-art/legal review.

## Scope control
- Do not rewrite unrelated modules.
- Do not merge branches or alter main unless explicitly authorized.
- Preserve user changes and existing branches.
- Final response must list changed files, tests actually run, failures/blockers, and next local verification commands.
