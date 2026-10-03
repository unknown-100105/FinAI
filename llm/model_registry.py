from dataclasses import dataclass
from typing import Tuple


@dataclass(frozen=True)
class ModelSpec:
    model_id: str
    model_name: str
    role: str
    capabilities: Tuple[str, ...]
    enabled: bool = False


MODEL_REGISTRY = {
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


def enabled_models():
    import os

    return [
        spec
        for spec in MODEL_REGISTRY.values()
        if spec.enabled
        or (
            spec.model_id == "openai-luna"
            and bool(os.getenv("OPENAI_API_KEY"))
        )
        or (
            spec.model_id == "openrouter-cloud"
            and bool(os.getenv("OPENROUTER_API_KEY"))
        )
    ]


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

