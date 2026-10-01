from response_engine.financial import FinancialResponseEngine


def test_emi_response_contains_verified_values():

    engine = FinancialResponseEngine()

    result = {
        "status": "CALCULATED",
        "result": {
            "principal": 1_000_000,
            "annual_rate": 8.5,
            "tenure_months": 240,
            "monthly_emi": 8678.23,
            "total_payment": 2082775.76,
            "total_interest": 1082775.76,
        }
    }

    text = engine.generate(
        intent="EMI_QUERY",
        result=result,
        status="CALCULATED",
    )

    assert "₹1,000,000.00" in text
    assert "8.50%" in text
    assert "240 months" in text
    assert "₹8,678.23" in text
    assert "₹2,082,775.76" in text
    assert "₹1,082,775.76" in text


def test_missing_parameters_response():

    engine = FinancialResponseEngine()

    result = {
        "status": "MISSING_PARAMETERS",
        "missing": [
            "loan amount",
            "annual interest rate",
            "loan tenure",
        ]
    }

    text = engine.generate(
        intent="EMI_QUERY",
        result=result,
        status="MISSING_PARAMETERS",
    )

    assert "loan amount" in text
    assert "annual interest rate" in text
    assert "loan tenure" in text


def test_hype_persona_changes_tone():

    engine = FinancialResponseEngine()

    result = {
        "status": "CALCULATED",
        "result": {
            "principal": 1_000_000,
            "annual_rate": 8.5,
            "tenure_months": 240,
            "monthly_emi": 8678.23,
            "total_payment": 2082775.76,
            "total_interest": 1082775.76,
        }
    }

    text = engine.generate(
        intent="EMI_QUERY",
        result=result,
        status="CALCULATED",
        persona="hype",
    )

    assert "Here is your EMI breakdown" in text


def test_stern_persona_changes_tone():

    engine = FinancialResponseEngine()

    result = {
        "status": "CALCULATED",
        "result": {
            "principal": 1_000_000,
            "annual_rate": 8.5,
            "tenure_months": 240,
            "monthly_emi": 8678.23,
            "total_payment": 2082775.76,
            "total_interest": 1082775.76,
        }
    }

    text = engine.generate(
        intent="EMI_QUERY",
        result=result,
        status="CALCULATED",
        persona="stern",
    )

    assert "calculation completed" in text.lower()
