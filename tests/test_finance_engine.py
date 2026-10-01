import pytest

from finance_engine.engine import FinanceEngine


def test_emi_known_value():
    result = FinanceEngine.calculate_emi(
        principal=1_000_000,
        annual_rate=8.5,
        tenure_months=240,
    )

    assert result.monthly_emi == pytest.approx(
        8678.23,
        abs=0.01
    )

    assert result.total_payment == pytest.approx(
        2082775.76,
        abs=0.01
    )

    assert result.total_interest == pytest.approx(
        1082775.76,
        abs=0.01
    )


def test_emi_zero_interest():
    result = FinanceEngine.calculate_emi(
        principal=120_000,
        annual_rate=0,
        tenure_months=12,
    )

    assert result.monthly_emi == pytest.approx(
        10_000,
        abs=0.01
    )

    assert result.total_interest == pytest.approx(
        0,
        abs=0.01
    )


def test_emi_invalid_principal():
    with pytest.raises(ValueError):
        FinanceEngine.calculate_emi(
            principal=0,
            annual_rate=8,
            tenure_months=120,
        )


def test_emi_invalid_tenure():
    with pytest.raises(ValueError):
        FinanceEngine.calculate_emi(
            principal=100_000,
            annual_rate=8,
            tenure_months=0,
        )


def test_sip_known_value():
    result = FinanceEngine.calculate_sip(
        monthly_investment=10_000,
        annual_return=12,
        years=10,
    )

    assert result.total_invested == pytest.approx(
        1_200_000,
        abs=0.01
    )

    assert result.estimated_value == pytest.approx(
        2_300_386.89,
        abs=0.01
    )

    assert result.estimated_profit == pytest.approx(
        1_100_386.89,
        abs=0.01
    )


def test_sip_zero_return():
    result = FinanceEngine.calculate_sip(
        monthly_investment=5_000,
        annual_return=0,
        years=5,
    )

    assert result.total_invested == pytest.approx(
        300_000,
        abs=0.01
    )

    assert result.estimated_value == pytest.approx(
        300_000,
        abs=0.01
    )

    assert result.estimated_profit == pytest.approx(
        0,
        abs=0.01
    )


def test_sip_invalid_amount():
    with pytest.raises(ValueError):
        FinanceEngine.calculate_sip(
            monthly_investment=0,
            annual_return=12,
            years=10,
        )


def test_compound_interest_known_value():
    result = FinanceEngine.calculate_compound_interest(
        principal=100_000,
        annual_rate=8,
        years=5,
        compounding_frequency=12,
    )

    assert result.final_amount == pytest.approx(
        148984.57,
        abs=0.01
    )

    assert result.total_interest == pytest.approx(
        48984.57,
        abs=0.01
    )


def test_compound_interest_invalid_frequency():
    with pytest.raises(ValueError):
        FinanceEngine.calculate_compound_interest(
            principal=100_000,
            annual_rate=8,
            years=5,
            compounding_frequency=0,
        )


def test_portfolio_total_value():
    assets = [
        {
            "name": "Asset_A",
            "quantity": 10,
            "price": 5000,
        },
        {
            "name": "Asset_B",
            "quantity": 20,
            "price": 2000,
        },
        {
            "name": "Asset_C",
            "quantity": 50,
            "price": 500,
        },
    ]

    result = FinanceEngine.portfolio_summary(assets)

    assert result["total_value"] == pytest.approx(
        115_000,
        abs=0.01
    )

    assert result["concentration"]["Asset_A"] == pytest.approx(
        43.48,
        abs=0.01
    )


def test_portfolio_concentration_flag():
    assets = [
        {
            "name": "Asset_A",
            "quantity": 100,
            "price": 1000,
        },
        {
            "name": "Asset_B",
            "quantity": 10,
            "price": 100,
        },
    ]

    result = FinanceEngine.portfolio_risk_proxy(assets)

    assert result["largest_position_percent"] > 50
    assert result["concentration_flag"] is True


def test_empty_portfolio_rejected():
    with pytest.raises(ValueError):
        FinanceEngine.portfolio_summary([])


def test_negative_asset_quantity_rejected():
    assets = [
        {
            "name": "BadAsset",
            "quantity": -1,
            "price": 100,
        }
    ]

    with pytest.raises(ValueError):
        FinanceEngine.portfolio_summary(assets)
