from dataclasses import dataclass
import os
from typing import Tuple


@dataclass(frozen=True)
class ModelSpec:
    model_id: str
    model_name: str
    role: str
    capabilities: Tuple[str, ...]
    enabled: bool = False
    provider: str = "local"
    quality_tier: int = 2
    latency_tier: int = 2
    cost_tier: int = 2
    routing_priority: int = 100
    min_ram_gb: float = 0.0
    preferred_vram_gb: float = 0.0
    gpu_required: bool = False


MODEL_REGISTRY = {
    "openai-astra": ModelSpec(
        model_id="openai-astra",
        model_name="gpt-6-astra",
        role="openai_deep_reasoning",
        capabilities=("response_generation","financial_qa","financial_reasoning","financial_explanation","tool_assisted_qa"),
        enabled=False,
        provider="openai",
        quality_tier=3,
        latency_tier=2,
        cost_tier=3,
        routing_priority=85,
    ),

    "openai-sol": ModelSpec(
        model_id="openai-sol",
        model_name="gpt-6.1-sol",
        role="openai_balanced_reasoning",
        capabilities=("response_generation","financial_qa","financial_reasoning","financial_explanation","tool_assisted_qa"),
        enabled=False,
        provider="openai",
        quality_tier=3,
        latency_tier=2,
        cost_tier=2,
        routing_priority=80,
    ),

    "openai-luna": ModelSpec(
        model_id="openai-luna",
        model_name="gpt-6-luna",
        role="openai_reasoning_financial_response",
        capabilities=(
            "response_generation",
            "financial_qa",
            "financial_reasoning",
            "financial_explanation",
            "persona_control",
            "table_reasoning",
            "tool_assisted_qa",
        ),
        enabled=False,
        provider="openai",
        quality_tier=4,
        latency_tier=3,
        cost_tier=3,
        routing_priority=92,
    ),

    "gemini-pro-cloud": ModelSpec(
        model_id="gemini-pro-cloud",
        model_name="gemini-3.1-pro-preview",
        role="gemini_deep_reasoning",
        capabilities=("response_generation","financial_qa","financial_reasoning","financial_explanation","tool_assisted_qa"),
        enabled=False,
        provider="gemini",
        quality_tier=3,
        latency_tier=1,
        cost_tier=2,
        routing_priority=100,
    ),

    "gemini-cloud": ModelSpec(
        model_id="gemini-cloud",
        model_name="gemini-3.8-flash",
        role="cloud_financial_response",
        capabilities=(
            "response_generation",
            "financial_qa",
            "financial_explanation",
            "persona_control",
            "table_reasoning",
            "tool_assisted_qa",
        ),
        enabled=True,
        provider="gemini",
        quality_tier=3,
        latency_tier=1,
        cost_tier=2,
        routing_priority=100,
    ),

    "openrouter-cloud": ModelSpec(
        model_id="openrouter-cloud",
        model_name="openrouter/auto",
        role="cloud_financial_response_fallback",
        capabilities=(
            "response_generation",
            "financial_qa",
            "financial_explanation",
            "persona_control",
            "table_reasoning",
            "tool_assisted_qa",
        ),
        enabled=False,
        provider="openrouter",
        quality_tier=2,
        latency_tier=2,
        cost_tier=2,
        routing_priority=75,
    ),

    "rllm-finqa-4b": ModelSpec(
        model_id="rllm-finqa-4b",
        model_name="rLLM/rLLM-FinQA-4B",
        role="financial_qa",
        capabilities=(
            "response_generation",
            "financial_qa",
            "financial_reasoning",
            "financial_explanation",
            "table_reasoning",
            "tool_assisted_qa",
        ),
        enabled=True,
        provider="local",
        quality_tier=2,
        latency_tier=3,
        cost_tier=1,
        routing_priority=40,
        min_ram_gb=4.0,
        preferred_vram_gb=4.0,
        gpu_required=False,
    ),

    "ollama-qwen3-4b": ModelSpec(
        model_id="ollama-qwen3-4b",
        model_name="qwen3:4b",
        role="local_general_financial_response",
        capabilities=(
            "response_generation",
            "financial_qa",
            "financial_reasoning",
            "financial_explanation",
            "tool_assisted_qa",
        ),
        enabled=False,
        provider="ollama",
        quality_tier=2,
        latency_tier=2,
        cost_tier=1,
        routing_priority=35,
        min_ram_gb=8.0,
        preferred_vram_gb=4.0,
        gpu_required=False,
    ),

    "anthropic-claude": ModelSpec(
        model_id="anthropic-claude",
        model_name="claude-sonnet-5-5",
        role="anthropic_deep_reasoning",
        capabilities=(
            "response_generation",
            "financial_qa",
            "financial_reasoning",
            "financial_explanation",
            "tool_assisted_qa",
        ),
        enabled=False,
        provider="anthropic",
        quality_tier=4,
        latency_tier=2,
        cost_tier=3,
        routing_priority=95,
    ),

    "mistral-large": ModelSpec(
        model_id="mistral-large",
        model_name="mistral-large-latest",
        role="mistral_balanced_reasoning",
        capabilities=(
            "response_generation",
            "financial_qa",
            "financial_reasoning",
            "financial_explanation",
            "tool_assisted_qa",
        ),
        enabled=False,
        provider="mistral",
        quality_tier=2,
        latency_tier=2,
        cost_tier=2,
        routing_priority=70,
    ),

    # Retained for migration/reproducibility, but no longer active.
    "sarvam-1": ModelSpec(
        model_id="sarvam-1",
        model_name="sarvamai/sarvam-1",
        role="legacy_general_financial_response",
        capabilities=(
            "response_generation",
            "financial_explanation",
            "persona_control",
        ),
        enabled=False,
    ),

    "fin-r1": ModelSpec(
        model_id="fin-r1",
        model_name="SUFE-AIFLM-Lab/Fin-R1",
        role="financial_reasoning",
        capabilities=(
            "financial_reasoning",
            "financial_qa",
            "financial_explanation",
        ),
    ),

    "qwen3-embedding-0.6b": ModelSpec(
        model_id="qwen3-embedding-0.6b",
        model_name="Qwen/Qwen3-Embedding-0.6B",
        role="semantic_retrieval",
        capabilities=(
            "semantic_retrieval",
            "multilingual_retrieval",
            "text_embedding",
        ),
        enabled=False,
    ),

    "qwen3-reranker-0.6b": ModelSpec(
        model_id="qwen3-reranker-0.6b",
        model_name="Qwen/Qwen3-Reranker-0.6B",
        role="reranking",
        capabilities=(
            "reranking",
            "evidence_ranking",
            "multilingual_reranking",
        ),
        enabled=False,
    ),

    "qwen-candidate": ModelSpec(
        model_id="qwen-candidate",
        model_name="Qwen-candidate",
        role="general_reasoning",
        capabilities=(
            "general_reasoning",
            "response_generation",
            "financial_explanation",
        ),
        enabled=False,
    ),

    "gemma-candidate": ModelSpec(
        model_id="gemma-candidate",
        model_name="Gemma-candidate",
        role="general_reasoning",
        capabilities=(
            "general_reasoning",
            "response_generation",
            "financial_explanation",
        ),
        enabled=False,
    ),
}


