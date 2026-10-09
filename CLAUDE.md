# Claude Code instructions for FinAI

Read `AGENTS.md` first; it is the shared repository contract.

Before changes:
- Inspect the current branch, working tree, module, call sites, and relevant tests.
- Prefer targeted patches over broad rewrites.
- Never overwrite user work or force-push.
- Do not modify secrets or local model/data assets.

For every implementation:
- Add regression tests for the intended behaviour and edge cases.
- Preserve deterministic financial calculation authority, evidence provenance, policy restrictions, and XAI/verification contracts.
- Keep provider calls bounded by timeouts and safe fallback rules.
- Treat causal outputs and calibration as research unless validated out of sample.
- Run focused tests and report the exact outcomes; never claim tests passed without running them.

Before finishing:
- Review the diff for accidental changes and credentials.
- Identify anything not tested because it requires local assets, provider keys, network access, or a GPU.
- Do not make patentability claims; document hypotheses and required prior-art work.
