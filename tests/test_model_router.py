import pytest

from llm.model_router import ModelRouter
from llm.resource_orchestrator import HardwareSnapshot


@pytest.fixture(autouse=True)
def configured_models_for_router_tests(monkeypatch, tmp_path):
    """Model-routing tests use explicit fake config, never real provider credentials."""
    monkeypatch.setenv("GEMINI_API_KEY", "test-gemini-key")
    monkeypatch.setenv("FINAI_LLM_PREFERENCE", "gemini-cloud")
    monkeypatch.setenv("HF_HUB_CACHE", str(tmp_path / "empty-hf-cache"))
    model_path = tmp_path / "rllm-model"
    model_path.mkdir()
    (model_path / "config.json").write_text("{}", encoding="utf-8")
    (model_path / "model.safetensors").write_bytes(b"test-placeholder")
    monkeypatch.setenv("FINAI_RLLM_MODEL_PATH", str(model_path))



def capable_gpu():
    return HardwareSnapshot(
        cpu_cores=8,
        ram_gb=16.0,
        vram_gb=8.0,
        storage_free_gb=100.0,
        cuda_available=True,
        platform="test",
    )


def test_router_prefers_high_priority_default_model():
    router = ModelRouter()
    result = router.route("response_generation", risk_level="low")
    assert result.selected_model == "gemini-cloud"
    assert result.policy == "heuristic"


def test_router_is_risk_aware():
    router = ModelRouter()
    result = router.route("financial_qa", risk_level="critical")
    assert result.reason == "risk_aware_policy_heuristic"
    assert result.fallback_chain[0] == result.selected_model


def test_explicit_model_selection_is_deterministic():
    router = ModelRouter()
    result = router.route(
        "financial_qa",
        risk_level="high",
        explicit_model="rllm-finqa-4b",
        hardware=capable_gpu(),
    )
    assert result.selected_model == "rllm-finqa-4b"
    assert result.policy == "explicit"
    assert result.fallback_chain == ["rllm-finqa-4b"]


def test_preference_can_promote_an_enabled_candidate(monkeypatch):
    monkeypatch.setenv("FINAI_LLM_PREFERENCE", "rllm-finqa-4b")
    router = ModelRouter()
    result = router.route("financial_qa", hardware=capable_gpu())
    assert result.selected_model == "rllm-finqa-4b"


def test_invalid_explicit_model_is_rejected():
    router = ModelRouter()
    try:
        router.route("financial_qa", explicit_model="does-not-exist")
    except KeyError:
        return
    raise AssertionError("Unknown model was accepted.")

def test_critical_risk_can_promote_high_reasoning_cloud(monkeypatch):
    for name in (
        "OPENAI_API_KEY",
        "OPENROUTER_API_KEY",
        "MISTRAL_API_KEY",
        "GEMINI_API_KEY",
    ):
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")

    router = ModelRouter()
    result = router.route("financial_qa", risk_level="critical")

    assert result.selected_model == "anthropic-claude"
    assert result.provider == "anthropic"

def test_offline_routing_is_local_only():
    router = ModelRouter()
    result = router.route(
        "financial_qa",
        network_mode="offline",
        hardware=capable_gpu(),
    )
    assert result.provider == "local"
    assert result.reason == "offline_local_only"
    assert "offline_local_only" in result.constraints_applied


def test_restricted_data_is_local_only():
    router = ModelRouter()
    result = router.route(
        "financial_qa",
        data_sensitivity="restricted",
        hardware=capable_gpu(),
    )
    assert result.provider == "local"
    assert result.reason == "restricted_data_local_only"


def test_degraded_network_prefers_local_model():
    router = ModelRouter(preference=["gemini-cloud"])
    result = router.route(
        "financial_qa",
        network_mode="degraded",
        hardware=capable_gpu(),
    )
    assert result.provider == "local"
    assert result.reason == "degraded_network_local_preference"


def test_offline_explicit_cloud_model_is_rejected():
    router = ModelRouter()
    try:
        router.route(
            "financial_qa",
            network_mode="offline",
            explicit_model="gemini-cloud",
        )
    except ValueError:
        return
    raise AssertionError("Cloud model was accepted in offline mode.")


def test_resource_aware_route_exposes_hardware_plan():
    hardware = HardwareSnapshot(
        cpu_cores=8,
        ram_gb=16.0,
        vram_gb=6.0,
        storage_free_gb=100.0,
        cuda_available=True,
        platform="test",
    )
    result = ModelRouter().route(
        "financial_qa",
        network_mode="offline",
        hardware=hardware,
    )
    assert result.provider == "local"
    assert result.execution_mode == "local_gpu"
    assert result.resource_fit is True
    assert result.hardware["ram_gb"] == 16.0


def test_insufficient_local_resources_are_pruned_from_online_candidates(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    hardware = HardwareSnapshot(
        cpu_cores=4,
        ram_gb=2.0,
        vram_gb=0.0,
        storage_free_gb=50.0,
        cuda_available=False,
        platform="test",
    )
    result = ModelRouter().route(
        "financial_qa",
        network_mode="online",
        hardware=hardware,
    )
    assert result.provider == "gemini"
    assert "local_resource_constraint" in result.constraints_applied


def test_offline_fails_when_no_local_model_fits():
    hardware = HardwareSnapshot(
        cpu_cores=2,
        ram_gb=2.0,
        vram_gb=0.0,
        storage_free_gb=20.0,
        cuda_available=False,
        platform="test",
    )
    try:
        ModelRouter().route(
            "financial_qa",
            network_mode="offline",
            hardware=hardware,
        )
    except RuntimeError as exc:
        assert "No enabled model" in str(exc)
        return
    raise AssertionError("Offline routing unexpectedly selected an unfit model.")
