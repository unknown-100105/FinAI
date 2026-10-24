# FinAI Brain, Model Readiness, and Local Runtime Integration

**Status:** implementation/runbook contract; not a production certification.

This document defines what FinAI's Brain status means, how to configure model providers, how to validate local inference, and what remains before a release can be called complete.

## 1. Brain architecture and ownership

The Brain is a diagnostic view over the existing pipeline. It is not an alternate authority engine and must never bypass the policy, deterministic finance, risk-control, evidence-verification, or XAI paths.

| Layer | Responsibility | Required release evidence |
|---|---|---|
| Intent/domain routing | Select a supported intent and execution path | trained router artifact; intent regression suite |
| Policy and authority | Enforce allowed actions and risk constraints | negative/denial tests; authority contract tests |
| Deterministic finance | Produce authoritative calculations | calculation tests, finite-input tests, boundary tests |
| Market data | Retrieve external or cached observations | mocked provider tests plus opt-in live smoke checks |
| Structured knowledge | Resolve catalog and regulatory scope | source/date/provenance checks for changing rules |
| RAG | Retrieve supporting source chunks | SQLite + FAISS + document-ID map; retrieval benchmark |
| Model generation | Explain verified system-owned context | configured provider/model plus a successful opt-in inference test |
| Verification and XAI | Check claims and preserve trace/evidence lineage | verifier regression tests; trace privacy/security tests |
| Resource orchestration | Select eligible model within hardware constraints | route tests against actual hardware snapshot |
| Offline inference | Use local-only inference when configured | local weights/runtime and a no-network test |
| Causal-risk research | Explore graph/intervention/stress hypotheses | reproducible benchmarks and chronological empirical evaluation |
| ResilientPay | Maintain a local payment-intent journal and adapter contract | ledger integrity and idempotency tests; live settlement remains a separate integration |

GET /api/v1/system/brain-status is deliberately diagnostic. File presence, environment variables, model registry entries, or synthetic benchmark passes are not evidence of live inference, causal identification, investment performance, or production safety.

## 2. Model configuration

Provider credentials belong only in the server environment or a local ignored .env file. Never place secrets in frontend variables, committed files, screenshots, or logs.

| Provider/model family | Configuration | What must be verified |
|---|---|---|
| OpenAI | OPENAI_API_KEY and model overrides documented in docs/multi-cloud-model-routing.md | valid credential, allowed model ID, opt-in smoke request |
| Gemini | GEMINI_API_KEY, optional GEMINI_MODEL | valid credential, quota/model access, opt-in smoke request |
| OpenRouter | OPENROUTER_API_KEY, optional OPENROUTER_MODEL | provider/model access, quota, opt-in smoke request |
| Anthropic | ANTHROPIC_API_KEY, optional ANTHROPIC_MODEL | valid credential, model access, opt-in smoke request |
| Mistral | MISTRAL_API_KEY, optional MISTRAL_MODEL | valid credential, model access, opt-in smoke request |
| rLLM-FinQA local | FINAI_RLLM_MODEL_PATH or a prepared Hugging Face cache snapshot | model config and weights exist, supported CUDA/quantization stack, actual generation test |
| Qwen embedding | FINAI_EMBEDDING_MODEL_PATH or prepared cache snapshot | weights load locally, embedding dimensions/index compatibility, retrieval benchmark |
| Colibrì local | FINAI_COLIBRI_BASE_URL, FINAI_COLIBRI_MODEL, optional local server key | server/model health and a local inference test; endpoint must remain loopback-only |

Model registry metadata and routing quality/latency/cost tiers are configuration hints, not benchmarked performance. A credential being present is not proof that the provider is reachable. A local model folder being present is not proof that its weights load. Route preview is not an inference call.

### Safe provider smoke checks

From the repository root, the no-network configuration check is:

~~~powershell
.\.venv\Scripts\python.exe scripts\smoke_llm_providers.py
~~~

A real provider request must be a deliberate opt-in because it requires network access and may incur charges:

~~~powershell
$env:FINAI_RUN_LIVE_PROVIDER_SMOKE = "1"
.\.venv\Scripts\python.exe scripts\smoke_llm_providers.py --live
~~~

