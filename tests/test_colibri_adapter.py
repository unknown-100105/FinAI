"""Optional Colibrì integration must stay loopback-only and route as local inference."""

from unittest.mock import Mock

import pytest

from llm.colibri_adapter import ColibriResponseAdapter
from llm.model_registry import enabled_models
from llm.model_router import ModelRouter
from llm.resource_orchestrator import HardwareSnapshot


def test_colibri_url_is_restricted_to_loopback():
    assert ColibriResponseAdapter._chat_completions_url(
        "http://127.0.0.1:8000"
    ) == "http://127.0.0.1:8000/v1/chat/completions"
    assert ColibriResponseAdapter._chat_completions_url(
        "http://localhost:8000/v1/"
    ) == "http://localhost:8000/v1/chat/completions"

    with pytest.raises(ValueError, match="localhost"):
        ColibriResponseAdapter._chat_completions_url(
            "http://model-server.example:8000/v1"
        )
    with pytest.raises(ValueError, match="path must be empty or /v1"):
        ColibriResponseAdapter._chat_completions_url(
            "http://127.0.0.1:8000/custom/path"
        )


def test_colibri_generate_uses_openai_compatible_payload(monkeypatch):
    monkeypatch.setenv("FINAI_COLIBRI_BASE_URL", "http://127.0.0.1:8000/v1")
    monkeypatch.setenv("FINAI_COLIBRI_MODEL", "olmoe-colibri")
    monkeypatch.setenv("FINAI_COLIBRI_API_KEY", "local-secret")

    response = Mock(
        status_code=200,
        json=Mock(return_value={
            "choices": [{"message": {"content": "Your EMI is ₹8,500."}}],
            "usage": {"prompt_tokens": 20, "completion_tokens": 8},
        }),
    )
    post = Mock(return_value=response)
    monkeypatch.setattr("llm.colibri_adapter.requests.post", post)

    adapter = ColibriResponseAdapter()
    result = adapter.generate(
        user_text="Explain the EMI.",
        intent="EMI_QUERY",
        verified_result={"monthly_emi": 8500},
        source="deterministic_finance_engine",
        language="English",
        persona="neutral",
        max_new_tokens=90,
    )

    assert result["status"] == "GENERATED"
    assert result["response"] == "Your EMI is ₹8,500."
    assert result["provider"] == "local_colibri"
    assert result["usage"]["completion_tokens"] == 8
    post.assert_called_once()
    args, kwargs = post.call_args
    assert args[0] == "http://127.0.0.1:8000/v1/chat/completions"
    assert kwargs["headers"]["Authorization"] == "Bearer local-secret"
    assert kwargs["allow_redirects"] is False
    assert kwargs["json"]["model"] == "olmoe-colibri"
    assert kwargs["json"]["max_tokens"] == 90
    assert kwargs["json"]["stream"] is False
    assert "monthly_emi" in kwargs["json"]["messages"][1]["content"]


def test_colibri_model_is_opt_in_and_selected_for_offline_routing(monkeypatch):
    monkeypatch.delenv("FINAI_COLIBRI_BASE_URL", raising=False)
    assert "colibri-local" not in {
        spec.model_id for spec in enabled_models()
    }

    monkeypatch.setenv("FINAI_COLIBRI_BASE_URL", "http://127.0.0.1:8000/v1")
    assert "colibri-local" in {
        spec.model_id for spec in enabled_models()
    }

    hardware = HardwareSnapshot(
        cpu_cores=8,
        ram_gb=16.0,
        vram_gb=0.0,
        storage_free_gb=100.0,
        cuda_available=False,
        platform="test",
    )
    route = ModelRouter().route(
        "financial_qa",
        network_mode="offline",
        data_sensitivity="restricted",
        hardware=hardware,
    )

    assert route.selected_model == "colibri-local"
    assert route.provider == "local"
    assert route.execution_mode == "local_ram"
    assert "offline_local_only" in route.constraints_applied
    assert "restricted_data_local_only" in route.constraints_applied


def test_colibri_fails_with_actionable_error_when_not_configured(monkeypatch):
    monkeypatch.delenv("FINAI_COLIBRI_BASE_URL", raising=False)
    adapter = ColibriResponseAdapter()
    with pytest.raises(RuntimeError, match="FINAI_COLIBRI_BASE_URL"):
        adapter.generate(
            user_text="Hello",
            intent="FINANCIAL_GUIDANCE",
            verified_result={},
            source="test",
        )
