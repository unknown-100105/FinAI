from llm.model_gateway import ModelGateway
from llm.response_service import ResponseService


class SequencedAdapter:
    def __init__(self, results):
        self.results = list(results)
        self.calls = []

    def generate(self, **kwargs):
        self.calls.append(kwargs)
        if not self.results:
            raise RuntimeError("No test result configured")
        result = self.results.pop(0)
        return dict(result)


def make_service(adapter):
    gateway = ModelGateway(default_model="gemini-cloud")
    gateway.register(
        "gemini-cloud",
        adapter,
        capabilities=["response_generation"],
    )
    return ResponseService(gateway=gateway)


def generated(response, truncated):
    return {
        "status": "GENERATED",
        "model_id": "gemini-cloud",
        "response": response,
        "metrics": {},
        "generation_complete": not truncated,
        "truncated": truncated,
        "finish_reason": "length" if truncated else "stop",
    }


def test_truncated_generation_is_retried_and_completed():
    adapter = SequencedAdapter([
        generated("This response is cut", truncated=True),
        generated(
            "This response is complete and ends normally.",
            truncated=False,
        ),
    ])

    service = make_service(adapter)

    result = service.generate(
        user_text="Explain digital payments.",
        intent="SUPPORT_REQUEST",
        verified_result={},
        source="support_system",
        max_new_tokens=160,
    )

    assert len(adapter.calls) == 2
    assert adapter.calls[0]["max_new_tokens"] == 160
    assert adapter.calls[1]["max_new_tokens"] == 320
    assert result["status"] == "GENERATED"
    assert result["generation_complete"] is True
    assert result["truncated"] is False
    assert result["finish_reason"] == "stop"
    assert result["retry_after_truncation"] is True


def test_persistent_truncation_returns_safe_incomplete_status():
    adapter = SequencedAdapter([
        generated("Still incomplete", truncated=True),
        generated("Still incomplete after retry", truncated=True),
    ])

    service = make_service(adapter)

    result = service.generate(
        user_text="Explain digital payments.",
        intent="SUPPORT_REQUEST",
        verified_result={},
        source="support_system",
        max_new_tokens=160,
    )

    assert len(adapter.calls) == 2
    assert result["status"] == "INCOMPLETE_GENERATION"
    assert result["generation_complete"] is False
    assert result["truncated"] is True
    assert result["finish_reason"] == "length"
    assert "couldn't complete" in result["response"].lower()
    assert result["original_response"] == "Still incomplete after retry"
