"""Request-path integration tests for the capability execution-plan diagnostics."""

import pytest

from orchestrator import hybrid_engine
from orchestrator.hybrid_engine import FinAIHybridEngine
from xai.trace import XAITrace


def _engine_with_stubbed_core():
    engine = FinAIHybridEngine.__new__(FinAIHybridEngine)
    engine.finance = object()
    engine.rag_retriever = None
    engine.response_service = None

    def core(**kwargs):
        return {
            "stage": "finance_engine",
            "status": "CALCULATED",
            "router": {"intent": "EMI_QUERY"},
            "execution_plan": {"capability": "finance_engine"},
            "policy": {"status": "ALLOWED"},
            "response_generation": None,
        }

    engine._process_core = core
    return engine


def test_hybrid_request_result_contains_serializable_capability_plan(monkeypatch):
    for key in (
        "OPENAI_API_KEY",
        "OPENROUTER_API_KEY",
        "ANTHROPIC_API_KEY",
        "MISTRAL_API_KEY",
        "GOOGLE_API_KEY",
        "GEMINI_API_KEY",
        "SARVAM_API_KEY",
    ):
        monkeypatch.delenv(key, raising=False)

    result = _engine_with_stubbed_core().process(
        user_text="Calculate EMI",
        generate_response=False,
    )

    plan = result["capability_execution_plan"]
    assert plan["planner_role"] == "request_path_diagnostic"
    assert plan["enforcement"].startswith("Existing routing")
    assert plan["observed_stage"] == "finance_engine"
    assert plan["observed_status"] == "CALCULATED"
    assert plan["blocked"] is False
    assert [step["capability"] for step in plan["steps"]] == [
        "policy",
        "deterministic_finance",
    ]
    assert plan["request_id"]
    assert plan["request_outcome"] == "CALCULATED"
    assert plan["request_outcome_stage"] == "finance_engine"
    assert [step["observed_status"] for step in plan["steps"]] == [
        "ALLOWED", "CALCULATED",
    ]


def test_requested_generation_without_observed_provider_blocks_diagnostic_plan(monkeypatch):
    for key in (
        "OPENAI_API_KEY",
        "OPENROUTER_API_KEY",
        "ANTHROPIC_API_KEY",
        "MISTRAL_API_KEY",
        "GOOGLE_API_KEY",
        "GEMINI_API_KEY",
        "SARVAM_API_KEY",
    ):
        monkeypatch.delenv(key, raising=False)

    result = _engine_with_stubbed_core().process(
        user_text="Calculate EMI",
        generate_response=True,
    )

    plan = result["capability_execution_plan"]
    assert plan["blocked"] is True
    assert any(
        "response generation" in explanation.lower()
        for explanation in plan["explanations"]
    )


def test_xai_trace_records_capability_plan_without_overwriting_authority():
    trace = XAITrace("capability-plan-trace-test")
    trace.record_execution_plan({
        "capability": "finance_engine",
        "decision": "EXECUTE",
        "execution_class": "COMPUTE",
        "authority_class": "DETERMINISTIC_RESULT",
        "authority_source": "finance_engine",
    })
    diagnostic = {
        "schema_version": "1.0",
        "planner_role": "request_path_diagnostic",
        "blocked": False,
        "steps": [{"step_id": "01_policy", "kind": "policy_check"}],
    }

    trace.record_capability_execution_plan(diagnostic)

    assert trace.data["capability_execution_plan"] == diagnostic
    assert trace.data["execution"]["capability"] == "finance_engine"
    assert trace.data["authority"]["authority_source"] == "finance_engine"


def test_missing_rag_assets_fail_before_embedding_model_load(monkeypatch, tmp_path):
    monkeypatch.setattr(hybrid_engine, "ROOT", tmp_path)
    engine = FinAIHybridEngine.__new__(FinAIHybridEngine)
    engine.rag_retriever = None

    with pytest.raises(FileNotFoundError, match="RAG assets are incomplete"):
        engine._get_rag_retriever()


