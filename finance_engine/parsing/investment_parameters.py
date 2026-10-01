import re
from typing import Dict, Optional


class SIPParameterParser:

    @staticmethod
    def parse(text: str) -> Dict[str, Optional[float]]:

        text = str(text).lower()

        monthly_investment = None
        annual_return = None
        years = None

        # ---------------------------------------------------------
        # Monthly investment
        # Examples:
        # ₹10,000/month
        # 10000 monthly
        # 10k per month
        # ---------------------------------------------------------

        amount_patterns = [
            r'(?:₹|rs\.?|inr)?\s*([\d,]+(?:\.\d+)?)\s*'
            r'(lakh|lac|crore|cr|k|thousand|million)?'
            r'\s*(?:per\s*month|/month|monthly)',
            r'(?:monthly\s*(?:investment|sip))\s*(?:of)?\s*'
            r'(?:₹|rs\.?|inr)?\s*([\d,]+(?:\.\d+)?)\s*'
            r'(lakh|lac|crore|cr|k|thousand|million)?',
        ]

        for pattern in amount_patterns:

            match = re.search(pattern, text)

            if not match:
                continue

            raw = match.group(1).replace(",", "")
            unit = match.group(2)

            try:
                monthly_investment = float(raw)
            except ValueError:
                continue

            monthly_investment = SIPParameterParser._apply_unit(
                monthly_investment,
                unit
            )

            break

        # ---------------------------------------------------------
        # Annual expected return
        # ---------------------------------------------------------

        rate_match = re.search(
            r'(\d+(?:\.\d+)?)\s*%'
            r'|(?:return|returns|growth|rate)\s*(?:of|is)?\s*'
            r'(\d+(?:\.\d+)?)',
            text
        )

        if rate_match:

            value = (
                rate_match.group(1)
                or rate_match.group(2)
            )

            if value:
                annual_return = float(value)

        # ---------------------------------------------------------
        # Years
        # ---------------------------------------------------------

        years_match = re.search(
            r'(\d+(?:\.\d+)?)\s*(?:years?|yrs?)',
            text
        )

        if years_match:
            years = float(
                years_match.group(1)
            )

        return {
            "monthly_investment": monthly_investment,
            "annual_return": annual_return,
            "years": int(years) if years is not None else None,
        }

    @staticmethod
    def _apply_unit(value, unit):

        if unit in {"lakh", "lac"}:
            return value * 100_000

        if unit in {"crore", "cr"}:
            return value * 10_000_000

        if unit in {"k", "thousand"}:
            return value * 1_000

        if unit == "million":
            return value * 1_000_000

        return value


class SIPParameterValidator:

    @staticmethod
    def validate(params):

        missing = []

        if params.get("monthly_investment") is None:
            missing.append("monthly investment")

        if params.get("annual_return") is None:
            missing.append("expected annual return")

        if params.get("years") is None:
            missing.append("investment period")

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

        if params["monthly_investment"] <= 0:
            return {
                "valid": False,
                "missing": [],
                "message": (
                    "Monthly investment must be greater than zero."
                ),
            }

        if params["annual_return"] < 0:
            return {
                "valid": False,
                "missing": [],
                "message": (
                    "Expected annual return cannot be negative."
                ),
            }

        if params["years"] <= 0:
            return {
                "valid": False,
                "missing": [],
                "message": (
                    "Investment period must be greater than zero."
                ),
            }

        return {
            "valid": True,
            "missing": [],
            "message": "All SIP parameters are valid.",
        }


