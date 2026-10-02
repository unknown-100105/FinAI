from orchestrator.session_xai import XAISessionOrchestrator
from orchestrator.session import SessionStore


class FakeEngine:

    def __init__(self):
        self.calls = []

    def process(
        self,
        user_text,
        authenticated=False,
        confirmed=False,
    ):
        self.calls.append({
            "user_text": user_text,
            "authenticated": authenticated,
            "confirmed": confirmed,
        })

        return {
            "status": "CALCULATED",
            "stage": "finance_engine",
            "message": "Calculation completed.",
            "router": {
                "intent": "EMI_QUERY",
                "confidence": 0.99,
                "margin": 0.90,
                "decision": "ROUTE",
            },
            "policy": {
                "status": "ALLOWED",
                "risk_level": "low",
                "authentication_required": False,
                "confirmation_required": False,
                "tool": None,
            },
            "finance": {
                "operation": "EMI_CALCULATION",
                "status": "CALCULATED",
                "parameters": {},
                "missing": [],
                "result": {
                    "principal": 1_000_000.0,
                    "annual_rate": 8.5,
                    "tenure_months": 240,
                    "monthly_emi": 8678.23,
                    "total_payment": 2082775.76,
                    "total_interest": 1082775.76,
                },
                "source": "deterministic_finance_engine",
            },
            "tool": None,
            "execution_plan": {
                "intent": "EMI_QUERY",
                "decision": "EXECUTE",
                "capability": "finance_engine",
                "execution_class": "COMPUTE",
                "authority_class": "DETERMINISTIC_COMPUTATION",
                "authority_source": "deterministic_finance_engine",
            },
            "response": "Verified EMI response.",
            "response_generation": {
                "status": "GENERATED_VERIFIED",
                "model_id": "rllm-finqa-4b",
                "source": "deterministic_finance_engine",
                "language": "English",
                "persona": "neutral",
                "selection": {
                    "capability": "financial_qa",
                    "model_id": "rllm-finqa-4b",
                },
                "verification": {
                    "applicable": True,
                    "passed": True,
                    "missing_values": [],
                    "semantic_errors": [],
                },
                "claim_verification": {
                    "applicable": True,
                    "passed": True,
                    "report": {
                        "passed": True,
                        "matched": [
                            {
                                "field": "monthly_emi",
                                "value": 8678.23,
                            },
                            {
                                "field": "total_payment",
                                "value": 2082775.76,
                            },
                            {
                                "field": "total_interest",
                                "value": 1082775.76,
                            },
                        ],
                        "mismatched": [],
                        "unsupported": [],
                        "rejected_claims": [],
                        "authority_violations": [],
                        "missing_required_fields": [],
                    },
                    "claims": [
                        {
                            "field": "monthly_emi",
                            "value": 8678.23,
                            "claim_type": "MODEL_INFERRED",
                            "authority_source": "llm",
                            "verification_status": "PENDING",
                        },
                        {
                            "field": "total_payment",
                            "value": 2082775.76,
                            "claim_type": "MODEL_INFERRED",
                            "authority_source": "llm",
                            "verification_status": "PENDING",
                        },
                        {
                            "field": "total_interest",
                            "value": 1082775.76,
                            "claim_type": "MODEL_INFERRED",
                            "authority_source": "llm",
                            "verification_status": "PENDING",
                        },
                    ],
                },
            },
        }


def test_session_orchestrator_accepts_injected_engine():

    fake = FakeEngine()
    app = XAISessionOrchestrator()
    app.engine = fake

    result = app.handle_message(
        session_id="session-xai-test",
        user_text="Calculate EMI",
    )

    assert fake.calls
    assert result["trace_id"]
    assert result["trace_path"]


def test_session_orchestrator_preserves_authentication_flow():

    fake = FakeEngine()
    app = XAISessionOrchestrator()
    app.engine = fake

    first = app.handle_message(
        session_id="auth-xai-test",
        user_text="Calculate EMI",
    )

    assert first["trace_id"]
    assert first["session"]["authenticated"] is False


def test_session_trace_can_record_model_response():

    fake = FakeEngine()
    app = XAISessionOrchestrator()
    app.engine = fake

    result = app.handle_message(
        session_id="model-xai-test",
        user_text="Calculate EMI",
    )

    trace_id = result["trace_id"]

    trace = app.engine
    assert trace is fake
    assert trace.calls


def test_session_trace_records_authority_and_execution():

    fake = FakeEngine()
    app = XAISessionOrchestrator()
    app.engine = fake

    result = app.handle_message(
        session_id="execution-xai-test",
        user_text="Calculate EMI",
    )

    trace_path = result["trace_path"]

    from pathlib import Path
    import json

    trace = json.loads(
        Path(trace_path).read_text(encoding="utf-8")
    )

    assert trace["authority"]["authority_class"] == (
        "DETERMINISTIC_COMPUTATION"
    )
    assert trace["authority"]["authority_source"] == (
        "deterministic_finance_engine"
    )
    assert trace["execution"]["execution_class"] == "COMPUTE"
    assert trace["execution"]["capability"] == "finance_engine"
