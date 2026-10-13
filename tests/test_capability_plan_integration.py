"""Request-path integration tests for the capability execution-plan diagnostics."""

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
