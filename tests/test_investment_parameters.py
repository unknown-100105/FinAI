from finance_engine.parsing.investment_parameters import (
    SIPParameterParser,
    SIPParameterValidator,
    InterestParameterParser,
    InterestParameterValidator,
)


def test_sip_parser():

    params = SIPParameterParser.parse(
        "Invest ₹10,000 per month for 10 years at 12% return"
    )

    assert params["monthly_investment"] == 10000
    assert params["annual_return"] == 12
    assert params["years"] == 10

    result = SIPParameterValidator.validate(params)

    assert result["valid"] is True


def test_sip_parser_k():

    params = SIPParameterParser.parse(
        "SIP of 10k monthly for 15 years at 10%"
    )

    assert params["monthly_investment"] == 10000
    assert params["annual_return"] == 10
    assert params["years"] == 15


def test_sip_missing():

    params = SIPParameterParser.parse(
        "Calculate my SIP"
    )

    result = SIPParameterValidator.validate(params)

    assert result["valid"] is False

    assert set(result["missing"]) == {
        "monthly investment",
        "expected annual return",
        "investment period",
    }


def test_interest_parser():

    params = InterestParameterParser.parse(
        "Calculate compound interest on ₹1 lakh at 8% for 5 years monthly"
    )

    assert params["principal"] == 100000
    assert params["annual_rate"] == 8
    assert params["years"] == 5
    assert params["compounding_frequency"] == 12

    result = InterestParameterValidator.validate(params)

    assert result["valid"] is True


def test_interest_quarterly():

    params = InterestParameterParser.parse(
        "₹500000 at 7.5% for 10 years quarterly compounding"
    )

    assert params["principal"] == 500000
    assert params["annual_rate"] == 7.5
    assert params["years"] == 10
    assert params["compounding_frequency"] == 4


def test_interest_yearly():

    params = InterestParameterParser.parse(
        "₹500000 at 7.5% for 10 years yearly"
    )

    assert params["compounding_frequency"] == 1


def test_interest_missing():

    params = InterestParameterParser.parse(
        "Calculate compound interest"
    )

    result = InterestParameterValidator.validate(params)

    assert result["valid"] is False


def test_negative_interest_rejected():

    result = InterestParameterValidator.validate({
        "principal": 100000,
        "annual_rate": -5,
        "years": 5,
        "compounding_frequency": 12,
    })

    assert result["valid"] is False
