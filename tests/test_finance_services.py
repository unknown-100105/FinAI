import pytest

from finance_engine.emi_service import EMIService
from finance_engine.sip_service import SIPService
from finance_engine.interest_service import InterestService


def test_sip_service():
    service = SIPService()

    result = service.process(
        monthly_investment=10_000,
        annual_return=12,
        years=10,
    )

    assert result["status"] == "CALCULATED"
    assert "assumptions" in result
    assert any("not guaranteed" in item.lower() for item in result["assumptions"])

    assert result["result"]["total_invested"] == pytest.approx(
        1_200_000,
        abs=0.01
    )

    assert result["result"]["estimated_value"] == pytest.approx(
        2_300_386.89,
        abs=0.01
    )


def test_sip_invalid_amount():
    service = SIPService()

    result = service.process(
        monthly_investment=0,
        annual_return=12,
        years=10,
    )

    assert result["status"] == "INVALID_PARAMETERS"
    assert result["result"] is None


def test_interest_service():
    service = InterestService()

    result = service.process(
        principal=100_000,
        annual_rate=8,
        years=5,
        compounding_frequency=12,
    )

    assert result["status"] == "CALCULATED"
    assert "assumptions" in result
    assert any("fixed" in item.lower() for item in result["assumptions"])

    assert result["result"]["final_amount"] == pytest.approx(
        148984.57,
        abs=0.01
    )

    assert result["result"]["total_interest"] == pytest.approx(
        48984.57,
        abs=0.01
    )


def test_interest_invalid_frequency():
    service = InterestService()

    result = service.process(
        principal=100_000,
        annual_rate=8,
        years=5,
        compounding_frequency=0,
    )

    assert result["status"] == "INVALID_PARAMETERS"
    assert result["result"] is None


def test_emi_service_discloses_calculation_assumptions():
    result = EMIService().process(
        "Calculate EMI for ₹5 lakh at 8% for 5 years"
    )
    assert result["status"] == "CALCULATED"
    assert "assumptions" in result
    assert any("monthly" in item.lower() for item in result["assumptions"])
