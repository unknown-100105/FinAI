from llm.model_registry import (
    MODEL_REGISTRY,
    get_model_spec,
    enabled_models,
    models_for_capability,
    model_configured,
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


def test_gemini_is_current_enabled_model(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "test-gemini-key")
    models = enabled_models()
    ids = {model.model_id for model in models}

    assert "gemini-cloud" in ids
    assert get_model_spec("gemini-cloud").enabled is True


def test_unconfigured_models_are_not_routable(monkeypatch, tmp_path):
    for name in (
        "OPENAI_API_KEY",
        "GEMINI_API_KEY",
        "ANTHROPIC_API_KEY",
        "MISTRAL_API_KEY",
        "OPENROUTER_API_KEY",
    ):
        monkeypatch.delenv(name, raising=False)
    monkeypatch.delenv("FINAI_RLLM_MODEL_PATH", raising=False)
    monkeypatch.delenv("FINAI_EMBEDDING_MODEL_PATH", raising=False)
    monkeypatch.setenv("HF_HUB_CACHE", str(tmp_path / "empty-hf-cache"))

    candidates = {model.model_id for model in enabled_models()}

    assert "gemini-cloud" not in candidates
    assert "rllm-finqa-4b" not in candidates
    assert model_configured(MODEL_REGISTRY["gemini-cloud"]) is False
    assert model_configured(MODEL_REGISTRY["rllm-finqa-4b"]) is False


def test_local_model_requires_config_and_weight_files(monkeypatch, tmp_path):
    model_path = tmp_path / "model"
    model_path.mkdir()
    (model_path / "config.json").write_text("{}", encoding="utf-8")
    monkeypatch.setenv("FINAI_RLLM_MODEL_PATH", str(model_path))
    monkeypatch.setenv("HF_HUB_CACHE", str(tmp_path / "empty-hf-cache"))

    spec = MODEL_REGISTRY["rllm-finqa-4b"]
    assert model_configured(spec) is False

    (model_path / "model.safetensors").write_bytes(b"test-placeholder")
    assert model_configured(spec) is True


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