class InterestParameterParser:

    @staticmethod
    def parse(text: str) -> Dict[str, Optional[float]]:

        text = str(text).lower()

        principal = None
        annual_rate = None
        years = None
        compounding_frequency = 12

        # ---------------------------------------------------------
        # Principal
        # ---------------------------------------------------------

        amount_match = re.search(
            r'(?:₹|rs\.?|inr)?\s*'
            r'([\d,]+(?:\.\d+)?)\s*'
            r'(crore|cr|lakh|lac|k|thousand|million)?'
            r'(?:\s*(?:principal|investment|amount))?',
            text
        )

        if amount_match:

            raw = amount_match.group(1).replace(",", "")
            unit = amount_match.group(2)

            try:
                principal = float(raw)
                principal = SIPParameterParser._apply_unit(
                    principal,
                    unit
                )
            except ValueError:
                principal = None

        # ---------------------------------------------------------
        # Annual interest rate
        # ---------------------------------------------------------

        rate_match = re.search(
            r'(\d+(?:\.\d+)?)\s*%'
            r'|(?:interest(?:\s+rate)?|rate)\s*(?:of|is|at)?\s*'
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
        # Years
        # ---------------------------------------------------------

        years_match = re.search(
            r'(\d+(?:\.\d+)?)\s*(?:years?|yrs?)',
            text
        )

        if years_match:
            years = float(
                years_match.group(1)
            )

        # ---------------------------------------------------------
        # Compounding frequency
        # ---------------------------------------------------------

        if re.search(
            r'(?:monthly|per\s+month|monthly\s+compounding)',
            text
        ):
            compounding_frequency = 12

        elif re.search(
            r'(?:quarterly|per\s+quarter|quarterly\s+compounding)',
            text
        ):
            compounding_frequency = 4

        elif re.search(
            r'(?:half[-\s]?yearly|semi[-\s]?annual|semiannual)',
            text
        ):
            compounding_frequency = 2

        elif re.search(
            r'(?:yearly|annual|annually|yearly\s+compounding)',
            text
        ):
            compounding_frequency = 1

        return {
            "principal": principal,
            "annual_rate": annual_rate,
            "years": int(years) if years is not None else None,
            "compounding_frequency": compounding_frequency,
        }


class InterestParameterValidator:

    @staticmethod
    def validate(params):

        missing = []

        if params.get("principal") is None:
            missing.append("principal amount")

        if params.get("annual_rate") is None:
            missing.append("annual interest rate")

        if params.get("years") is None:
            missing.append("investment period")

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
                "message": (
                    "Principal amount must be greater than zero."
                ),
            }

        if params["annual_rate"] < 0:
            return {
                "valid": False,
                "missing": [],
                "message": (
                    "Interest rate cannot be negative."
                ),
            }

        if params["years"] <= 0:
            return {
                "valid": False,
                "missing": [],
                "message": (
                    "Investment period must be greater than zero."
                ),
            }

        if params["compounding_frequency"] <= 0:
            return {
                "valid": False,
                "missing": [],
                "message": (
                    "Compounding frequency must be greater than zero."
                ),
            }

        return {
            "valid": True,
            "missing": [],
            "message": "All interest parameters are valid.",
        }


if __name__ == "__main__":

    sip_parser = SIPParameterParser()
    sip_validator = SIPParameterValidator()

    interest_parser = InterestParameterParser()
    interest_validator = InterestParameterValidator()

    print("=" * 80)
    print("FinAI SIP + INTEREST PARAMETER PARSER TEST")
    print("=" * 80)

    sip_tests = [
        "Invest ₹10,000 per month for 10 years at 12% return",
        "SIP of 10k monthly for 15 years at 10%",
        "Calculate my SIP",
    ]

    print()
    print("SIP TESTS")

    for text in sip_tests:

        params = sip_parser.parse(text)
        validation = sip_validator.validate(params)

        print()
        print("USER:", text)
        print("PARAMETERS:", params)
        print("VALID:", validation["valid"])
        print("MESSAGE:", validation["message"])

    interest_tests = [
        "Calculate compound interest on ₹1 lakh at 8% for 5 years monthly",
        "₹500000 at 7.5% for 10 years quarterly compounding",
        "Calculate compound interest",
    ]

    print()
    print("INTEREST TESTS")

    for text in interest_tests:

        params = interest_parser.parse(text)
        validation = interest_validator.validate(params)

        print()
        print("USER:", text)
        print("PARAMETERS:", params)
        print("VALID:", validation["valid"])
        print("MESSAGE:", validation["message"])
