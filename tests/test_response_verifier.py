from llm.response_verifier import FinancialResponseVerifier


def verified_emi():
    return {
        "principal": 1_000_000,
        "annual_rate": 8.5,
        "tenure_months": 240,
        "monthly_emi": 8678.23,
        "total_payment": 2082775.76,
        "total_interest": 1082775.76,
    }


def test_correct_response_passes():

    verifier = FinancialResponseVerifier()

    response = (
        "Your monthly EMI is ₹8,678.23. "
        "Total payment is ₹2,082,775.76, "
        "including ₹1,082,775.76 in total interest."
    )

    result = verifier.verify_emi(
        response,
        verified_emi(),
    )

    assert result["passed"] is True
    assert result["missing_values"] == []
    assert result["semantic_errors"] == []


def test_missing_total_payment_fails():

    verifier = FinancialResponseVerifier()

    response = (
        "Your monthly EMI is ₹8,678.23. "
        "Total interest is ₹1,082,775.76."
    )

    result = verifier.verify_emi(
        response,
        verified_emi(),
    )

    assert result["passed"] is False

    assert any(
        item["field"] == "total_payment"
        for item in result["missing_values"]
    )


def test_wrong_total_cost_fails():

    verifier = FinancialResponseVerifier()

    response = (
        "Your EMI is ₹8,678.23. "
        "The total cost of the loan is ₹1,082,775.76."
    )

    result = verifier.verify_emi(
        response,
        verified_emi(),
    )

    assert result["passed"] is False


def test_all_verified_values_required():

    verifier = FinancialResponseVerifier()

    response = (
        "Monthly EMI: ₹8,678.23. "
        "Total payment: ₹2,082,775.76. "
        "Total interest: ₹1,082,775.76."
    )

    result = verifier.verify_emi(
        response,
        verified_emi(),
    )

    assert result["passed"] is True
