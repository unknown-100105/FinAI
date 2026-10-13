# FinAI completion status — 13 October 2026

Repository: `unknown-100105/FinAI`
Working branch: `ai/finai-completion`
Pull request: https://github.com/unknown-100105/FinAI/pull/6 (draft; not merged)

## Changes added in this continuation

- The hybrid engine attaches a `capability_execution_plan` diagnostic to each result returned from `FinAIHybridEngine.process`, without replacing the legacy `execution_plan`.
- XAI traces record the diagnostic in a separate field, preserving the existing authority/execution decision.
- Canonical calculation-intent detection was extended for EMI/SIP/loan/tax-style requests.
- The RAG retriever now fails early with concrete missing-asset instructions rather than beginning an embedding-model load when the SQLite/FAISS/ID-map files are missing.
- The FAISS index builder validates vector count, ID-map order/uniqueness, checkpoint consistency, embedding model identity, and vector dimension. Ambiguous non-empty indexes fail closed; embedding device selection can use `FINAI_RAG_DEVICE` or CPU/CUDA auto-detection.
- Added a local-only preflight report (`scripts/finai_preflight.py`) and Windows/offline operations guide (`docs/OFFLINE_AND_PREFLIGHT.md`). It checks package/file presence and credential names without printing secrets or contacting services.
- Added centralized network-mode policy and guards for cloud generation at both gateway and direct Gemini/OpenAI/OpenRouter/Anthropic/Mistral provider boundaries, cloud fallback selection, Yahoo Finance quote/history/search/news, CCXT live order-book/market requests, and mempool.space mining-statistics calls. Restricted data and provider allow-list policy are also checked at direct cloud-provider boundaries. The local rLLM adapter now requires local weight files and uses Hugging Face `local_files_only=True`; the Qwen embedding adapter uses local cache-only resolution in offline mode.
- Corrected rLLM registry metadata so the current quantized adapter is not advertised as CPU-capable. rLLM, Sarvam, and optional local embedding model paths now resolve relative to the repository root, and the Sarvam base model is also local-only with early validation of its adapter directory.
- Added focused integration, direct cloud-provider policy, offline market-provider, local model-loading, preflight, and FAISS-resume tests to the artifact-independent CI list. The preflight dependency list now includes core analytics, provider, local-model, and test packages.
- Added an opt-in `colibri-local` model adapter that talks only to loopback Colibrì OpenAI-compatible `/v1/chat/completions`. The adapter is disabled when `FINAI_COLIBRI_BASE_URL` is blank; it refuses non-loopback targets and redirects. The third-party engine and model weights are **not** bundled; this is an integration seam, not a completed FinAI implementation of NVMe expert streaming. Preflight reports configuration presence without exposing the local API key or checking service reachability.

## Verification caveat

These changes were written to the remote branch through GitHub file commits. This editing environment did not run the project’s Python or Node test suites. Tests must be executed locally, and GitHub Actions must report success, before treating these edits as validated.

Recent GitHub Actions runs ended in failure within seconds and the job API returned empty steps; the job log download returned a missing log blob. The failure cause is therefore **unknown**, not proven to be a code failure or a successful test run. Inspect the current Actions page and repository Actions/billing/runner availability, then rerun the workflow.

## Still required before a complete or production-ready claim

1. Reconcile the user's saved local stash (Frontend 2.0 design system/API client, artifact bootstrap and smoke scripts, configuration, parser hardening, and other backend changes). It is not accessible through remote repository editing. Do not drop or blindly pop it.
2. Run backend regression tests, frontend build/lint, and API smoke tests against the current branch; resolve failures and review warnings.
3. Provision the generated TF-IDF router artifact and approved/licensed RAG source chunks/indexes for a clean clone. The source datasets and large generated indexes are not included here.
4. The shared network guard covers the named adapters above; it is not an OS-level sandbox for arbitrary direct HTTP calls or future providers. Audit every outbound integration and test that offline blocks the entire application request path, not only individual adapters.
5. Install and test the separately released Colibrì engine/model locally through `colibri-local`, then benchmark its actual model placement and generation. FinAI currently provides only a loopback API adapter; it does not implement GPU/RAM/NVMe streaming itself. Also decide whether to maintain a native Calibre/Colibrì-compatible engine adapter or rely on the external runtime.
6. Validate configured model providers with live server-side credentials, quotas, reachable endpoints, and end-to-end fallback tests.
7. Replace demo authentication/session semantics, sample account/payment identifiers, and mock bank operations before production use.
8. Implement/integrate the ResilientPay/DLT settlement bridge with explicit authorization, idempotency, reconciliation, recovery, local/test-network coverage, and a security review. No live bank or DLT settlement bridge is claimed here.
9. Expand causal-risk evaluation with realistically sourced, chronologically held-out datasets, baselines, ablations, repeated runs, false-prune testing, runtime/memory and uncertainty reporting. The current benchmark is a finite toy experiment, not real-market validation or a patentability determination.
10. Complete accessibility/mobile/runtime testing for Frontend 2.0, then merge only after reproducible local verification and passing hosted CI.

## Local verification commands

From Windows PowerShell:

```powershell
Set-Location "C:\Users\roghe\FinAI"
git status --short
git switch ai/finai-completion
git pull --ff-only origin ai/finai-completion
.\.venv\Scripts\python.exe -m pytest -q
Set-Location .\frontend
npm ci
npm run build
npm run lint
```

Keep the working tree and local stash intact until their changes are safely reconciled.


## Additional research prototypes committed in this continuation

- Added finance_engine/counterfactual_screening.py, its test suite and deterministic synthetic benchmark from the separate patent-screening work branch. The component computes conservative bounds over bounded linear DAGs and may mask only actions certified as unable to reach a target interval under supplied bounds. RETAIN is not a feasibility guarantee.
- Added finance_engine/epcrp.py as a separate evidence-gated paired-world reference implementation, with tests and a disclosure note. It evaluates a single time-scoped static DAG snapshot; it does not model lagged time series, discover causal truth, or establish patentability.
- Fixed request-path diagnostic planning so retrieval/model/verification steps are not listed solely because those capabilities happen to be available when the current request did not use them.
- Added both prototype test suites to artifact-independent CI and added the screening synthetic smoke benchmark to the research benchmark job.

## Validation status after these changes

The files are committed to the remote branch, but full Windows/Node test execution is not available in this editing session. Run tests/test_epcrp.py, tests/test_counterfactual_screening.py, the complete backend suite, frontend build/lint, and both research benchmarks against the current checkout. Do not label this production-ready until those results are reviewed. The synthetic benchmark is not real-market evidence or a patentability conclusion.


## Opt-in research API

Added app/patent_mechanism_api.py with EPCRP and bounded-DAG feasibility-screen endpoints and added endpoint tests to CI. app/main.py mounts this router only when FINAI_ENABLE_RESEARCH_PATENT_ENDPOINTS is explicitly enabled. The handlers use caller-supplied models and are not connected to bank execution or production authorization. Test execution on the final branch remains pending because the current hosted Actions runs fail before exposing any job steps.

The opt-in experimental HTTP routes now also fail closed unless a bearer token of at least 32 characters is configured via `FINAI_RESEARCH_API_TOKEN`; tests include missing/invalid token cases. This is an extra guard, not a substitute for deployment authentication/rate limiting.
