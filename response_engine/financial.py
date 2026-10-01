from typing import Any, Dict, Optional


class FinancialResponseEngine:

    def generate(
        self,
        intent: str,
        result: Optional[Dict[str, Any]] = None,
        status: str = "UNKNOWN",
        persona: str = "neutral",
    ) -> str:

        if status == "MISSING_PARAMETERS":
            missing = []

            if result:
                missing = result.get("missing", [])

            if missing:
                return (
                    "I can calculate this for you. "
                    "Please provide: "
                    + ", ".join(missing)
                    + "."
                )

            return "I need a few more details to calculate this."

        if status == "INVALID_PARAMETERS":
            if result and result.get("message"):
                return str(result["message"])

            return "The provided financial parameters are invalid."

        if status != "CALCULATED":
            return (
                "I could not complete the requested financial calculation."
            )

        calculation = (
            result.get("result", {})
            if result
            else {}
        )

        if intent == "EMI_QUERY":
            return self._emi_response(
                calculation,
                persona
            )

        if intent == "SIP_QUERY":
            return self._sip_response(
                calculation,
                persona
            )

        if intent == "INTEREST_QUERY":
            return self._interest_response(
                calculation,
                persona
            )

        return (
            "The calculation was completed successfully."
        )

    @staticmethod
    def _emi_response(
        data: Dict[str, Any],
        persona: str,
    ):

        principal = data.get("principal")
        rate = data.get("annual_rate")
        tenure = data.get("tenure_months")
        emi = data.get("monthly_emi")
        total = data.get("total_payment")
        interest = data.get("total_interest")

        if persona == "hype":
            opening = (
                "Here is your EMI breakdown. "
            )
        elif persona == "stern":
            opening = (
                "EMI calculation completed from the supplied parameters. "
            )
        else:
            opening = "Here is your EMI calculation. "

        return (
            f"{opening}"
            f"Loan amount: ₹{principal:,.2f}. "
            f"Annual interest rate: {rate:.2f}%. "
            f"Tenure: {tenure} months. "
            f"Monthly EMI: ₹{emi:,.2f}. "
            f"Total payment: ₹{total:,.2f}. "
            f"Total interest: ₹{interest:,.2f}."
        )

    @staticmethod
    def _sip_response(
        data: Dict[str, Any],
        persona: str,
    ):

        monthly = data.get("monthly_investment")
        annual_return = data.get("annual_return")
        years = data.get("years")
        invested = data.get("total_invested")
        value = data.get("estimated_value")
        profit = data.get("estimated_profit")

        if persona == "hype":
            opening = (
                "Here is the SIP projection based on your assumptions. "
            )
        elif persona == "stern":
            opening = (
                "SIP projection completed using the supplied assumptions. "
            )
        else:
            opening = "Here is your SIP projection. "

        return (
            f"{opening}"
            f"Monthly investment: ₹{monthly:,.2f}. "
            f"Assumed annual return: {annual_return:.2f}%. "
            f"Period: {years} years. "
            f"Total invested: ₹{invested:,.2f}. "
            f"Estimated value: ₹{value:,.2f}. "
            f"Estimated profit: ₹{profit:,.2f}."
        )

    @staticmethod
    def _interest_response(
        data: Dict[str, Any],
        persona: str,
    ):

        principal = data.get("principal")
        rate = data.get("annual_rate")
        years = data.get("years")
        frequency = data.get("compounding_frequency")
        amount = data.get("final_amount")
        interest = data.get("total_interest")

        if persona == "hype":
            opening = (
                "Here is the compound-interest projection. "
            )
        elif persona == "stern":
            opening = (
                "Compound-interest calculation completed "
                "from the supplied assumptions. "
            )
        else:
            opening = "Here is your compound-interest projection. "

        return (
            f"{opening}"
            f"Principal: ₹{principal:,.2f}. "
            f"Annual rate: {rate:.2f}%. "
            f"Period: {years} years. "
            f"Compounding frequency: {frequency} times per year. "
            f"Final amount: ₹{amount:,.2f}. "
            f"Total interest: ₹{interest:,.2f}."
        )


if __name__ == "__main__":

    engine = FinancialResponseEngine()

    emi_result = {
        "status": "CALCULATED",
        "result": {
            "principal": 1_000_000,
            "annual_rate": 8.5,
            "tenure_months": 240,
            "monthly_emi": 8678.23,
            "total_payment": 2082775.76,
            "total_interest": 1082775.76,
        }
    }

    print("=" * 80)
    print("FinAI RESPONSE ENGINE TEST")
    print("=" * 80)

    for persona in (
        "neutral",
        "hype",
        "stern",
    ):

        print()
        print("PERSONA:", persona)

        print(
            engine.generate(
                intent="EMI_QUERY",
                result=emi_result,
                status="CALCULATED",
                persona=persona,
            )
        )

    print()
    print(
        engine.generate(
            intent="EMI_QUERY",
            result={
                "status": "MISSING_PARAMETERS",
                "missing": [
                    "loan amount",
                    "annual interest rate",
                    "loan tenure",
                ],
            },
            status="MISSING_PARAMETERS",
        )
    )
