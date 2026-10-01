from xai.claims import (
    Claim,
    ClaimSet,
    ClaimType,
    VerificationStatus,
    build_finance_claims,
    build_model_claim,
    build_tool_claims,
)


def test_finance_claims_are_calculated_and_verified():

    claims = build_finance_claims(
        result={
            "monthly_emi": 8678.23,
            "total_payment": 2082775.76,
            "total_interest": 1082775.76,
        },
        source="deterministic_finance_engine",
        operation="EMI_CALCULATION",
    )

    assert len(claims.claims) == 3

    for claim in claims.claims:

        assert (
            claim.claim_type
            == ClaimType.CALCULATED
        )

        assert (
            claim.authority_source
            == "deterministic_finance_engine"
        )

        assert (
            claim.verification_status
            == VerificationStatus.VERIFIED
        )


def test_tool_claims_use_tool_authority():

    claims = build_tool_claims(
        result={
            "balance": 58240.75,
            "currency": "INR",
        },
        tool_name="get_account_balance",
        success=True,
    )

    assert len(claims.claims) == 2

    assert all(
        claim.claim_type
        == ClaimType.TOOL_VERIFIED
        for claim in claims.claims
    )

    assert all(
        claim.authority_source
        == "tool:get_account_balance"
        for claim in claims.claims
    )


def test_failed_tool_claims_are_rejected():

    claims = build_tool_claims(
        result={
            "balance": 58240.75,
        },
        tool_name="get_account_balance",
        success=False,
    )

    assert all(
        claim.verification_status
        == VerificationStatus.REJECTED
        for claim in claims.claims
    )


def test_model_claim_is_not_authoritative():

    claim = build_model_claim(
        field="balance",
        value=60000,
    )

    assert (
        claim.claim_type
        == ClaimType.MODEL_INFERRED
    )

    assert (
        claim.authority_source
        == "llm"
    )

    assert (
        claim.verification_status
        == VerificationStatus.PENDING
    )


def test_claimset_all_verified():

    claim = Claim(
        field="monthly_emi",
        value=8678.23,
        claim_type=ClaimType.CALCULATED,
        authority_source=(
            "deterministic_finance_engine"
        ),
        verification_status=(
            VerificationStatus.VERIFIED
        ),
    )

    claims = ClaimSet([claim])

    assert claims.all_verified()


def test_claimset_detects_unverified_claim():

    claim = build_model_claim(
        field="balance",
        value=60000,
    )

    claims = ClaimSet([claim])

    assert not claims.all_verified()


def test_authoritative_claims_exclude_model_inference():

    calculated = Claim(
        field="emi",
        value=8678.23,
        claim_type=ClaimType.CALCULATED,
        authority_source=(
            "deterministic_finance_engine"
        ),
        verification_status=(
            VerificationStatus.VERIFIED
        ),
    )

    inferred = build_model_claim(
        field="extra_claim",
        value="unknown",
    )

    claims = ClaimSet([
        calculated,
        inferred,
    ])

    authoritative = (
        claims.authoritative_claims()
    )

    assert len(authoritative) == 1
    assert (
        authoritative[0].field
        == "emi"
    )


def test_claimset_serializes_to_json_safe_dict():

    claims = build_finance_claims(
        result={
            "monthly_emi": 8678.23,
        },
        source="deterministic_finance_engine",
        operation="EMI_CALCULATION",
    )

    data = claims.to_dict()

    assert isinstance(data, list)
    assert data[0]["field"] == "monthly_emi"
    assert (
        data[0]["claim_type"]
        == "CALCULATED"
    )
    assert (
        data[0]["verification_status"]
        == "VERIFIED"
    )


def test_claimset_rejects_invalid_claim_objects():

    claims = ClaimSet()

    try:
        claims.add("not-a-claim")
    except TypeError:
        return

    raise AssertionError(
        "ClaimSet accepted a non-Claim object."
    )

def test_empty_claimset_is_not_verified():

    claims = ClaimSet()

    assert not claims.all_verified()
