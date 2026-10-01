from typing import Optional

from finance_engine.engine import FinanceEngine
from finance_engine.parsing.investment_parameters import (
    InterestParameterParser,
    InterestParameterValidator,
)


class InterestService:

    def __init__(self):
        self.finance = FinanceEngine()
        self.parser = InterestParameterParser()
        self.validator = InterestParameterValidator()

    def process(
        self,
        user_text: Optional[str] = None,
        *,
        principal=None,
        annual_rate=None,
        years=None,
        compounding_frequency=12,
    ):

        structured = any(
            value is not None
            for value in (
                principal,
                annual_rate,
                years,
            )
        )

        if structured:
            params = {
                "principal": principal,
                "annual_rate": annual_rate,
                "years": years,
                "compounding_frequency": compounding_frequency,
            }
        else:
            params = self.parser.parse(
                user_text or ""
            )

        validation = self.validator.validate(params)

        if not validation["valid"]:
            return {
                "status": (
                    "MISSING_PARAMETERS"
                    if validation["missing"]
                    else "INVALID_PARAMETERS"
                ),
                "parameters": params,
                "missing": validation["missing"],
                "message": validation["message"],
                "result": None,
            }

        result = self.finance.calculate_compound_interest(
            principal=params["principal"],
            annual_rate=params["annual_rate"],
            years=params["years"],
            compounding_frequency=params["compounding_frequency"],
        )

        output = {
            "principal": result.principal,
            "annual_rate": result.annual_rate,
            "years": result.years,
            "compounding_frequency": result.compounding_frequency,
            "final_amount": result.final_amount,
            "total_interest": result.total_interest,
        }

        return {
            "status": "CALCULATED",
            "parameters": params,
            "missing": [],
            "message": (
                "Compound-interest projection "
                "calculated successfully."
            ),
            "result": output,
        }


if __name__ == "__main__":

    service = InterestService()

    tests = [
        "Calculate compound interest on ₹1 lakh at 8% for 5 years monthly",
        "₹500000 at 7.5% for 10 years quarterly compounding",
        "Calculate compound interest",
    ]

    for text in tests:
        print()
        print("USER:", text)

        result = service.process(text)

        print("STATUS:", result["status"])
        print("PARAMETERS:", result["parameters"])
        print("MISSING:", result["missing"])
        print("MESSAGE:", result["message"])

        if result["result"]:
            print("RESULT:", result["result"])
