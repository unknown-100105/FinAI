import pytest

from portfolio.engine import PortfolioEngine


def portfolio():

    return [
        {
            "name": "Asset_A",
            "quantity": 10,
            "current_price": 5000,
            "cost_basis": 45000,
        },
        {
            "name": "Asset_B",
            "quantity": 20,
            "current_price": 2000,
            "cost_basis": 42000,
        },
        {
            "name": "Asset_C",
            "quantity": 50,
            "current_price": 500,
            "cost_basis": 25000,
        },
    ]


def test_valuation():

    result = PortfolioEngine.valuation(
        portfolio()
    )

    assert result["total_market_value"] == pytest.approx(
        115000,
        abs=0.01
    )

    assert result["total_cost_basis"] == pytest.approx(
        112000,
        abs=0.01
    )

    assert result["total_unrealized_pl"] == pytest.approx(
        3000,
        abs=0.01
    )


def test_position_weights():

    result = PortfolioEngine.valuation(
        portfolio()
    )

    weights = {
        item["name"]: item["weight_percent"]
        for item in result["positions"]
    }

    assert weights["Asset_A"] == pytest.approx(
        43.48,
        abs=0.01
    )

    assert weights["Asset_B"] == pytest.approx(
        34.78,
        abs=0.01
    )

    assert weights["Asset_C"] == pytest.approx(
        21.74,
        abs=0.01
    )


def test_concentration():

    valuation = PortfolioEngine.valuation(
        portfolio()
    )

    result = PortfolioEngine.concentration(
        valuation
    )

    assert result["largest_position_percent"] == pytest.approx(
        43.48,
        abs=0.01
    )

    assert result["high_concentration_flag"] is False


def test_high_concentration():

    assets = [
        {
            "name": "Asset_A",
            "quantity": 100,
            "current_price": 1000,
        },
        {
            "name": "Asset_B",
            "quantity": 10,
            "current_price": 100,
        },
    ]

    valuation = PortfolioEngine.valuation(
        assets
    )

    result = PortfolioEngine.concentration(
        valuation
    )

    assert result["high_concentration_flag"] is True
    assert result["largest_position_percent"] > 50


def test_volatility():

    returns = [
        0.01,
        -0.005,
        0.008,
        -0.012,
        0.006,
        0.004,
        -0.003,
        0.009,
        -0.007,
        0.005,
    ]

    result = PortfolioEngine.annualized_volatility(
        returns
    )

    assert result > 0


def test_sharpe():

    returns = [
        0.010,
        -0.005,
        0.008,
        -0.012,
        0.006,
        0.004,
        -0.003,
        0.009,
        -0.007,
        0.005,
    ]

    result = PortfolioEngine.sharpe_ratio(
        returns,
        risk_free_rate_annual=0.06,
    )

    assert isinstance(result, float)


def test_maximum_drawdown():

    returns = [
        0.10,
        -0.20,
        0.05,
        -0.10,
    ]

    result = PortfolioEngine.maximum_drawdown(
        returns
    )

    assert result > 0


def test_risk_report_without_history():

    result = PortfolioEngine.risk_report(
        assets=portfolio()
    )

    assert result["historical_risk"] is None
    assert "valuation" in result
    assert "concentration" in result


def test_risk_report_with_history():

    returns = [
        0.01,
        -0.005,
        0.008,
        -0.012,
        0.006,
        0.004,
    ]

    result = PortfolioEngine.risk_report(
        assets=portfolio(),
        periodic_returns=returns,
    )

    assert result["historical_risk"] is not None

    assert (
        result["historical_risk"]["observations"]
        == 6
    )


def test_empty_portfolio():

    with pytest.raises(ValueError):
        PortfolioEngine.valuation([])


def test_negative_quantity():

    assets = [
        {
            "name": "BadAsset",
            "quantity": -1,
            "current_price": 100,
        }
    ]

    with pytest.raises(ValueError):
        PortfolioEngine.valuation(assets)


def test_insufficient_returns():

    with pytest.raises(ValueError):
        PortfolioEngine.annualized_volatility(
            [0.01]
        )
