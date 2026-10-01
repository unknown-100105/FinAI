from router.domain_router import (
    DOMAIN_CALCULATION,
    DOMAIN_MARKET_DATA,
    FinAIDomainRouter,
)


def test_market_calculation_stays_market_data():
    router = FinAIDomainRouter()

    result = router.route(
        "Calculate NIFTY 50 volatility for the last 6 months"
    )

    assert result["domain"] == DOMAIN_MARKET_DATA


def test_market_history_with_calculation_stays_market_data():
    router = FinAIDomainRouter()

    result = router.route(
        "Show NIFTY 50 history and calculate return"
    )

    assert result["domain"] == DOMAIN_MARKET_DATA


def test_generic_calculation_remains_calculation():
    router = FinAIDomainRouter()

    result = router.route(
        "Calculate compound interest on 100000"
    )

    assert result["domain"] == DOMAIN_CALCULATION
