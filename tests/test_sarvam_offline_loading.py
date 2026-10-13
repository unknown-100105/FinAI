"""Sarvam's local base model must be pre-provisioned; requests do not download weights."""

from types import SimpleNamespace
from unittest.mock import Mock, patch

import pytest

from llm.response_adapter import SarvamResponseAdapter


def test_sarvam_loader_uses_local_files_only(monkeypatch, tmp_path):
    base_path = tmp_path / "sarvam-base"
    adapter_path = tmp_path / "finai-adapter"
    base_path.mkdir()
    adapter_path.mkdir()

    monkeypatch.setenv("FINAI_SARVAM_BASE_MODEL_PATH", str(base_path))
    monkeypatch.setattr("llm.response_adapter.torch.cuda.is_available", lambda: True)

    tokenizer = SimpleNamespace(pad_token_id=1, eos_token="eos")
    model = Mock()
    with (
        patch("transformers.AutoTokenizer.from_pretrained", return_value=tokenizer) as tokenizer_load,
        patch("transformers.AutoModelForCausalLM.from_pretrained", return_value=model) as model_load,
        patch("transformers.BitsAndBytesConfig", return_value=object()),
        patch("peft.PeftModel.from_pretrained", return_value=model) as peft_load,
    ):
        adapter = SarvamResponseAdapter(lazy_load=True, adapter_path=str(adapter_path))
        adapter.load()

    assert adapter.loaded is True
    assert tokenizer_load.call_args.args[0] == str(base_path)
    assert tokenizer_load.call_args.kwargs["local_files_only"] is True
    assert model_load.call_args.args[0] == str(base_path)
    assert model_load.call_args.kwargs["local_files_only"] is True
    peft_load.assert_called_once()


def test_sarvam_loader_rejects_missing_explicit_base_path(monkeypatch, tmp_path):
    missing_path = tmp_path / "does-not-exist"
    monkeypatch.setenv("FINAI_SARVAM_BASE_MODEL_PATH", str(missing_path))
    monkeypatch.setattr("llm.response_adapter.torch.cuda.is_available", lambda: True)

    adapter = SarvamResponseAdapter(lazy_load=True)
    with pytest.raises(FileNotFoundError, match="FINAI_SARVAM_BASE_MODEL_PATH"):
        adapter.load()
