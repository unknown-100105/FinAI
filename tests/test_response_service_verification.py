from llm.response_service import ResponseService


VERIFIED = {
    "principal": 1_000_000,
    "annual_rate": 8.5,
    "tenure_months": 240,
    "monthly_emi": 8678.23,
    "total_payment": 2082775.76,
    "total_interest": 1082775.76,
}


class FakeGateway:

    def __init__(self, response):
        self.response = response
        self.calls = []

    def generate(self, **kwargs):
        self.calls.append(kwargs)

        return {
            "status": "GENERATED",
            "model_id": "fake-model",
            "source": kwargs["source"],
            "language": kwargs["language"],
            "persona": kwargs["persona"],
            "response": self.response,
            "metrics": {},
        }


def test_good_model_response_is_verified():

    response = (
        "Monthly EMI: ₹8,678.23. "
        "Total payment: ₹2,082,775.76. "
        "Total interest: ₹1,082,775.76."
    )

    gateway = FakeGateway(response)
    service = ResponseService(gateway=gateway)

    result = service.generate(
        user_text="Calculate EMI",
        intent="EMI_QUERY",
        verified_result=VERIFIED,
        source="deterministic_finance_engine",
    )

    assert result["status"] == "GENERATED_VERIFIED"
    assert result["response"] == response
    assert result["verification"]["passed"] is True
    assert result["claim_verification"]["passed"] is True
    assert len(gateway.calls) == 1


def test_missing_model_value_triggers_verified_fallback():

    response = (
        "Monthly EMI: ₹8,678.23. "
        "Total interest: ₹1,082,775.76."
    )

    gateway = FakeGateway(response)
    service = ResponseService(gateway=gateway)

    result = service.generate(
        user_text="Calculate EMI",
        intent="EMI_QUERY",
        verified_result=VERIFIED,
        source="deterministic_finance_engine",
    )

    assert result["status"] == "FALLBACK_VERIFIED"
    assert result["original_response"] == response

    assert (
        result["fallback_verification"]["passed"]
        is True
    )

    assert (
        result["fallback_claim_verification"]["passed"]
        is True
    )

    assert "₹8,678.23" in result["response"]
    assert "₹2,082,775.76" in result["response"]
    assert "₹1,082,775.76" in result["response"]


def test_wrong_numeric_value_triggers_verified_fallback():

    response = (
        "Monthly EMI: ₹9,000.00. "
        "Total payment: ₹2,082,775.76. "
        "Total interest: ₹1,082,775.76."
    )

    gateway = FakeGateway(response)
    service = ResponseService(gateway=gateway)

    result = service.generate(
        user_text="Calculate EMI",
        intent="EMI_QUERY",
        verified_result=VERIFIED,
        source="deterministic_finance_engine",
    )

    assert result["status"] == "FALLBACK_VERIFIED"
    assert result["original_response"] == response
    assert "₹8,678.23" in result["response"]
    assert "₹9,000.00" not in result["response"]


def test_indian_number_grouping_is_verified_as_numeric_equivalent():

    response = (
        "Monthly EMI: ₹8,678.23. "
        "Total payment: ₹20,82,775.76. "
        "Total interest: ₹10,82,775.76."
    )

    gateway = FakeGateway(response)
    service = ResponseService(gateway=gateway)

    result = service.generate(
        user_text="Calculate EMI",
        intent="EMI_QUERY",
        verified_result=VERIFIED,
        source="deterministic_finance_engine",
    )

    assert result["status"] == "GENERATED_VERIFIED"
    assert result["verification"]["passed"] is True
    assert result["claim_verification"]["passed"] is True
    assert result["response"] == response


def test_rllm_model_id_is_preserved_in_verified_result():

    response = (
        "Monthly EMI: ₹8,678.23. "
        "Total payment: ₹2,082,775.76. "
        "Total interest: ₹1,082,775.76."
    )

    gateway = FakeGateway(response)
    service = ResponseService(gateway=gateway)

    result = service.generate(
        user_text="Calculate EMI",
        intent="EMI_QUERY",
        verified_result=VERIFIED,
        source="deterministic_finance_engine",
        model_id="rllm-finqa-4b",
    )

    assert result["model_id"] == "rllm-finqa-4b"
    assert result["selection"]["model_id"] == "rllm-finqa-4b"
    assert result["selection"]["capability"] == "financial_qa"
