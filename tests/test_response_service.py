from llm.response_service import ResponseService
from llm.rllm_finqa_adapter import RLLMFinQAModelAdapter
from llm.response_adapter import SarvamResponseAdapter
from llm.cloud.gemini_adapter import GeminiResponseAdapter


def test_enabled_models_are_registered():
    service = ResponseService()

    assert service.gateway.available_models() == [
        "gemini-cloud",
        "rllm-finqa-4b",
    ]


def test_default_model_is_gemini():
    service = ResponseService()

    assert service.gateway.default_model == "gemini-cloud"


def test_financial_qa_intents_use_gemini():
    service = ResponseService()

    assert service.select_model("EMI_QUERY") == "gemini-cloud"
    assert service.select_model("INTEREST_QUERY") == "gemini-cloud"


def test_general_response_intents_use_gemini():
    service = ResponseService()

    assert service.select_model("ACCOUNT_BALANCE") == "gemini-cloud"


def test_rllm_adapter_is_lazy():
    service = ResponseService()

    adapter = service.gateway.get_adapter("rllm-finqa-4b")

    assert isinstance(adapter, RLLMFinQAModelAdapter)
    assert adapter.loaded is False
    assert adapter.model is None
    assert adapter.tokenizer is None


def test_gemini_adapter_is_registered():
    service = ResponseService()

    adapter = service.gateway.get_adapter("gemini-cloud")

    assert isinstance(adapter, GeminiResponseAdapter)


def test_sarvam_is_not_registered_when_disabled():
    service = ResponseService()

    try:
        service.gateway.get_adapter("sarvam-1")
    except ValueError:
        return

    raise AssertionError("Disabled Sarvam model was registered.")
