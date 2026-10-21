from finance_engine.engine import FinanceEngine


class SIPService:

    def __init__(self):
        self.finance = FinanceEngine()

    def process(
        self,
        monthly_investment,
        annual_return,
        years,
    ):

        try:

            result = self.finance.calculate_sip(
                monthly_investment=monthly_investment,
                annual_return=annual_return,
                years=years,
            )

            return {
                "status": "CALCULATED",
                "parameters": {
                    "monthly_investment": monthly_investment,
                    "annual_return": annual_return,
                    "years": years,
                },
                "message": (
                    "SIP projection assumes monthly contributions at period end "
                    "and a constant annualized return. Actual returns vary and "
                    "are not guaranteed."
                ),
                "assumptions": [
                    "Contributions are made monthly at period end.",
                    "The annualized return is held constant for illustration.",
                    "Market volatility, taxes, fees, and contribution changes are excluded.",
                    "Projected returns are not guaranteed.",
                ],
                "result": {
                    "monthly_investment": result.monthly_investment,
                    "annual_return": result.annual_return,
                    "years": result.years,
                    "total_invested": result.total_invested,
                    "estimated_value": result.estimated_value,
                    "estimated_profit": result.estimated_profit,
                },
            }

        except ValueError as exc:

            return {
                "status": "INVALID_PARAMETERS",
                "parameters": {
                    "monthly_investment": monthly_investment,
                    "annual_return": annual_return,
                    "years": years,
                },
                "message": str(exc),
                "result": None,
            }


if __name__ == "__main__":

    service = SIPService()

    result = service.process(
        monthly_investment=10000,
        annual_return=12,
        years=10,
    )

    print("=" * 80)
    print("FinAI SIP SERVICE TEST")
    print("=" * 80)
    print("STATUS:", result["status"])
    print("PARAMETERS:", result["parameters"])
    print("RESULT:", result["result"])
    print("MESSAGE:", result["message"])
