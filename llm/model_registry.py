from dataclasses import dataclass
import os
from pathlib import Path
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

    "colibri-local": ModelSpec(
        model_id="colibri-local",
        model_name="Colibrì local inference server",
        role="local_streaming_inference",
        capabilities=(
            "response_generation",
            "financial_qa",
            "financial_explanation",
            "persona_control",
            "tool_assisted_qa",
        ),
        enabled=False,
        provider="local",
        quality_tier=2,
        latency_tier=3,
        cost_tier=1,
        routing_priority=55,
        # The model is hosted in a separate local Colibrì process. The server
        # owns its VRAM/RAM/NVMe placement and must be checked independently.
        min_ram_gb=0.0,
        preferred_vram_gb=0.0,
        gpu_required=False,
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
        # The current adapter uses 4-bit CUDA quantization. Do not advertise
        # this model as runnable on CPU-only hosts.
        gpu_required=True,
    ),

    "anthropic-claude": ModelSpec(
        model_id="anthropic-claude",
        model_name="claude-sonnet-5",
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
    }
    key = env_by_provider.get(provider)
    return bool(os.getenv(key, "").strip()) if key else False


def _resolve_configured_model_path(env_name: str) -> Path | None:
    configured = os.getenv(env_name, "").strip()
    if not configured:
        return None
    path = Path(configured).expanduser()
    if not path.is_absolute():
        path = Path(__file__).resolve().parents[1] / path
    return path.resolve()


def _directory_has_model_weights(path: Path) -> bool:
    """Require model configuration and weight files, not merely an existing folder."""
    if not path.is_dir():
        return False
    if not any(path.rglob("config.json")):
        return False
    return any(path.rglob("*.safetensors")) or any(
        path.rglob("pytorch_model*.bin")
    )


def _cached_model_exists(model_reference: str) -> bool:
    """Check the local Hugging Face cache without triggering downloads."""
    configured_cache = (
        os.getenv("HF_HUB_CACHE", "").strip()
        or os.getenv("HUGGINGFACE_HUB_CACHE", "").strip()
    )
    if configured_cache:
        cache_root = Path(configured_cache).expanduser()
    else:
        hf_home = os.getenv("HF_HOME", "").strip()
        cache_root = (
            Path(hf_home).expanduser() / "hub"
            if hf_home
            else Path.home() / ".cache" / "huggingface" / "hub"
        )

    cache_name = "models--" + model_reference.replace("/", "--")
    snapshots = cache_root / cache_name / "snapshots"
    if not snapshots.is_dir():
        return False
    return any(
        _directory_has_model_weights(snapshot)
        for snapshot in snapshots.iterdir()
        if snapshot.is_dir()
    )


def model_configured(spec: ModelSpec) -> bool:
    """Report local configuration readiness; this does not claim live inference works."""
    if spec.model_id == "colibri-local":
        return bool(os.getenv("FINAI_COLIBRI_BASE_URL", "").strip())

    if spec.provider in {"openai", "gemini", "anthropic", "mistral", "openrouter"}:
        return provider_configured(spec.provider)

    # Only local models with an implemented adapter and a verifiable model source
    # are reported as configured. Registry entries for research candidates do
    # not become runnable just because their provider label defaults to "local".
    local_model_sources = {
        "rllm-finqa-4b": (
            "FINAI_RLLM_MODEL_PATH",
            "rLLM/rLLM-FinQA-4B",
        ),
        "qwen3-embedding-0.6b": (
            "FINAI_EMBEDDING_MODEL_PATH",
            "Qwen/Qwen3-Embedding-0.6B",
        ),
    }
    source = local_model_sources.get(spec.model_id)
    if source is None:
        return False

    env_name, model_reference = source
    configured_path = _resolve_configured_model_path(env_name)
    if configured_path is not None:
        return _directory_has_model_weights(configured_path)

    return _cached_model_exists(model_reference)


def enabled_models():
    """Return registry candidates enabled by policy/provider configuration.

    This is deliberately separate from model_configured(): adapters may be
    registered for tests and diagnostics even while credentials or weights are
    absent. Execution routing must check model_configured() before selection.
    """
    result = []
    for spec in MODEL_REGISTRY.values():
        if spec.model_id == "colibri-local":
            # The optional local server is opt-in and is not probed at startup.
            if os.getenv("FINAI_COLIBRI_BASE_URL", "").strip():
                result.append(spec)
            continue
        if spec.enabled or provider_configured(spec.provider):
            result.append(spec)
    return result


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

