from llm.model_router import ModelRouter


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
    )
    assert result.selected_model == "rllm-finqa-4b"
    assert result.policy == "explicit"
    assert result.fallback_chain == ["rllm-finqa-4b"]


def test_preference_can_promote_an_enabled_candidate(monkeypatch):
    monkeypatch.setenv("FINAI_LLM_PREFERENCE", "rllm-finqa-4b")
    router = ModelRouter()
    result = router.route("financial_qa")
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
    ):
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")

    router = ModelRouter()
    result = router.route("financial_qa", risk_level="critical")

    assert result.selected_model == "anthropic-claude"
    assert result.provider == "anthropic"

def test_offline_routing_is_local_only():
    router = ModelRouter()
    result = router.route("financial_qa", network_mode="offline")
    assert result.provider == "local"
    assert result.reason == "offline_local_only"
    assert "offline_local_only" in result.constraints_applied


def test_restricted_data_is_local_only():
    router = ModelRouter()
    result = router.route("financial_qa", data_sensitivity="restricted")
    assert result.provider == "local"
    assert result.reason == "restricted_data_local_only"


def test_degraded_network_prefers_local_model():
    router = ModelRouter(preference=["gemini-cloud"])
    result = router.route("financial_qa", network_mode="degraded")
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
