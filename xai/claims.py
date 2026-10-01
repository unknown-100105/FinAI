from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class ClaimType(str, Enum):
    CALCULATED = "CALCULATED"
    TOOL_VERIFIED = "TOOL_VERIFIED"
    RETRIEVED = "RETRIEVED"
    USER_PROVIDED = "USER_PROVIDED"
    MODEL_INFERRED = "MODEL_INFERRED"
    UNVERIFIED = "UNVERIFIED"


class VerificationStatus(str, Enum):
    VERIFIED = "VERIFIED"
    PENDING = "PENDING"
    REJECTED = "REJECTED"
    NOT_APPLICABLE = "NOT_APPLICABLE"


@dataclass(frozen=True)
class Claim:
    field: str
    value: Any

    claim_type: ClaimType
    authority_source: str

    verification_status: VerificationStatus

    evidence_ref: Optional[str] = None
    metadata: Dict[str, Any] = field(
        default_factory=dict
    )


class ClaimSet:

    def __init__(self, claims: Optional[List[Claim]] = None):

        self.claims: List[Claim] = list(
            claims or []
        )

    def add(self, claim: Claim) -> None:

        if not isinstance(claim, Claim):
            raise TypeError(
                "ClaimSet accepts Claim objects only."
            )

        self.claims.append(claim)

    def all_verified(self) -> bool:

        # An empty claim set is not considered verified.
        return (
            bool(self.claims)
            and all(
                claim.verification_status
                == VerificationStatus.VERIFIED
                for claim in self.claims
            )
        )

    def authoritative_claims(self) -> List[Claim]:

        return [
            claim
            for claim in self.claims
            if claim.claim_type
            != ClaimType.MODEL_INFERRED
            and claim.claim_type
            != ClaimType.UNVERIFIED
        ]

    def to_dict(self) -> List[Dict[str, Any]]:

        return [
            {
                "field": claim.field,
                "value": claim.value,
                "claim_type": claim.claim_type.value,
                "authority_source": (
                    claim.authority_source
                ),
                "verification_status": (
                    claim.verification_status.value
                ),
                "evidence_ref": claim.evidence_ref,
                "metadata": dict(claim.metadata),
            }
            for claim in self.claims
        ]


def build_finance_claims(
    result: Dict[str, Any],
    source: str,
    operation: str,
) -> ClaimSet:

    if not isinstance(result, dict):
        raise TypeError(
            "Finance result must be a dictionary."
        )

    claims = ClaimSet()

    for field_name, value in result.items():

        if value is None:
            continue

        claims.add(
            Claim(
                field=field_name,
                value=value,
                claim_type=ClaimType.CALCULATED,
                authority_source=source,
                verification_status=(
                    VerificationStatus.VERIFIED
                ),
                metadata={
                    "operation": operation,
                    "domain": "finance",
                },
            )
        )

    return claims


def build_tool_claims(
    result: Dict[str, Any],
    tool_name: str,
    success: bool,
) -> ClaimSet:

    if not isinstance(result, dict):
        raise TypeError(
            "Tool result must be a dictionary."
        )

    status = (
        VerificationStatus.VERIFIED
        if success
        else VerificationStatus.REJECTED
    )

    claims = ClaimSet()

    for field_name, value in result.items():

        claims.add(
            Claim(
                field=field_name,
                value=value,
                claim_type=ClaimType.TOOL_VERIFIED,
                authority_source=(
                    f"tool:{tool_name}"
                ),
                verification_status=status,
                metadata={
                    "tool": tool_name,
                },
            )
        )

    return claims


def build_model_claim(
    field: str,
    value: Any,
    authority_source: str = "llm",
) -> Claim:

    return Claim(
        field=field,
        value=value,
        claim_type=ClaimType.MODEL_INFERRED,
        authority_source=authority_source,
        verification_status=(
            VerificationStatus.PENDING
        ),
    )


if __name__ == "__main__":

    print("=" * 80)
    print("FINAI UNIFIED CLAIM / RESULT CONTRACT")
    print("=" * 80)

    finance_claims = build_finance_claims(
        result={
            "monthly_emi": 8678.23,
            "total_payment": 2082775.76,
            "total_interest": 1082775.76,
        },
        source="deterministic_finance_engine",
        operation="EMI_CALCULATION",
    )

    print()
    print("FINANCE CLAIMS:")
    print(finance_claims.to_dict())

    tool_claims = build_tool_claims(
        result={
            "account_id": "ACC1001",
            "balance": 58240.75,
            "currency": "INR",
        },
        tool_name="get_account_balance",
        success=True,
    )

    print()
    print("TOOL CLAIMS:")
    print(tool_claims.to_dict())

    model_claim = build_model_claim(
        field="balance",
        value=60000,
    )

    print()
    print("MODEL CLAIM:")
    print(
        ClaimSet([model_claim]).to_dict()
    )

