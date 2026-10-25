import pytest

from app.models_api import models, route_preview, resources
from llm.resource_orchestrator import HardwareSnapshot


@pytest.fixture(autouse=True)
def configured_model_api_environment(monkeypatch, tmp_path):
    monkeypatch.setenv("GEMINI_API_KEY", "test-gemini-key")
    monkeypatch.setenv("FINAI_LLM_PREFERENCE", "gemini-cloud")
    monkeypatch.setenv("HF_HUB_CACHE", str(tmp_path / "empty-hf-cache"))
    model_path = tmp_path / "rllm-model"
    model_path.mkdir()
    (model_path / "config.json").write_text("{}", encoding="utf-8")
    (model_path / "model.safetensors").write_bytes(b"test-placeholder")
    monkeypatch.setenv("FINAI_RLLM_MODEL_PATH", str(model_path))
    hardware = HardwareSnapshot(
        cpu_cores=8,
        ram_gb=16.0,
        vram_gb=8.0,
        storage_free_gb=100.0,
        cuda_available=True,
        platform="test",
    )
    monkeypatch.setattr("llm.model_router.detect_hardware", lambda: hardware)



def test_model_catalog_includes_provider_metadata():
    payload = models()
    rows = payload["models"]
    gemini = next(row for row in rows if row["model_id"] == "gemini-cloud")

    assert gemini["provider"] == "gemini"
    assert "configured" in gemini
    assert "quality_tier" in gemini
    assert "cost_tier" in gemini


def test_route_preview_returns_auditable_policy():
    result = route_preview(
        {
            "capability": "financial_qa",
            "risk_level": "high",
            "language": "English",
        }
    )

    assert result["capability"] == "financial_qa"
    assert result["risk_level"] == "high"
    assert result["policy"] == "heuristic"
    assert result["fallback_chain"]

def test_route_preview_enforces_offline_constraints():
    result = route_preview(
        {
            "capability": "financial_qa",
            "risk_level": "medium",
            "language": "English",
            "network_mode": "offline",
        }
    )
    assert result["provider"] == "local"
    assert result["reason"] == "offline_local_only"
    assert result["network_mode"] == "offline"


def test_resource_api_exposes_hardware_and_local_model_fit():
    result = resources()
    assert "hardware" in result
    assert "cpu_cores" in result["hardware"]
    assert "ram_gb" in result["hardware"]
    assert "vram_gb" in result["hardware"]
    assert "local_models" in result
    assert result["local_models"]
    assert "resource" in result["local_models"][0]
