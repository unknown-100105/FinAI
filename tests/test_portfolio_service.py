from portfolio.services.portfolio_service import PortfolioService


def test_portfolio_service():

    service = PortfolioService()

    assets = [
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

    result = service.analyze(
        assets=assets
    )

    assert result["status"] == "ANALYZED"

    assert result["portfolio"]["total_market_value"] == 115000
    assert result["portfolio"]["total_unrealized_pl"] == 3000

    assert (
        result["concentration"]["largest_position_percent"]
        == 43.48
    )

    assert (
        result["historical_risk"]
        is None
    )


def test_portfolio_service_with_history():

    service = PortfolioService()

    assets = [
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
    ]

    returns = [
        0.01,
        -0.005,
        0.008,
        -0.012,
        0.006,
        0.004,
    ]

    result = service.analyze(
        assets=assets,
        periodic_returns=returns,
        risk_free_rate_annual=0.06,
    )

    assert result["historical_risk"] is not None

    assert (
        result["historical_risk"]["observations"]
        == 6
    )

    assert (
        result["xai"]["historical_risk_source"]
        == "user_supplied_return_series"
    )