def get_model_spec(model_id: str) -> ModelSpec:
    model_id = str(model_id).strip().lower()

    if model_id not in MODEL_REGISTRY:
        raise KeyError(f"Unknown model: {model_id}")

    return MODEL_REGISTRY[model_id]


def provider_configured(provider: str) -> bool:
    env_by_provider = {
        "openai": "OPENAI_API_KEY",
        "gemini": "GEMINI_API_KEY",
        "anthropic": "ANTHROPIC_API_KEY",
        "mistral": "MISTRAL_API_KEY",
        "openrouter": "OPENROUTER_API_KEY",
        "ollama": "OLLAMA_MODEL",
    }
    key = env_by_provider.get(provider)
    return bool(os.getenv(key, "").strip()) if key else False


def enabled_models():
    import os

    result = []
    for spec in MODEL_REGISTRY.values():
        if spec.enabled or provider_configured(spec.provider):
            result.append(spec)
    return result


def model_configured(spec: ModelSpec) -> bool:
    import os

    if spec.provider == "local":
        return True
    env_by_provider = {
        "openai": "OPENAI_API_KEY",
        "gemini": "GEMINI_API_KEY",
        "anthropic": "ANTHROPIC_API_KEY",
        "mistral": "MISTRAL_API_KEY",
        "openrouter": "OPENROUTER_API_KEY",
        "ollama": "OLLAMA_MODEL",
    }
    key = env_by_provider.get(spec.provider)
    return bool(os.getenv(key, "").strip()) if key else False


def models_for_capability(capability: str):
    return [
        spec
        for spec in MODEL_REGISTRY.values()
        if capability in spec.capabilities
    ]


if __name__ == "__main__":
    print("=" * 80)
    print("FINAI MODEL REGISTRY")
    print("=" * 80)

    for spec in MODEL_REGISTRY.values():
        print()
        print("MODEL ID:", spec.model_id)
        print("MODEL:", spec.model_name)
        print("ROLE:", spec.role)
        print("CAPABILITIES:", spec.capabilities)
        print("ENABLED:", spec.enabled)

