# FinAI multi-cloud model routing

FinAI now treats cloud LLMs as interchangeable reasoning providers behind the existing financial authority, verification and XAI layers.

## Providers

| Provider | FinAI adapter | Default model | Configuration |
| --- | --- | --- | --- |
| Google Gemini | `gemini-cloud` | `gemini-3.8-flash` | `GEMINI_API_KEY` |
| OpenAI | `openai-*` | registry-defined | `OPENAI_API_KEY` |
| Anthropic | `anthropic-claude` | `claude-sonnet-5-5` | `ANTHROPIC_API_KEY` |
| Mistral | `mistral-large` | `mistral-large-latest` | `MISTRAL_API_KEY` |
| OpenRouter | `openrouter-cloud` | `openrouter/auto` | `OPENROUTER_API_KEY` |
| Local/research | `rllm-finqa-4b`, research candidates | registry-defined | local artifacts |
| Optional local Colibrì | `colibri-local` | local Colibrì API model ID | `FINAI_COLIBRI_BASE_URL` (loopback only) |

Provider calls are all behind provider adapters. API keys never enter the frontend.

## Routing

`ModelRouter` performs deterministic policy routing using capability, risk level, configured quality/latency/cost tiers and an optional `FINAI_LLM_PREFERENCE` list.

This is an engineering policy heuristic, not a learned model benchmark. Live latency, price and answer quality need separate empirical measurement before any production policy is declared optimal.

## Runtime configuration

```
OPENAI_API_KEY=
OPENAI_MODEL=
OPENAI_DEEP_MODEL=
OPENAI_FAST_MODEL=

GEMINI_API_KEY=
GEMINI_MODEL=gemini-3.8-flash

ANTHROPIC_API_KEY=
ANTHROPIC_MODEL=claude-sonnet-5-5

MISTRAL_API_KEY=
MISTRAL_MODEL=mistral-large-latest

OPENROUTER_API_KEY=
OPENROUTER_MODEL=openrouter/auto

FINAI_LLM_PREFERENCE=
FINAI_LLM_COST_SENSITIVITY=balanced
```

## Safety boundary

Financial calculations, authority decisions, transactions and verification remain system-owned. A cloud LLM only generates language around verified context. Explicit model selection remains deterministic and does not silently fail over.


## Adaptive execution constraints

The router can incorporate runtime execution constraints in addition to capability and risk:

- `online`: normal provider selection.
- `degraded`: prefers local execution while retaining configured cloud candidates.
- `offline`: local-only execution.
- `restricted` data sensitivity: local-only execution.

The route-preview API accepts `network_mode` and `data_sensitivity` and returns `constraints_applied` so the decision remains auditable.

Runtime environment defaults:

~~~text
FINAI_NETWORK_MODE=online
FINAI_DATA_SENSITIVITY=standard
FINAI_ALLOWED_PROVIDERS=
~~~

### Optional Colibrì local server

When `FINAI_COLIBRI_BASE_URL` points to a local loopback `/v1` server,
`colibri-local` is added to eligible local models and can be selected in
offline/restricted mode. It uses the local OpenAI-compatible
`/v1/chat/completions` endpoint. The adapter rejects non-loopback endpoints and
redirects; it does not silently send prompts to remote hosts.

The Colibrì engine and weights must be installed separately. This FinAI adapter
does not implement disk/VRAM/RAM expert streaming, nor does it prove local model
quality or latency. See [the Colibrì API guide](https://github.com/JustVugg/colibri/blob/main/docs/api.md)
and [Windows guide](https://github.com/JustVugg/colibri/blob/main/docs/windows.md),
then [FinAI's offline/preflight guide](OFFLINE_AND_PREFLIGHT.md).


This is an execution-policy boundary, not a claim that every cloud provider has identical privacy, residency or retention characteristics. Provider-specific compliance should be configured separately where required.

## Hardware-aware orchestration

FinAI also evaluates local resource availability before choosing a local model:

- CPU core count
- system RAM
- currently available GPU VRAM and CUDA availability
- free local storage

The model registry exposes conservative routing metadata (`min_ram_gb`, `preferred_vram_gb`, `gpu_required`). These values are configuration hints for orchestration, not measured model-memory benchmarks.

Execution modes are reported as:

- `local_gpu`
- `local_ram`
- `cloud`
- `cloud_fallback`

The route response includes `resource_fit`, `resource_reason` and the current hardware snapshot. When a local candidate does not satisfy its configured resource profile, it is removed from the eligible local candidate set; cloud fallback is still subject to network and data-sensitivity policy.
