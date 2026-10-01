import re
from typing import Any, Dict, Iterable, Optional

from .claims import (
    Claim,
    ClaimSet,
    ClaimType,
    VerificationStatus,
)


class FinancialClaimExtractor:

    FIELD_ALIASES = {
        "monthly_emi": (
            "monthly emi",
            "emi",
            "monthly payment",
            "monthly installment",
        ),
        "total_payment": (
            "total payment",
            "total repayment",
            "total cost",
        ),
        "total_interest": (
            "total interest",
            "interest paid",
            "interest component",
        ),
        "principal": (
            "loan amount",
            "principal",
            "principal amount",
        ),
        "annual_rate": (
            "interest rate",
            "annual interest rate",
            "rate",
        ),
        "tenure_months": (
            "tenure",
            "loan tenure",
            "term",
        ),
    }

    @staticmethod
    def _parse_number(value: str) -> Optional[float]:

        try:
            cleaned = (
                value
                .replace(",", "")
                .replace("₹", "")
                .replace("$", "")
                .replace("€", "")
                .replace("£", "")
                .strip()
            )

            return float(cleaned)

        except (TypeError, ValueError):
            return None

    @classmethod
    def _patterns_for_field(
        cls,
        field: str,
    ) -> Iterable[str]:

        aliases = cls.FIELD_ALIASES.get(
            field,
            (),
        )

        for alias in aliases:

            escaped = re.escape(alias)

            # Exact forward form:
            # "Total interest is ₹1,082,775.76"
            # "Total payment: ₹2,082,775.76"
            yield (
                rf"{escaped}\b"
                rf"[ \t]*(?:is|was|are|:|=)"
                rf"[ \t]*(?:₹|Rs\.?|INR|USD|\$)?"
                rf"[ \t]*([\d,]+(?:\.\d+)?)"
            )

            # Descriptive forward form, kept within the same
            # sentence/clause:
            # "EMI for a loan of ₹10 lakh ... is ₹8,678.23"
            # "Total payment over the tenure: ₹2,082,775.76"
            #
            # The character class deliberately excludes newline and
            # sentence/field delimiters so another claim cannot be
            # captured accidentally.
            yield (
                rf"{escaped}\b"
                rf"[ \t]+"
                rf"(?:[^\r\n!?:]|\.(?=\d)){{0,200}}?"
                rf"[ \t]*(?:is|was|are|:)"
                rf"[ \t]*(?:₹|Rs\.?|INR|USD|\$)?"
                rf"[ \t]*([\d,]+(?:\.\d+)?)"
            )

            # Compact form:
            # "EMI ₹8,678.23"
            yield (
                rf"{escaped}\b"
                rf"[ \t]+"
                rf"(?:₹|Rs\.?|INR|USD|\$)?"
                rf"[ \t]*([\d,]+(?:\.\d+)?)"
            )

            # Reverse/natural-language form:
            # "₹1,082,775.76 in total interest"
            # "₹1,082,775.76 total interest"
            #
            # [ \t] is intentional: never cross a newline.
            yield (
                rf"(?:₹|Rs\.?|INR|USD|\$)?"
                rf"[ \t]*([\d,]+(?:\.\d+)?)"
                rf"[ \t]+(?:in[ \t]+)?"
                rf"{escaped}\b"
            )

    @classmethod
    def extract(
        cls,
        response: str,
        expected_fields: Iterable[str],
    ) -> ClaimSet:

        response = str(response)

        claims = ClaimSet()

        for field in expected_fields:

            found_value = None

            for pattern in cls._patterns_for_field(field):

                match = re.search(
                    pattern,
                    response,
                    flags=re.IGNORECASE,
                )

                if not match:
                    continue

                parsed = cls._parse_number(
                    match.group(1)
                )

                if parsed is not None:
                    found_value = parsed
                    break

            if found_value is None:
                continue

            claims.add(
                Claim(
                    field=field,
                    value=found_value,
                    claim_type=ClaimType.MODEL_INFERRED,
                    authority_source="llm",
                    verification_status=(
                        VerificationStatus.PENDING
                    ),
                )
            )

        return claims


if __name__ == "__main__":

    response = (
        "Your monthly EMI is ₹8,678.23. "
        "Total payment is ₹2,082,775.76. "
        "Total interest is ₹1,082,775.76."
    )

    claims = FinancialClaimExtractor.extract(
        response=response,
        expected_fields=[
            "monthly_emi",
            "total_payment",
            "total_interest",
        ],
    )

    print("=" * 80)
    print("FINAI FINANCIAL CLAIM EXTRACTOR")
    print("=" * 80)
    print("EXTRACTED CLAIMS:")
    print(claims.to_dict())




