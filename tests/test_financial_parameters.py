import pytest

from finance_engine.parsing.parameters import (
    FinancialParameterParser,
    FinancialParameterValidator,
)


def test_emi_lakh_years():
    params = FinancialParameterParser.parse_emi(
        "Calculate EMI for ₹10 lakh at 8.5% for 20 years"
    )

    assert params["principal"] == pytest.approx(1_000_000)
    assert params["annual_rate"] == pytest.approx(8.5)
    assert params["tenure_months"] == 240

    result = FinancialParameterValidator.validate_emi(params)

    assert result["valid"] is True


def test_emi_months():
    params = FinancialParameterParser.parse_emi(
        "EMI for 500000 at 9% for 60 months"
    )

    assert params["principal"] == pytest.approx(500_000)
    assert params["annual_rate"] == pytest.approx(9)
    assert params["tenure_months"] == 60


def test_emi_incomplete():
    params = FinancialParameterParser.parse_emi(
        "Calculate my EMI"
    )

    result = FinancialParameterValidator.validate_emi(params)

    assert result["valid"] is False

    assert set(result["missing"]) == {
        "loan amount",
        "annual interest rate",
        "loan tenure",
    }


def test_emi_lakh_percent_years():
    params = FinancialParameterParser.parse_emi(
        "What is EMI for Rs 12 lakh at 7.5 percent for 10 years"
    )

    assert params["principal"] == pytest.approx(1_200_000)
    assert params["annual_rate"] == pytest.approx(7.5)
    assert params["tenure_months"] == 120


def test_negative_loan_rejected():
    result = FinancialParameterValidator.validate_emi({
        "principal": -100_000,
        "annual_rate": 8,
        "tenure_months": 120,
    })

    assert result["valid"] is False


def test_negative_rate_rejected():
    result = FinancialParameterValidator.validate_emi({
        "principal": 100_000,
        "annual_rate": -1,
        "tenure_months": 120,
    })

    assert result["valid"] is False


def test_zero_tenure_rejected():
    result = FinancialParameterValidator.validate_emi({
        "principal": 100_000,
        "annual_rate": 8,
        "tenure_months": 0,
    })

    assert result["valid"] is False
