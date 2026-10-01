from evaluation.sarvam_benchmark_adapter import (
    SarvamBenchmarkAdapter,
)


class FakeProductionAdapter:

    def __init__(self):
        self.calls = []

    def generate(self, **kwargs):
        self.calls.append(kwargs)

        return {
            "status": "GENERATED_VERIFIED",
            "response": "Test response",
        }


def test_benchmark_adapter_uses_production_adapter():

    benchmark = SarvamBenchmarkAdapter()

    fake = FakeProductionAdapter()
    benchmark.adapter = fake

    response = benchmark.generate(
        user_text="My payment failed",
        language="en",
        intent="PAYMENT_FAILED",
        reference_response="Your payment failed.",
    )

    assert response == "Test response"
    assert len(fake.calls) == 1

    call = fake.calls[0]

    assert call["user_text"] == "My payment failed"
    assert call["language"] == "en"
    assert call["intent"] == "PAYMENT_FAILED"
    assert call["source"] == "multilingual_benchmark"
    assert call["persona"] == "neutral"


def test_benchmark_adapter_accepts_verified_result():

    benchmark = SarvamBenchmarkAdapter()

    fake = FakeProductionAdapter()
    benchmark.adapter = fake

    benchmark.generate(
        user_text="Calculate EMI",
        language="en",
        intent="EMI_QUERY",
        reference_response="EMI is ₹8,678.23.",
        verified_result={
            "monthly_emi": 8678.23,
        },
        max_new_tokens=512,
    )

    call = fake.calls[0]

    assert call["verified_result"] == {
        "monthly_emi": 8678.23,
    }

    assert call["max_new_tokens"] == 512


def test_model_id():

    benchmark = SarvamBenchmarkAdapter()

    assert benchmark.model_id == "sarvam-1"
