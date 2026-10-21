from dataclasses import dataclass
from math import isfinite, pow
from statistics import mean
from typing import Dict, List


def _require_finite_parameters(**values) -> None:
    for name, value in values.items():
        try:
            finite = isfinite(float(value))
        except (TypeError, ValueError, OverflowError):
            finite = False
        if not finite:
            raise ValueError(f"{name} must be a finite numeric value.")


@dataclass
class EMIResult:
    principal: float
    annual_rate: float
    tenure_months: int
    monthly_emi: float
    total_payment: float
    total_interest: float


@dataclass
class SIPResult:
    monthly_investment: float
    annual_return: float
    years: int
    total_invested: float
    estimated_value: float
    estimated_profit: float


@dataclass
class CompoundInterestResult:
    principal: float
    annual_rate: float
    years: int
    compounding_frequency: int
    final_amount: float
    total_interest: float


class FinanceEngine:

    # ---------------------------------------------------------
    # EMI
    # ---------------------------------------------------------

    @staticmethod
    def calculate_emi(
        principal: float,
        annual_rate: float,
        tenure_months: int,
    ) -> EMIResult:

        _require_finite_parameters(
            principal=principal, annual_rate=annual_rate, tenure_months=tenure_months
        )
        if not float(tenure_months).is_integer():
            raise ValueError("Tenure must be a whole number of months.")
        _require_finite_parameters(
            principal=principal,
            annual_rate=annual_rate,
            years=years,
            compounding_frequency=compounding_frequency,
        )
        if not float(years).is_integer():
            raise ValueError("Investment period must be a whole number of years.")
        if not float(compounding_frequency).is_integer():
            raise ValueError("Compounding frequency must be a whole number.")
        if principal <= 0:
            raise ValueError("Principal must be greater than zero.")

        if annual_rate < 0:
            raise ValueError("Annual interest rate cannot be negative.")

        if tenure_months <= 0:
            raise ValueError("Tenure must be greater than zero.")

        monthly_rate = annual_rate / 100 / 12

        if monthly_rate == 0:
            emi = principal / tenure_months
        else:
            try:
                factor = pow(
                    1 + monthly_rate,
                    tenure_months
                )
            except OverflowError as exc:
                raise ValueError("EMI inputs exceed the supported numeric range.") from exc

            emi = (
                principal
                * monthly_rate
                * factor
                / (factor - 1)
            )

        total_payment = emi * tenure_months
        total_interest = total_payment - principal

        return EMIResult(
            principal=round(principal, 2),
            annual_rate=round(annual_rate, 4),
            tenure_months=tenure_months,
            monthly_emi=round(emi, 2),
            total_payment=round(total_payment, 2),
            total_interest=round(total_interest, 2),
        )

    # ---------------------------------------------------------
    # SIP
    # ---------------------------------------------------------

    @staticmethod
    def calculate_sip(
        monthly_investment: float,
        annual_return: float,
        years: int,
    ) -> SIPResult:

        _require_finite_parameters(
            monthly_investment=monthly_investment,
            annual_return=annual_return,
            years=years,
        )
        if not float(years).is_integer():
            raise ValueError("Investment period must be a whole number of years.")
        if monthly_investment <= 0:
            raise ValueError(
                "Monthly investment must be greater than zero."
            )

        if annual_return < 0:
            raise ValueError(
                "Expected annual return cannot be negative."
            )

        if years <= 0:
            raise ValueError(
                "Investment period must be greater than zero."
            )

        months = years * 12

        monthly_rate = annual_return / 100 / 12

        total_invested = monthly_investment * months

        if monthly_rate == 0:
            estimated_value = total_invested
        else:
            try:
                estimated_value = (
                    monthly_investment
                    * (
                        ((1 + monthly_rate) ** months - 1)
                        / monthly_rate
                    )
                )
            except OverflowError as exc:
                raise ValueError("SIP inputs exceed the supported numeric range.") from exc

        estimated_profit = (
            estimated_value - total_invested
        )

        return SIPResult(
            monthly_investment=round(monthly_investment, 2),
            annual_return=round(annual_return, 4),
            years=years,
            total_invested=round(total_invested, 2),
            estimated_value=round(estimated_value, 2),
            estimated_profit=round(estimated_profit, 2),
        )

    # ---------------------------------------------------------
    # Compound Interest
    # ---------------------------------------------------------

    @staticmethod
    def calculate_compound_interest(
        principal: float,
        annual_rate: float,
        years: int,
        compounding_frequency: int = 12,
    ) -> CompoundInterestResult:

        if principal <= 0:
            raise ValueError("Principal must be greater than zero.")

        if annual_rate < 0:
            raise ValueError("Annual interest rate cannot be negative.")

        if years <= 0:
            raise ValueError(
                "Investment period must be greater than zero."
            )

        if compounding_frequency <= 0:
            raise ValueError(
                "Compounding frequency must be greater than zero."
            )

        try:
            final_amount = (
                principal
                * (
                    1 + annual_rate / 100
                    / compounding_frequency
                )
                ** (
                    compounding_frequency * years
                )
            )
        except OverflowError as exc:
            raise ValueError("Compound-interest inputs exceed the supported numeric range.") from exc

        total_interest = final_amount - principal

        return CompoundInterestResult(
            principal=round(principal, 2),
            annual_rate=round(annual_rate, 4),
            years=years,
            compounding_frequency=compounding_frequency,
            final_amount=round(final_amount, 2),
            total_interest=round(total_interest, 2),
        )

    # ---------------------------------------------------------
    # Portfolio metrics
    # ---------------------------------------------------------

    @staticmethod
    def portfolio_summary(
        assets: List[Dict],
    ) -> Dict:

        if not assets:
            raise ValueError("Portfolio cannot be empty.")

        total_value = 0.0

        for asset in assets:

            quantity = float(asset.get("quantity", 0))
            price = float(asset.get("price", 0))

            if quantity < 0:
                raise ValueError(
                    "Asset quantity cannot be negative."
                )

            if price < 0:
                raise ValueError(
                    "Asset price cannot be negative."
                )

            total_value += quantity * price

        if total_value == 0:
            return {
                "total_value": 0.0,
                "assets": [],
                "concentration": {},
            }

        allocation = {}

        for asset in assets:

            name = str(
                asset.get("name", "UNKNOWN")
            )

            value = (
                float(asset.get("quantity", 0))
                * float(asset.get("price", 0))
            )

            allocation[name] = round(
                value / total_value * 100,
                2
            )

        return {
            "total_value": round(total_value, 2),
            "assets": assets,
            "concentration": allocation,
        }

    @staticmethod
    def portfolio_risk_proxy(
        assets: List[Dict],
    ) -> Dict:
        """
        Simple deterministic concentration-based risk proxy.

        This is NOT a market-risk model and should not be presented
        as a professional investment risk score.
        """

        summary = FinanceEngine.portfolio_summary(
            assets
        )

        concentrations = list(
            summary["concentration"].values()
        )

        if not concentrations:
            return {
                "total_value": 0.0,
                "largest_position_percent": 0.0,
                "average_position_percent": 0.0,
                "concentration_flag": False,
            }

        largest = max(concentrations)
        average = mean(concentrations)

        return {
            "total_value": summary["total_value"],
            "largest_position_percent": round(
                largest,
                2
            ),
            "average_position_percent": round(
                average,
                2
            ),
            "concentration_flag": largest >= 50.0,
        }


