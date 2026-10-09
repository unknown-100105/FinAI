from llm.model_registry import MODEL_REGISTRY, enabled_models, model_configured
from llm.model_router import ModelRouter
from llm.resource_orchestrator import HardwareSnapshot


def test_ollama_model_is_registered_but_opt_in(monkeypatch):
    monkeypatch.delenv("OLLAMA_MODEL", raising=False)
    spec = MODEL_REGISTRY["ollama-qwen3-4b"]
    assert spec.enabled is False
    assert not model_configured(spec)
    assert "ollama-qwen3-4b" not in {item.model_id for item in enabled_models()}


def test_ollama_can_be_selected_for_offline_execution_when_configured(monkeypatch):
    monkeypatch.setenv("OLLAMA_MODEL", "qwen3:4b")
    hardware = HardwareSnapshot(
        cpu_cores=8,
        ram_gb=16.0,
        vram_gb=8.0,
        storage_free_gb=100.0,
        cuda_available=True,
        platform="test",
    )
    result = ModelRouter().route(
        "financial_qa",
        network_mode="offline",
        explicit_model="ollama-qwen3-4b",
        hardware=hardware,
    )
    assert result.selected_model == "ollama-qwen3-4b"
    assert result.provider == "ollama"
    assert result.execution_mode == "local_gpu"
    assert result.fallback_chain == ["ollama-qwen3-4b"]
