import re
from typing import Dict


class FinancialResponseVerifier:

    @staticmethod
    def _contains_numeric_value(
        response: str,
        value: float,
    ) -> bool:
        """
        Check for a numeric value independent of locale-specific
        thousands separators (for example 2,082,775.76 vs 20,82,775.76).
        """
        expected = round(float(value), 2)

        number_tokens = re.findall(
            r"(?<![\d.,])\d[\d,]*(?:\.\d+)?(?![\d,])",
            response,
        )

        for token in number_tokens:
            try:
                mentioned = float(token.replace(",", ""))
            except ValueError:
                continue

            if abs(mentioned - expected) < 0.01:
                return True

        return False

    def verify_emi(
        self,
        response: str,
        verified_result: Dict,
    ) -> Dict:

        response = str(response)

        required_values = {
            "monthly_emi": verified_result["monthly_emi"],
            "total_payment": verified_result["total_payment"],
            "total_interest": verified_result["total_interest"],
        }

        missing_values = []

        for field, value in required_values.items():

            formatted = f"{float(value):,.2f}"

            if not self._contains_numeric_value(
                response=response,
                value=value,
            ):
                missing_values.append({
                    "field": field,
                    "value": formatted,
                })

        # Check that the response actually distinguishes
        # total payment from total interest.
        semantic_errors = []

        total_payment = verified_result["total_payment"]
        total_interest = verified_result["total_interest"]

        payment_text_patterns = [
            r"total\s+(?:cost|payment|repayment)[^₹]{0,80}"
            r"₹\s*([\d,]+(?:\.\d+)?)",
        ]

        for pattern in payment_text_patterns:

            match = re.search(
                pattern,
                response,
                flags=re.IGNORECASE
            )

            if not match:
                continue

            try:
                mentioned = float(
                    match.group(1).replace(",", "")
                )
            except ValueError:
                continue

            if abs(mentioned - total_interest) < 0.01:

                semantic_errors.append(
                    "Total payment/cost was incorrectly "
                    "equated with total interest."
                )

        passed = (
            len(missing_values) == 0
            and len(semantic_errors) == 0
        )

        return {
            "passed": passed,
            "missing_values": missing_values,
            "semantic_errors": semantic_errors,
        }


if __name__ == "__main__":

    verifier = FinancialResponseVerifier()

    verified = {
        "principal": 1_000_000,
        "annual_rate": 8.5,
        "tenure_months": 240,
        "monthly_emi": 8678.23,
        "total_payment": 2082775.76,
        "total_interest": 1082775.76,
    }

    bad_response = (
        "Estimated monthly payments of ₹8,678.23 on a ₹10 lakh loan "
        "with an annual interest rate of 8.5%. This is based on a "
        "tenure of 240 months (20 years). The total cost of the loan "
        "will be ₹1,082,775.76 after 20 years."
    )

    result = verifier.verify_emi(
        bad_response,
        verified,
    )

    print("=" * 80)
    print("FinAI RESPONSE VERIFIER TEST")
    print("=" * 80)
    print("PASSED:", result["passed"])
    print("MISSING VALUES:", result["missing_values"])
    print("SEMANTIC ERRORS:", result["semantic_errors"])