if __name__ == "__main__":

    engine = FinanceEngine()

    print("=" * 80)
    print("FinAI DETERMINISTIC FINANCE ENGINE TEST")
    print("=" * 80)

    # ---------------------------------------------------------
    # EMI
    # ---------------------------------------------------------

    emi = engine.calculate_emi(
        principal=1000000,
        annual_rate=8.5,
        tenure_months=240,
    )

    print()
    print("EMI")
    print("Principal:", emi.principal)
    print("Annual rate:", emi.annual_rate)
    print("Tenure:", emi.tenure_months)
    print("Monthly EMI:", emi.monthly_emi)
    print("Total payment:", emi.total_payment)
    print("Total interest:", emi.total_interest)

    # ---------------------------------------------------------
    # SIP
    # ---------------------------------------------------------

    sip = engine.calculate_sip(
        monthly_investment=10000,
        annual_return=12,
        years=10,
    )

    print()
    print("SIP")
    print("Monthly investment:", sip.monthly_investment)
    print("Annual return:", sip.annual_return)
    print("Years:", sip.years)
    print("Total invested:", sip.total_invested)
    print("Estimated value:", sip.estimated_value)
    print("Estimated profit:", sip.estimated_profit)

    # ---------------------------------------------------------
    # Compound interest
    # ---------------------------------------------------------

    ci = engine.calculate_compound_interest(
        principal=100000,
        annual_rate=8,
        years=5,
        compounding_frequency=12,
    )

    print()
    print("COMPOUND INTEREST")
    print("Principal:", ci.principal)
    print("Annual rate:", ci.annual_rate)
    print("Years:", ci.years)
    print("Final amount:", ci.final_amount)
    print("Total interest:", ci.total_interest)

    # ---------------------------------------------------------
    # Portfolio
    # ---------------------------------------------------------

    portfolio = [
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

    summary = engine.portfolio_summary(
        portfolio
    )

    risk = engine.portfolio_risk_proxy(
        portfolio
    )

    print()
    print("PORTFOLIO")
    print("Summary:", summary)

    print()
    print("PORTFOLIO RISK PROXY")
    print("Risk:", risk)

    print()
    print("FINANCE ENGINE TEST COMPLETED")
