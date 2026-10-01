import re
from typing import Dict, Optional


class FinancialParameterParser:

    @staticmethod
    def parse_emi(text: str) -> Dict[str, Optional[float]]:

        text = str(text).lower()

        principal = None
        annual_rate = None
        tenure_months = None

        # ---------------------------------------------------------
        # Loan amount
        # ---------------------------------------------------------

        amount_match = re.search(
            r'(?:₹|rs\.?|inr)?\s*'
            r'([\d,]+(?:\.\d+)?)\s*'
            r'(crore|cr|lakh|lac|k|thousand|million)?',
            text
        )

        if amount_match:
            raw_number = amount_match.group(1).replace(",", "")
            unit = amount_match.group(2)

            try:
                principal = float(raw_number)
            except ValueError:
                principal = None

            if principal is not None:

                if unit in {"crore", "cr"}:
                    principal *= 10_000_000

                elif unit in {"lakh", "lac"}:
                    principal *= 100_000

                elif unit in {"k", "thousand"}:
                    principal *= 1_000

                elif unit == "million":
                    principal *= 1_000_000

        # ---------------------------------------------------------
        # Interest rate
        # ---------------------------------------------------------

        rate_match = re.search(
            r'(\d+(?:\.\d+)?)\s*%'
            r'|(?:at|rate|interest(?:\s+rate)?)\s*'
            r'(\d+(?:\.\d+)?)',
            text
        )

        if rate_match:
            value = (
                rate_match.group(1)
                or rate_match.group(2)
            )

            if value:
                annual_rate = float(value)

        # ---------------------------------------------------------
        # Tenure
        # ---------------------------------------------------------

        years_match = re.search(
            r'(\d+(?:\.\d+)?)\s*(?:years?|yrs?)',
            text
        )

        months_match = re.search(
            r'(\d+)\s*(?:months?|mos?)',
            text
        )

        if years_match:
            years = float(years_match.group(1))
            tenure_months = int(round(years * 12))

        elif months_match:
            tenure_months = int(
                months_match.group(1)
            )

        return {
            "principal": principal,
            "annual_rate": annual_rate,
            "tenure_months": tenure_months,
        }


class FinancialParameterValidator:

    @staticmethod
    def validate_emi(
        params: Dict[str, Optional[float]]
    ) -> Dict:

        missing = []

        if params.get("principal") is None:
            missing.append("loan amount")

        if params.get("annual_rate") is None:
            missing.append("annual interest rate")

        if params.get("tenure_months") is None:
            missing.append("loan tenure")

        if missing:
            return {
                "valid": False,
                "missing": missing,
                "message": (
                    "Please provide "
                    + ", ".join(missing)
                    + "."
                ),
            }

        if params["principal"] <= 0:
            return {
                "valid": False,
                "missing": [],
                "message": "Loan amount must be greater than zero.",
            }

        if params["annual_rate"] < 0:
            return {
                "valid": False,
                "missing": [],
                "message": "Interest rate cannot be negative.",
            }

        if params["tenure_months"] <= 0:
            return {
                "valid": False,
                "missing": [],
                "message": "Loan tenure must be greater than zero.",
            }

        return {
            "valid": True,
            "missing": [],
            "message": "All EMI parameters are valid.",
        }


if __name__ == "__main__":

    tests = [
        "Calculate EMI for ₹10 lakh at 8.5% for 20 years",
        "EMI for 500000 at 9% for 60 months",
        "Calculate my EMI",
        "What is EMI for Rs 12 lakh at 7.5 percent for 10 years",
    ]

    parser = FinancialParameterParser()
    validator = FinancialParameterValidator()

    print("=" * 80)
    print("FinAI FINANCIAL PARAMETER PARSER TEST")
    print("=" * 80)

    for text in tests:

        print()
        print("USER:", text)

        params = parser.parse_emi(text)
        result = validator.validate_emi(params)

        print("PARAMETERS:", params)
        print("VALID:", result["valid"])
        print("MESSAGE:", result["message"])
