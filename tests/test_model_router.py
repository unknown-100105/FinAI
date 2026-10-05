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
