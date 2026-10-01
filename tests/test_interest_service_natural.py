from finance_engine.interest_service import InterestService


def test_interest_natural_language():

    service = InterestService()

    result = service.process(
        "Calculate compound interest on ₹1 lakh at 8% for 5 years monthly"
    )

    assert result["status"] == "CALCULATED"
    assert result["parameters"]["principal"] == 100000
    assert result["parameters"]["annual_rate"] == 8
    assert result["parameters"]["years"] == 5
    assert result["parameters"]["compounding_frequency"] == 12

    assert result["result"]["final_amount"] == 148984.57
    assert result["result"]["total_interest"] == 48984.57


def test_interest_quarterly():

    service = InterestService()

    result = service.process(
        "₹500000 at 7.5% for 10 years quarterly compounding"
    )

    assert result["status"] == "CALCULATED"
    assert result["parameters"]["compounding_frequency"] == 4


def test_interest_missing_parameters():

    service = InterestService()

    result = service.process(
        "Calculate compound interest"
    )

    assert result["status"] == "MISSING_PARAMETERS"
    assert result["result"] is None


def test_interest_yearly():

    service = InterestService()

    result = service.process(
        "₹500000 at 7.5% for 10 years yearly"
    )

    assert result["status"] == "CALCULATED"
    assert result["parameters"]["compounding_frequency"] == 1
