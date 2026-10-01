from xai.integration import XAIIntegration


def test_portfolio_xai_trace():

    integration = XAIIntegration(
        session_id="portfolio-test-001",
        user_text="Analyze my portfolio risk",
    )

    integration.record_portfolio(
        status="ANALYZED",
        portfolio={
            "total_market_value": 115000.0,
            "total_cost_basis": 112000.0,
            "total_unrealized_pl": 3000.0,
        },
        concentration={
            "largest_position_percent": 43.48,
            "hhi_concentration_index": 3572.79,
            "high_concentration_flag": False,
        },
        historical_risk={
            "observations": 10,
            "annualized_volatility_percent": 12.1417,
            "sharpe_ratio": 2.6191,
            "maximum_drawdown_percent": 1.2,
            "source": "user_supplied_return_series",
        },
        xai_sources={
            "valuation_source": "supplied_portfolio_holdings",
            "concentration_source": "derived_from_current_holdings",
            "historical_risk_source": "user_supplied_return_series",
        },
    )

    integration.record_final(
        stage="portfolio_engine",
        status="ANALYZED",
        message="Portfolio analysis completed.",
    )

    path = integration.save()

    assert path.exists()

    assert (
        integration.trace.data["portfolio"]["status"]
        == "ANALYZED"
    )

    assert (
        integration.trace.data["portfolio"]["portfolio"]
        ["total_market_value"]
        == 115000.0
    )

    assert (
        integration.trace.data["portfolio"]["historical_risk"]
        ["source"]
        == "user_supplied_return_series"
    )
