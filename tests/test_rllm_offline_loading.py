"""Offline/local-only model-loading regression tests."""

from llm import rllm_finqa_adapter as adapter_module


class FakeTorchCuda:
    @staticmethod
    def is_available():
        return True


class FakeModel:
    pass


def test_rllm_adapter_load_never_allows_huggingface_downloads(
    monkeypatch,
    tmp_path,
):
    seen = []
    model_dir = str(tmp_path)

    monkeypatch.setenv("FINAI_NETWORK_MODE", "online")
    monkeypatch.setenv("FINAI_RLLM_MODEL_PATH", model_dir)
    monkeypatch.setattr(
        adapter_module.torch.cuda,
        "is_available",
        lambda: True,
    )
    monkeypatch.setattr(
        adapter_module,
        "BitsAndBytesConfig",
        lambda **kwargs: {"quantization": kwargs},
    )

    def tokenizer_loader(model_reference, **kwargs):
        seen.append(("tokenizer", model_reference, kwargs))
        return object()

    def model_loader(model_reference, **kwargs):
        seen.append(("model", model_reference, kwargs))
        return FakeModel()

    monkeypatch.setattr(
        adapter_module.AutoTokenizer,
        "from_pretrained",
        tokenizer_loader,
    )
    monkeypatch.setattr(
        adapter_module.AutoModelForCausalLM,
        "from_pretrained",
        model_loader,
    )

    adapter = adapter_module.RLLMFinQAModelAdapter()
    adapter.load()

    assert adapter.loaded is True
    assert len(seen) == 2
    assert {item[1] for item in seen} == {model_dir}
    assert all(item[2]["local_files_only"] is True for item in seen)


def test_explicit_local_model_path_must_exist(monkeypatch, tmp_path):
    monkeypatch.setenv(
        "FINAI_RLLM_MODEL_PATH",
        str(tmp_path / "missing-model"),
    )
    monkeypatch.setattr(
        adapter_module.torch.cuda,
        "is_available",
        lambda: True,
    )

    adapter = adapter_module.RLLMFinQAModelAdapter()
    try:
        adapter.load()
    except FileNotFoundError as exc:
        assert "FINAI_RLLM_MODEL_PATH" in str(exc)
    else:
        raise AssertionError("Missing local model path was accepted")
