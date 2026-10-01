import torch

from llm.response_adapter import SarvamResponseAdapter


class FakeTokenizer:

    eos_token_id = 0

    def __call__(self, prompt, return_tensors="pt"):
        return {
            "input_ids": torch.tensor([[1, 2, 3]]),
            "attention_mask": torch.tensor([[1, 1, 1]]),
        }

    def decode(self, output, skip_special_tokens=True):
        return (
            "Estimated monthly payments of ₹8,678.23. "
            "The total cost of the loan will be ₹1,082,775.76."
        )


class FakeModel:

    device = torch.device("cpu")

    def generate(self, **kwargs):
        return torch.tensor([[1, 2, 3]])


def build_verified_result():
    return {
        "principal": 1_000_000,
        "annual_rate": 8.5,
        "tenure_months": 240,
        "monthly_emi": 8678.23,
        "total_payment": 2082775.76,
        "total_interest": 1082775.76,
    }


def test_bad_llm_response_is_rejected_and_fallback_used():

    adapter = SarvamResponseAdapter(
        model=FakeModel(),
        tokenizer=FakeTokenizer(),
    )

    result = adapter.generate(
        user_text="Calculate EMI for ₹10 lakh at 8.5% for 20 years",
        intent="EMI_QUERY",
        verified_result=build_verified_result(),
        source="deterministic_finance_engine",
        language="English",
        persona="neutral",
    )

    assert result["status"] == "FALLBACK_VERIFIED"

    assert (
        result["verification"]["passed"]
        is False
    )

    assert (
        "Total payment is ₹2,082,775.76"
        in result["response"]
    )

    assert (
        "₹1,082,775.76 in total interest"
        in result["response"]
    )

    assert (
        result["original_response"]
        == "Estimated monthly payments of ₹8,678.23. "
        "The total cost of the loan will be ₹1,082,775.76."
    )


def test_valid_llm_response_is_accepted():

    class ValidTokenizer(FakeTokenizer):

        def decode(self, output, skip_special_tokens=True):
            return (
                "Your monthly EMI is ₹8,678.23. "
                "Total payment is ₹2,082,775.76, "
                "including ₹1,082,775.76 in total interest."
            )

    adapter = SarvamResponseAdapter(
        model=FakeModel(),
        tokenizer=ValidTokenizer(),
    )

    result = adapter.generate(
        user_text="Calculate EMI",
        intent="EMI_QUERY",
        verified_result=build_verified_result(),
        source="deterministic_finance_engine",
    )

    assert result["status"] == "GENERATED_VERIFIED"
    assert result["verification"]["passed"] is True
