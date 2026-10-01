from typing import Dict, List, Optional

from portfolio.engine import PortfolioEngine


class PortfolioService:

    def __init__(self):
        self.engine = PortfolioEngine()

    def analyze(
        self,
        assets: List[Dict],
        periodic_returns: Optional[List[float]] = None,
        risk_free_rate_annual: float = 0.0,
        periods_per_year: int = 252,
    ):

        report = self.engine.risk_report(
            assets=assets,
            periodic_returns=periodic_returns,
            risk_free_rate_annual=risk_free_rate_annual,
            periods_per_year=periods_per_year,
        )

        valuation = report["valuation"]
        concentration = report["concentration"]
        historical = report["historical_risk"]

        return {
            "status": "ANALYZED",

            "portfolio": {
                "total_market_value": valuation[
                    "total_market_value"
                ],
                "total_cost_basis": valuation[
                    "total_cost_basis"
                ],
                "total_unrealized_pl": valuation[
                    "total_unrealized_pl"
                ],
                "positions": valuation[
                    "positions"
                ],
            },

            "concentration": concentration,

            "historical_risk": historical,

            "xai": {
                "valuation_source": (
                    "supplied_portfolio_holdings"
                ),
                "concentration_source": (
                    "derived_from_current_holdings"
                ),
                "historical_risk_source": (
                    historical["source"]
                    if historical
                    else None
                ),
            },
        }


if __name__ == "__main__":

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

    result = service.analyze(
        assets=assets,
        periodic_returns=returns,
        risk_free_rate_annual=0.06,
        periods_per_year=252,
    )

    print("=" * 80)
    print("FinAI PORTFOLIO SERVICE TEST")
    print("=" * 80)

    print()
    print("STATUS:", result["status"])

    print()
    print("PORTFOLIO:")
    print(result["portfolio"])

    print()
    print("CONCENTRATION:")
    print(result["concentration"])

    print()
    print("HISTORICAL RISK:")
    print(result["historical_risk"])

    print()
    print("XAI SOURCES:")
    print(result["xai"])
