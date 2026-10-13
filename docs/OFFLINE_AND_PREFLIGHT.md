# Offline / degraded mode and clean-checkout preflight

## Modes

Set `FINAI_NETWORK_MODE` to one of:

- `online`: remote providers and public market-data sources are eligible under the normal provider/risk rules.
- `degraded`: the model router prefers a local model when the capability and hardware requirements permit it; other remote fallbacks may still be used.
- `offline`: cloud-model generation and the guarded live market-data providers reject network access. The public crypto market-universe cache may still answer while its local cache entry is fresh. A cache miss fails rather than contacting the provider.

An invalid non-empty mode is treated as a configuration error by the network guard; it is not interpreted as permission to call a provider.

## PowerShell

From the repository root:

```powershell
Set-Location "C:\Users\roghe\FinAI"
.\.venv\Scripts\python.exe .\scripts\finai_preflight.py
.\.venv\Scripts\python.exe .\scripts\finai_preflight.py --json
```

To enforce offline mode for the current PowerShell session:

```powershell
$env:FINAI_NETWORK_MODE = "offline"
$env:FINAI_DATA_SENSITIVITY = "restricted"
.\.venv\Scripts\python.exe -m pytest -q tests\test_network_mode_enforcement.py tests\test_model_gateway.py tests\test_response_provider_fallback.py
```

Return to normal connectivity explicitly with:

```powershell
$env:FINAI_NETWORK_MODE = "online"
$env:FINAI_DATA_SENSITIVITY = "standard"
```

These environment variables apply to processes started from that PowerShell session; they do not permanently change Windows settings.

## Local model weights

The rLLM-FinQA 4B adapter uses 4-bit CUDA quantization and therefore requires a compatible NVIDIA CUDA environment. The router now marks that model as GPU-required rather than claiming that CPU-only execution is supported.

The adapter uses `local_files_only=True` and does not download multiple gigabytes during a request. Provision the model files in the Hugging Face cache before selecting offline generation, or set `FINAI_RLLM_MODEL_PATH` to an existing local model directory. This setting must point to model files in the format expected by Transformers.

The optional Sarvam-1 base adapter also uses `local_files_only=True`; set `FINAI_SARVAM_BASE_MODEL_PATH` to an existing local Transformers model directory when it is not available in the Hugging Face cache. Its PEFT adapter directory must also be present locally. Neither local-model path downloads weights automatically during a request.
Relative model paths in `FINAI_RLLM_MODEL_PATH`, `FINAI_SARVAM_BASE_MODEL_PATH`, and `FINAI_EMBEDDING_MODEL_PATH` are resolved from the repository root, not the shell's current working directory. The variables are documented in `.env.example`.

The embedding model used by RAG is separate. `FINAI_RAG_DEVICE` can be set to `cuda` or `cpu`; when unset the embedding adapter chooses CUDA if available and otherwise CPU. RAG still requires the source chunks, SQLite database, FAISS index, and document ID map described by the preflight report.

## What preflight verifies (and does not)

`scripts/finai_preflight.py` is a read-only local presence check. It reports tracked/derived artifact presence, importable dependency availability, and *names only* of configured provider credentials. It never prints key values, connects to providers, downloads datasets, or modifies the checkout.

A clean preflight does **not** prove that API credentials are valid, providers are reachable, model weights are usable, generated indexes have sound retrieval quality, or the application is production-ready. Use the API smoke tests and backend/frontend test suites after preparing licensed source data and generated artifacts.

## Guard scope

Offline guards currently cover the model gateway and direct Gemini/OpenAI/OpenRouter/Anthropic/Mistral provider boundaries, response-service cloud fallback policy, Yahoo Finance quotes/history/discovery/news, CCXT order-book and live market queries, and the public mempool.space mining-statistics adapter. The entire process is not a network sandbox: any future provider or direct HTTP client must use `assert_external_network_allowed` or `assert_cloud_provider_allowed` (or an equivalent explicit policy) before outbound requests.
