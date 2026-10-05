from llm.model_registry import (
    MODEL_REGISTRY,
    get_model_spec,
    enabled_models,
    models_for_capability,
)


def test_registry_contains_expected_candidates():
    assert "gemini-cloud" in MODEL_REGISTRY
    assert "sarvam-1" in MODEL_REGISTRY
    assert "fin-r1" in MODEL_REGISTRY
    assert "rllm-finqa-4b" in MODEL_REGISTRY
    assert "qwen-candidate" in MODEL_REGISTRY
    assert "gemma-candidate" in MODEL_REGISTRY
    assert "anthropic-claude" in MODEL_REGISTRY
    assert "mistral-large" in MODEL_REGISTRY


def test_gemini_is_current_enabled_model():
    models = enabled_models()
    ids = {model.model_id for model in models}

    assert "gemini-cloud" in ids
    assert get_model_spec("gemini-cloud").enabled is True


def test_sarvam_is_disabled_legacy_model():
    spec = get_model_spec("sarvam-1")

    assert spec.enabled is False


def test_fin_r1_is_financial_reasoning_candidate():
    spec = get_model_spec("fin-r1")

    assert spec.role == "financial_reasoning"
    assert "financial_reasoning" in spec.capabilities


def test_finqa_model_is_qa_candidate():
    spec = get_model_spec("rllm-finqa-4b")

    assert spec.role == "financial_qa"
    assert "financial_qa" in spec.capabilities


def test_capability_lookup():
    models = models_for_capability("financial_reasoning")
    ids = {model.model_id for model in models}

    assert "fin-r1" in ids


def test_unknown_model_fails():
    try:
        get_model_spec("does-not-exist")
    except KeyError:
        return

    raise AssertionError("Unknown model was accepted.")

def test_cloud_provider_metadata_is_explicit():
    assert get_model_spec("anthropic-claude").provider == "anthropic"
    assert get_model_spec("mistral-large").provider == "mistral"
    assert get_model_spec("openrouter-cloud").provider == "openrouter"
