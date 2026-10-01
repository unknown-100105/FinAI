from llm.model_registry import (
    MODEL_REGISTRY,
    get_model_spec,
    enabled_models,
    models_for_capability,
)


def test_registry_contains_expected_candidates():

    assert "sarvam-1" in MODEL_REGISTRY
    assert "fin-r1" in MODEL_REGISTRY
    assert "rllm-finqa-4b" in MODEL_REGISTRY
    assert "qwen-candidate" in MODEL_REGISTRY
    assert "gemma-candidate" in MODEL_REGISTRY


def test_sarvam_is_current_enabled_model():

    models = enabled_models()

    assert len(models) == 1
    assert models[0].model_id == "sarvam-1"


def test_fin_r1_is_financial_reasoning_candidate():

    spec = get_model_spec("fin-r1")

    assert spec.role == "financial_reasoning"
    assert "financial_reasoning" in spec.capabilities


def test_finqa_model_is_qa_candidate():

    spec = get_model_spec("rllm-finqa-4b")

    assert spec.role == "financial_qa"
    assert "financial_qa" in spec.capabilities


def test_capability_lookup():

    models = models_for_capability(
        "financial_reasoning"
    )

    ids = {
        model.model_id
        for model in models
    }

    assert "fin-r1" in ids


def test_unknown_model_fails():

    try:
        get_model_spec("does-not-exist")
    except KeyError:
        return

    raise AssertionError(
        "Unknown model was accepted."
    )
