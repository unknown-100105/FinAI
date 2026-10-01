from llm.response_service import ResponseService
from llm.response_adapter import SarvamResponseAdapter


def test_production_sarvam_adapter_is_lazy():

    service = ResponseService()

    adapter = service.gateway.get_adapter("sarvam-1")

    assert isinstance(
        adapter,
        SarvamResponseAdapter,
    )

    assert adapter.lazy_load is True
    assert adapter.loaded is False
    assert adapter.model is None
    assert adapter.tokenizer is None
