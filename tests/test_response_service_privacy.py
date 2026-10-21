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