Use synthetic, non-sensitive test prompts only. Do not run a live smoke check in offline/restricted mode. Capture provider name, model ID, result status and latency—not secrets or private prompt contents.

## 3. Local-only and offline mode

~~~powershell
$env:FINAI_NETWORK_MODE = "offline"
$env:FINAI_DATA_SENSITIVITY = "restricted"
.\.venv\Scripts\python.exe scripts\finai_preflight.py --json
.\.venv\Scripts\python.exe -m pytest -q tests\test_network_mode_enforcement.py tests\test_model_gateway.py tests\test_response_provider_fallback.py tests\test_colibri_adapter.py
~~~

Offline mode is a policy constraint, not an OS-level network sandbox. Every new provider or HTTP client must call the shared network-policy guard before external requests. Do not describe the system as fully air-gapped without OS/network-level enforcement and a separate audit.

## 4. Calibre vs. Colibrì: integration boundary

The current repository documents and implements an optional **Colibrì** local inference adapter at llm/colibri_adapter.py. It calls an OpenAI-compatible local server; FinAI does not bundle the engine, download its weights, or implement its GPU/RAM/NVMe weight-streaming runtime.

The word **Calibre** can refer to different products or runtimes. No Calibre-specific runtime contract, package, endpoint, or model ID is currently declared by this repository. Do not silently treat Calibre and Colibrì as the same dependency. Before adding a distinct Calibre adapter, specify its exact upstream repository/package, license/version, supported API/protocol, model format, process lifecycle, authentication, and health endpoint. Then implement it behind a separate adapter and model-registry entry with mocked contract tests; do not couple FinAI's policy/authority layer to vendor-specific APIs.

If “Calibre” was intended to mean the already-present Colibrì runtime, use the Colibrì configuration above and follow the upstream [Windows guide](https://github.com/JustVugg/colibri/blob/main/docs/windows.md) and [API guide](https://github.com/JustVugg/colibri/blob/main/docs/api.md). Bind the local server to loopback only. Do not expose a local inference port to the LAN or internet.

## 5. Reproducible data/model artifacts

A clean Git checkout does not include all large datasets, trained model weights, or generated RAG indexes.

1. Obtain only approved/licensed source data and record source URL, license, retrieval date, and checksum.
2. Rebuild the intent-router artifact using the training JSONL documented by scripts/finai_preflight.py.
3. Prepare domain chunks under data/domain_chunks/.
4. Run scripts/build_rag_index.py, then scripts/build_rag_faiss.py.
5. Run preflight and review every missing package/artifact.
6. Run focused tests, the full regression suite, frontend build/lint, and deterministic research benchmarks.
7. Run live provider/model checks only when credentials, quota, network policy, and budget are explicitly approved.

Do not commit API keys, private financial records, raw licensed corpora, model weights, local caches, or runtime traces.

## 6. Release acceptance checklist

- [ ] GitHub Actions runner executes workflow steps and exposes useful failure logs.
- [ ] Full backend regression suite passes on a reproducible checkout.
- [ ] Frontend npm ci, npm run build, and npm run lint pass.
- [ ] Browser chat completes a request through the configured backend and selected provider/model.
- [ ] Route selection filters unconfigured models and respects offline/restricted/resource constraints.
- [ ] RAG retrieval returns source IDs and passes recall/MRR and evidence-verifier regression checks.
- [ ] Brain diagnostics distinguish code presence, artifacts, configuration, runtime reachability, and actual inference.
- [ ] Security tests cover auth, session isolation, trace redaction/retention, and secret non-disclosure.
- [ ] Financial tools use deterministic calculations and fail closed for unsupported/unauthorized actions.
- [ ] Research benchmarks are reproducible; synthetic metrics are not described as real-market validation.
- [ ] ResilientPay is labelled simulation-only until a separately tested bank/ledger settlement adapter exists.
- [ ] Release notes state exact commit, test counts, benchmark artifacts, configured providers, and known limitations.

A release is not complete merely because a UI renders or a model appears in a registry. Every enabled capability must have an executable path, tests, operational configuration, and an explicit failure mode.
