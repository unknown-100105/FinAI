from finance_engine.engine import FinanceEngine
from finance_engine.parsing.parameters import (
    FinancialParameterParser,
    FinancialParameterValidator,
)


class EMIService:

    def __init__(self):
        self.finance = FinanceEngine()
        self.parser = FinancialParameterParser()
        self.validator = FinancialParameterValidator()

    def process(self, user_text: str):

        params = self.parser.parse_emi(user_text)

        validation = self.validator.validate_emi(
            params
        )

        if not validation["valid"]:

            return {
                "status": "MISSING_PARAMETERS"
                if validation["missing"]
                else "INVALID_PARAMETERS",
                "parameters": params,
                "missing": validation["missing"],
                "message": validation["message"],
                "result": None,
            }

        emi = self.finance.calculate_emi(
            principal=params["principal"],
            annual_rate=params["annual_rate"],
            tenure_months=params["tenure_months"],
        )

        result = {
            "principal": emi.principal,
            "annual_rate": emi.annual_rate,
            "tenure_months": emi.tenure_months,
            "monthly_emi": emi.monthly_emi,
            "total_payment": emi.total_payment,
            "total_interest": emi.total_interest,
        }

        return {
            "status": "CALCULATED",
            "parameters": params,
            "missing": [],
            "message": "EMI calculated successfully.",
            "result": result,
        }


if __name__ == "__main__":

    service = EMIService()

    tests = [
        "Calculate EMI for ₹10 lakh at 8.5% for 20 years",
        "EMI for 500000 at 9% for 60 months",
        "Calculate my EMI",
    ]

    print("=" * 80)
    print("FinAI EMI SERVICE TEST")
    print("=" * 80)

    for text in tests:

        print()
        print("USER:", text)

        output = service.process(text)

        print("STATUS:", output["status"])
        print("PARAMETERS:", output["parameters"])
        print("MISSING:", output["missing"])
        print("MESSAGE:", output["message"])

        if output["result"]:
            print("RESULT:", output["result"])
