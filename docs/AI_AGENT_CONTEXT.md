# FinAI AI-agent context synchronization

## Purpose
Use a single repository contract across coding agents so changes remain consistent when using Claude Code, Gemini CLI, GitHub Copilot, or other tools. `AGENTS.md` is the canonical cross-agent rule set; `CLAUDE.md` adds Claude-specific reminders; `GEMINI.md` remains the Gemini entry point.

## Calibre/context-manager integration
Calibre is treated as an agent context/configuration synchronizer, not as an LLM provider or a financial calibration library. Do not add a Python package called `calibre` merely to satisfy the name. Verify the exact Calibre tool/repository and version intended by the project owner before automating its commands.

The intended synchronization outcome is:
- `AGENTS.md`: canonical shared engineering and safety rules.
- `CLAUDE.md`: Claude Code entry point that references the canonical rules.
- `GEMINI.md`: Gemini entry point that references the same rules while preserving its existing read-only audit policy.
- Tool-specific config files: only generated or edited using the documented Calibre workflow after inspecting its configuration and ensuring it does not overwrite project-specific policies.

## Safe setup procedure
1. Back up/checkpoint the repository before running a context synchronization tool.
2. Read the tool's official documentation and inspect the current configuration.
3. Run its preview/diff mode if available.
4. Verify that generated files preserve FinAI's financial-safety, testing, no-secret, and research-honesty rules.
5. Inspect `git diff`; reject broad rewrites or removal of tool-specific protections.
6. Commit only the reviewed output.

## Current limitation
The repository now has a canonical `AGENTS.md` and a Claude entry point. Calibre itself has not been executed from this GitHub editing session, so no claim is made that its generated configuration is synchronized or that the tool is installed.
