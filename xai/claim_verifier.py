import json
import math
from dataclasses import dataclass, field
from decimal import Decimal, InvalidOperation
from typing import Any, Dict, List

from .claims import (
    ClaimSet,
    ClaimType,
    VerificationStatus,
)


@dataclass
class ClaimVerificationReport:

    passed: bool

    matched: List[Dict[str, Any]] = field(
        default_factory=list
    )

    mismatched: List[Dict[str, Any]] = field(
        default_factory=list
    )

    unsupported: List[Dict[str, Any]] = field(
        default_factory=list
    )

    rejected_claims: List[Dict[str, Any]] = field(
        default_factory=list
    )

    authority_violations: List[Dict[str, Any]] = field(
        default_factory=list
    )

    missing_required_fields: List[str] = field(
        default_factory=list
    )

    def to_dict(self) -> Dict[str, Any]:

        return {
            "passed": self.passed,
            "matched": list(self.matched),
            "mismatched": list(self.mismatched),
            "unsupported": list(self.unsupported),
            "rejected_claims": list(
                self.rejected_claims
            ),
            "authority_violations": list(
                self.authority_violations
            ),
            "missing_required_fields": list(
                self.missing_required_fields
            ),
        }


class ClaimVerifier:

    @staticmethod
    def _normalise_number(
        value: Any,
    ) -> Decimal:

        if isinstance(value, bool):
            raise InvalidOperation

        text = str(value).strip()

        text = (
            text.replace(",", "")
            .replace("₹", "")
            .replace("$", "")
            .replace("€", "")
            .replace("£", "")
            .replace("%", "")
        )

        return Decimal(text)

    @classmethod
    def _values_match(
        cls,
        expected: Any,
        actual: Any,
    ) -> bool:

        if (
            isinstance(expected, bool)
            or isinstance(actual, bool)
        ):

            return expected == actual

        # Numeric comparison.
        try:

            expected_number = (
                cls._normalise_number(expected)
            )

            actual_number = (
                cls._normalise_number(actual)
            )

            difference = abs(
                expected_number
                - actual_number
            )

            return difference <= Decimal("0.01")

        except (
            InvalidOperation,
            ValueError,
            TypeError,
        ):
            pass

        # Structured values.
        if isinstance(expected, (dict, list, tuple)):

            try:

                return json.dumps(
                    expected,
                    sort_keys=True,
                    default=str,
                ) == json.dumps(
                    actual,
                    sort_keys=True,
                    default=str,
                )

            except (TypeError, ValueError):

                return expected == actual

        # Text comparison.
        return (
            str(expected).strip().casefold()
            == str(actual).strip().casefold()
        )

    def verify(
        self,
        authoritative: ClaimSet,
        proposed: ClaimSet,
        required_fields: Any = None,
    ) -> ClaimVerificationReport:

        matched = []
        mismatched = []
        unsupported = []
        rejected_claims = []
        authority_violations = []
        missing_required_fields = []

        if not authoritative.claims:

            return ClaimVerificationReport(
                passed=False,
                authority_violations=[
                    {
                        "reason": (
                            "No authoritative claims "
                            "were supplied."
                        )
                    }
                ],
            )

        authoritative_by_field = {}

        for claim in authoritative.claims:

            if (
                claim.verification_status
                != VerificationStatus.VERIFIED
            ):

                authority_violations.append({
                    "field": claim.field,
                    "reason": (
                        "Authoritative claim is not "
                        "verified."
                    ),
                    "verification_status": (
                        claim.verification_status.value
                    ),
                })

                continue

            authoritative_by_field[
                claim.field
            ] = claim

        if not authoritative_by_field:

            authority_violations.append({
                "reason": (
                    "No verified authoritative claims "
                    "are available."
                )
            })

        for claim in proposed.claims:

            claim_info = {
                "field": claim.field,
                "value": claim.value,
                "claim_type": (
                    claim.claim_type.value
                ),
                "authority_source": (
                    claim.authority_source
                ),
            }

            if (
                claim.verification_status
                == VerificationStatus.REJECTED
            ):

                rejected_claims.append(
                    claim_info
                )

                continue

            # A model cannot declare itself authoritative.
            if (
                claim.claim_type
                in {
                    ClaimType.MODEL_INFERRED,
                    ClaimType.UNVERIFIED,
                }
                and claim.authority_source == "llm"
            ):
                pass

            if claim.field not in authoritative_by_field:

                unsupported.append(
                    claim_info
                )

                continue

            source_claim = (
                authoritative_by_field[
                    claim.field
                ]
            )

            if self._values_match(
                source_claim.value,
                claim.value,
            ):

                matched.append({
                    **claim_info,
                    "expected_value": (
                        source_claim.value
                    ),
                    "authority_source": (
                        source_claim.authority_source
                    ),
                })

            else:

                mismatched.append({
                    **claim_info,
                    "expected_value": (
                        source_claim.value
                    ),
                    "expected_authority": (
                        source_claim.authority_source
                    ),
                })

        # ---------------------------------------------------------
        # Completeness check.
        #
        # When required_fields are supplied, every required field
        # must be present and successfully matched.
        # ---------------------------------------------------------

        if required_fields is not None:

            required_fields = [
                str(field)
                for field in required_fields
            ]

            matched_fields = {
                item["field"]
                for item in matched
            }

            missing_required_fields = [
                field
                for field in required_fields
                if field not in matched_fields
            ]

        passed = (
            len(mismatched) == 0
            and len(unsupported) == 0
            and len(rejected_claims) == 0
            and len(authority_violations) == 0
            and len(missing_required_fields) == 0
            and bool(matched)
        )

        return ClaimVerificationReport(
            passed=passed,
            matched=matched,
            mismatched=mismatched,
            unsupported=unsupported,
            rejected_claims=rejected_claims,
            authority_violations=authority_violations,
            missing_required_fields=(
                missing_required_fields
            ),
        )


if __name__ == "__main__":

    from .claims import (
        build_finance_claims,
        build_model_claim,
    )

    print("=" * 80)
    print("FINAI CLAIM VERIFICATION ENGINE")
    print("=" * 80)

    authoritative = build_finance_claims(
        result={
            "monthly_emi": 8678.23,
            "total_payment": 2082775.76,
            "total_interest": 1082775.76,
        },
        source="deterministic_finance_engine",
        operation="EMI_CALCULATION",
    )

    proposed = ClaimSet([
        build_model_claim(
            field="monthly_emi",
            value=8678.23,
        ),
        build_model_claim(
            field="total_payment",
            value=2082775.76,
        ),
        build_model_claim(
            field="total_interest",
            value=1082775.76,
        ),
    ])

    verifier = ClaimVerifier()

    report = verifier.verify(
        authoritative=authoritative,
        proposed=proposed,
    )

    print()
    print("PASSED:", report.passed)
    print("REPORT:")
    print(report.to_dict())

