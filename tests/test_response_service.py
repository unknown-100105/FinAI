from llm.response_service import ResponseService
from llm.rllm_finqa_adapter import RLLMFinQAModelAdapter
from llm.response_adapter import SarvamResponseAdapter


def test_enabled_models_are_registered():
    service = ResponseService()

    assert service.gateway.available_models() == [
        "rllm-finqa-4b",
        "sarvam-1",
    ]


def test_default_model_is_sarvam():
    service = ResponseService()

    assert service.gateway.default_model == "sarvam-1"


def test_financial_qa_intents_use_rllm():
    service = ResponseService()

    assert service.select_model("EMI_QUERY") == "rllm-finqa-4b"
    assert service.select_model("INTEREST_QUERY") == "rllm-finqa-4b"


def test_general_response_intents_use_sarvam():
    service = ResponseService()

    assert service.select_model("ACCOUNT_BALANCE") == "sarvam-1"


def test_rllm_adapter_is_lazy():
    service = ResponseService()

    adapter = service.gateway.get_adapter("rllm-finqa-4b")

    assert isinstance(adapter, RLLMFinQAModelAdapter)
    assert adapter.loaded is False
    assert adapter.model is None
    assert adapter.tokenizer is None


def test_sarvam_adapter_is_registered():
    service = ResponseService()

    adapter = service.gateway.get_adapter("sarvam-1")

    assert isinstance(adapter, SarvamResponseAdapter)