def test_capability_plan_records_generation_and_verification_outcomes(monkeypatch):
    for key in (
        "OPENAI_API_KEY",
        "OPENROUTER_API_KEY",
        "ANTHROPIC_API_KEY",
        "MISTRAL_API_KEY",
        "GOOGLE_API_KEY",
        "GEMINI_API_KEY",
        "SARVAM_API_KEY",
    ):
        monkeypatch.delenv(key, raising=False)

    engine = _engine_with_stubbed_core()

    def core(**kwargs):
        return {
            "stage": "financial_knowledge",
            "status": "KNOWLEDGE_RETRIEVED",
            "router": {"intent": "FINANCIAL_PRODUCT_KNOWLEDGE"},
            "execution_plan": {"capability": "financial_knowledge"},
            "policy": {"status": "ALLOWED"},
            "response_generation": {
                "status": "GENERATED_VERIFIED",
                "verification": {"applicable": True, "passed": True},
                "claim_verification": {"applicable": True, "passed": True},
            },
        }

    engine._process_core = core
    result = engine.process(
        user_text="Explain mutual funds",
        generate_response=True,
    )

    plan = result["capability_execution_plan"]
    observed = {
        step["capability"]: step["observed_status"]
        for step in plan["steps"]
    }
    assert plan["request_outcome"] == "KNOWLEDGE_RETRIEVED"
    assert observed["model_generation"] == "GENERATED_VERIFIED"
    assert observed["claim_verification"] == "PASSED"
    assert observed["response_verification"] == "PASSED"


def test_capability_plan_respects_offline_mode_without_claiming_cloud_generation(monkeypatch):
    monkeypatch.setenv("FINAI_NETWORK_MODE", "offline")
    for key in (
        "OPENAI_API_KEY",
        "OPENROUTER_API_KEY",
        "ANTHROPIC_API_KEY",
        "MISTRAL_API_KEY",
        "GOOGLE_API_KEY",
        "GEMINI_API_KEY",
        "SARVAM_API_KEY",
    ):
        monkeypatch.delenv(key, raising=False)

    result = _engine_with_stubbed_core().process(
        user_text="Calculate EMI",
        generate_response=True,
    )
    plan = result["capability_execution_plan"]

    assert plan["mode"] == "offline"
    assert plan["blocked"] is True
    assert any(
        "model_generation" in explanation.lower()
        or "model generation" in explanation.lower()
        for explanation in plan["explanations"]
    )


def test_capability_plan_exposes_structured_knowledge_stage(monkeypatch):
    monkeypatch.setenv("FINAI_NETWORK_MODE", "online")
    for key in (
        "OPENAI_API_KEY", "OPENROUTER_API_KEY", "ANTHROPIC_API_KEY",
        "MISTRAL_API_KEY", "GOOGLE_API_KEY", "GEMINI_API_KEY", "SARVAM_API_KEY",
    ):
        monkeypatch.delenv(key, raising=False)

    engine = _engine_with_stubbed_core()

    def core(**kwargs):
        return {
            "stage": "financial_knowledge",
            "status": "KNOWLEDGE_RETRIEVED",
            "router": {"intent": "FINANCIAL_PRODUCT_KNOWLEDGE"},
            "execution_plan": {"capability": "rag"},
            "policy": {"status": "ALLOWED"},
            "knowledge": {"source": "structured_financial_catalog"},
        }

    engine._process_core = core
    result = engine.process(user_text="Explain mutual funds", generate_response=False)
    plan = result["capability_execution_plan"]
    steps = {step["capability"]: step for step in plan["steps"]}

    assert "structured_knowledge" in steps
    assert steps["structured_knowledge"]["kind"] == "structured_knowledge"
    assert steps["structured_knowledge"]["observed_status"] == "KNOWLEDGE_RETRIEVED"
    assert steps["structured_knowledge"]["depends_on"] == ["01_policy"]


def test_capability_plan_exposes_market_data_stage(monkeypatch):
    monkeypatch.setenv("FINAI_NETWORK_MODE", "online")
    for key in (
        "OPENAI_API_KEY", "OPENROUTER_API_KEY", "ANTHROPIC_API_KEY",
        "MISTRAL_API_KEY", "GOOGLE_API_KEY", "GEMINI_API_KEY", "SARVAM_API_KEY",
    ):
        monkeypatch.delenv(key, raising=False)

    engine = _engine_with_stubbed_core()

    def core(**kwargs):
        return {
            "stage": "market_data",
            "status": "MARKET_DATA_READY",
            "router": {"intent": "MARKET_DATA_QUERY"},
            "execution_plan": {"capability": "market_data"},
            "policy": {"status": "ALLOWED"},
            "market_data": {"instrument": "NIFTY 50"},
        }

    engine._process_core = core
    result = engine.process(user_text="Show NIFTY 50", generate_response=False)
    plan = result["capability_execution_plan"]
    steps = {step["capability"]: step for step in plan["steps"]}

    assert "market_data" in steps
    assert steps["market_data"]["kind"] == "market_data"
    assert steps["market_data"]["observed_status"] == "MARKET_DATA_READY"
    assert steps["market_data"]["depends_on"] == ["01_policy"]
