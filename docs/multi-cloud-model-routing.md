# FinAI multi-cloud model routing

FinAI now treats cloud LLMs as interchangeable reasoning providers behind the existing financial authority, verification and XAI layers.

## Providers

| Provider | FinAI adapter | Default model | Configuration |
| --- | --- | --- | --- |
| Google Gemini | `gemini-cloud` | `gemini-3.8-flash` | `GEMINI_API_KEY` |
| OpenAI | `openai-*` | registry-defined | `OPENAI_API_KEY` |
| Anthropic | `anthropic-claude` | `claude-sonnet-5.5` | `ANTHROPIC_API_KEY` |
| Mistral | `mistral-large` | `mistral-large-latest` | `MISTRAL_API_KEY` |
| OpenRouter | `openrouter-cloud` | `openrouter/auto` | `OPENROUTER_API_KEY` |
| Local/research | `rllm-finqa-4b`, research candidates | registry-defined | local artifacts |

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
ANTHROPIC_MODEL=claude-sonnet-5.5

MISTRAL_API_KEY=
MISTRAL_MODEL=mistral-large-latest

OPENROUTER_API_KEY=
OPENROUTER_MODEL=openrouter/auto

FINAI_LLM_PREFERENCE=
FINAI_LLM_COST_SENSITIVITY=balanced
```

## Safety boundary

Financial calculations, authority decisions, transactions and verification remain system-owned. A cloud LLM only generates language around verified context. Explicit model selection remains deterministic and does not silently fail over.
