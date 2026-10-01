from math import sqrt
from statistics import mean, stdev
from typing import Dict, List, Optional


class PortfolioEngine:

    @staticmethod
    def valuation(
        assets: List[Dict],
    ) -> Dict:

        if not assets:
            raise ValueError("Portfolio cannot be empty.")

        total_value = 0.0
        total_cost = 0.0

        positions = []

        for asset in assets:

            name = str(asset["name"])

            quantity = float(asset["quantity"])
            current_price = float(asset["current_price"])

            if quantity < 0:
                raise ValueError(
                    f"Quantity cannot be negative for {name}."
                )

            if current_price < 0:
                raise ValueError(
                    f"Current price cannot be negative for {name}."
                )

            market_value = quantity * current_price

            cost_basis = asset.get("cost_basis")

            if cost_basis is not None:
                cost_basis = float(cost_basis)

                if cost_basis < 0:
                    raise ValueError(
                        f"Cost basis cannot be negative for {name}."
                    )

            else:
                cost_basis = market_value

            unrealized_pl = market_value - cost_basis

            total_value += market_value
            total_cost += cost_basis

            positions.append({
                "name": name,
                "quantity": quantity,
                "current_price": current_price,
                "market_value": round(market_value, 2),
                "cost_basis": round(cost_basis, 2),
                "unrealized_pl": round(unrealized_pl, 2),
            })

        for position in positions:

            if total_value > 0:
                weight = (
                    position["market_value"]
                    / total_value
                    * 100
                )
            else:
                weight = 0.0

            position["weight_percent"] = round(
                weight,
                2
            )

        total_pl = total_value - total_cost

        return {
            "total_market_value": round(
                total_value,
                2
            ),
            "total_cost_basis": round(
                total_cost,
                2
            ),
            "total_unrealized_pl": round(
                total_pl,
                2
            ),
            "positions": positions,
        }

    @staticmethod
    def concentration(
        valuation: Dict,
    ) -> Dict:

        positions = valuation["positions"]

        weights = [
            position["weight_percent"]
            for position in positions
        ]

        largest_position = (
            max(weights)
            if weights
            else 0.0
        )

        hhi = sum(
            (weight / 100) ** 2
            for weight in weights
        )

        # HHI-like concentration index scaled to 0–10000.
        hhi_score = hhi * 10000

        return {
            "largest_position_percent": round(
                largest_position,
                2
            ),
            "hhi_concentration_index": round(
                hhi_score,
                2
            ),
            "high_concentration_flag": (
                largest_position >= 50
            ),
        }

    @staticmethod
    def annualized_volatility(
        periodic_returns: List[float],
        periods_per_year: int = 252,
    ) -> float:

        if len(periodic_returns) < 2:
            raise ValueError(
                "At least two return observations are required."
            )

        if periods_per_year <= 0:
            raise ValueError(
                "Periods per year must be greater than zero."
            )

        values = [
            float(value)
            for value in periodic_returns
        ]

        return round(
            stdev(values)
            * sqrt(periods_per_year)
            * 100,
            4
        )

    @staticmethod
    def sharpe_ratio(
        periodic_returns: List[float],
        risk_free_rate_annual: float = 0.0,
        periods_per_year: int = 252,
    ) -> float:

        if len(periodic_returns) < 2:
            raise ValueError(
                "At least two return observations are required."
            )

        if periods_per_year <= 0:
            raise ValueError(
                "Periods per year must be greater than zero."
            )

        values = [
            float(value)
            for value in periodic_returns
        ]

        mean_periodic_return = mean(values)

        annualized_return = (
            mean_periodic_return
            * periods_per_year
        )

        annualized_volatility = (
            stdev(values)
            * sqrt(periods_per_year)
        )

        if annualized_volatility == 0:
            raise ValueError(
                "Sharpe ratio cannot be calculated "
                "when volatility is zero."
            )

        excess_return = (
            annualized_return
            - float(risk_free_rate_annual)
        )

        return round(
            excess_return / annualized_volatility,
            4
        )

    @staticmethod
    def maximum_drawdown(
        periodic_returns: List[float],
    ) -> float:

        if not periodic_returns:
            raise ValueError(
                "Return series cannot be empty."
            )

        wealth = 1.0
        peak = 1.0
        maximum_drawdown = 0.0

        for periodic_return in periodic_returns:

            wealth *= (
                1 + float(periodic_return)
            )

            if wealth > peak:
                peak = wealth

            if peak > 0:
                drawdown = (
                    wealth - peak
                ) / peak

                maximum_drawdown = min(
                    maximum_drawdown,
                    drawdown
                )

        return round(
            abs(maximum_drawdown) * 100,
            4
        )

    @staticmethod
    def risk_report(
        assets: List[Dict],
        periodic_returns: Optional[List[float]] = None,
        risk_free_rate_annual: float = 0.0,
        periods_per_year: int = 252,
    ) -> Dict:

        valuation = PortfolioEngine.valuation(
            assets
        )

        concentration = PortfolioEngine.concentration(
            valuation
        )

        report = {
            "valuation": valuation,
            "concentration": concentration,
            "historical_risk": None,
        }

        if periodic_returns is not None:

            volatility = (
                PortfolioEngine.annualized_volatility(
                    periodic_returns,
                    periods_per_year,
                )
            )

            sharpe = PortfolioEngine.sharpe_ratio(
                periodic_returns,
                risk_free_rate_annual,
                periods_per_year,
            )

            drawdown = (
                PortfolioEngine.maximum_drawdown(
                    periodic_returns
                )
            )

            report["historical_risk"] = {
                "observations": len(periodic_returns),
                "periods_per_year": periods_per_year,
                "annualized_volatility_percent": volatility,
                "sharpe_ratio": sharpe,
                "maximum_drawdown_percent": drawdown,
                "risk_free_rate_annual": (
                    risk_free_rate_annual
                ),
                "source": (
                    "user_supplied_return_series"
                ),
            }

        return report


if __name__ == "__main__":

    engine = PortfolioEngine()

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

    print("=" * 80)
    print("FinAI PORTFOLIO & RISK ENGINE TEST")
    print("=" * 80)

    valuation = engine.valuation(assets)

    print()
    print("VALUATION")
    print(valuation)

    concentration = engine.concentration(
        valuation
    )

    print()
    print("CONCENTRATION")
    print(concentration)

    report = engine.risk_report(
        assets=assets,
        periodic_returns=returns,
        risk_free_rate_annual=0.06,
        periods_per_year=252,
    )

    print()
    print("FULL RISK REPORT")
    print(report)

    print()
    print("PORTFOLIO & RISK ENGINE TEST COMPLETED")
