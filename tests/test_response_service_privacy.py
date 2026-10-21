from types import SimpleNamespace

from llm.response_service import ResponseService


class FakeGateway:
    def generate(self, **kwargs):
        return {
            "status": "GENERATED",
            "model_id": kwargs["model_id"],
            "response": "A general explanation.",
            "generation_complete": True,
            "truncated": False,
            "finish_reason": "stop",
            "metrics": {},
        }


def test_response_service_defaults_to_restricted_data_sensitivity(monkeypatch):
    monkeypatch.delenv("FINAI_DATA_SENSITIVITY", raising=False)
    service = ResponseService(gateway=FakeGateway())
    observed = {}

    def fake_route(**kwargs):
        observed.update(kwargs)
        return SimpleNamespace(
            selected_model="test-local-model",
            network_mode=kwargs["network_mode"],
            data_sensitivity=kwargs["data_sensitivity"],
            allowed_providers=kwargs["allowed_providers"],
            reason="test",
            policy="restricted",
            risk_level="low",
            fallback_chain=[],
        )

    monkeypatch.setattr(service.model_router, "route", fake_route)
    result = service.generate(
        user_text="Explain budgeting.",
        intent="SUPPORT_REQUEST",
        verified_result={},
        source="support_system",
    )

    assert observed["data_sensitivity"] == "restricted"
    assert result["status"] == "GENERATED"


def test_provider_context_minimization_removes_sensitive_fields():
    cleaned = ResponseService._minimize_provider_context(
        "SUPPORT_REQUEST",
        {
            "account_id": "ACC-123",
            "balance": 5000,
            "summary": "general help",
            "nested": {"phone": "555-0100", "topic": "budgeting"},
        },
    )
    assert "account_id" not in cleaned
    assert "balance" not in cleaned
    assert cleaned["summary"] == "general help"
    assert cleaned["nested"] == {"topic": "budgeting"}


def test_finance_provider_context_uses_allowlist():
    cleaned = ResponseService._minimize_provider_context(
        "EMI_QUERY",
        {
            "principal": 100000,
            "annual_rate": 8,
            "tenure_months": 120,
            "monthly_emi": 1213.28,
            "total_payment": 145593.6,
            "total_interest": 45593.6,
            "account_id": "ACC-123",
            "customer_name": "Sensitive Name",
        },
    )
    assert "account_id" not in cleaned
    assert "customer_name" not in cleaned
    assert set(cleaned) == {
        "principal", "annual_rate", "tenure_months",
        "monthly_emi", "total_payment", "total_interest",
    }
