from xai.claim_verifier import ClaimVerifier
from xai.claims import (
    Claim,
    ClaimSet,
    ClaimType,
    VerificationStatus,
    build_finance_claims,
    build_model_claim,
)


def finance_authority():

    return build_finance_claims(
        result={
            "monthly_emi": 8678.23,
            "total_payment": 2082775.76,
            "total_interest": 1082775.76,
        },
        source="deterministic_finance_engine",
        operation="EMI_CALCULATION",
    )


def test_matching_model_claims_pass():

    authoritative = finance_authority()

    proposed = ClaimSet([
        build_model_claim(
            "monthly_emi",
            8678.23,
        ),
        build_model_claim(
            "total_payment",
            2082775.76,
        ),
        build_model_claim(
            "total_interest",
            1082775.76,
        ),
    ])

    report = ClaimVerifier().verify(
        authoritative,
        proposed,
    )

    assert report.passed
    assert len(report.matched) == 3
    assert report.mismatched == []
    assert report.unsupported == []


def test_wrong_numeric_value_fails():

    authoritative = finance_authority()

    proposed = ClaimSet([
        build_model_claim(
            "monthly_emi",
            8678.32,
        ),
        build_model_claim(
            "total_payment",
            2082775.76,
        ),
        build_model_claim(
            "total_interest",
            1082775.76,
        ),
    ])

    report = ClaimVerifier().verify(
        authoritative,
        proposed,
    )

    assert not report.passed
    assert len(report.mismatched) == 1
    assert (
        report.mismatched[0]["field"]
        == "monthly_emi"
    )


def test_missing_authoritative_field_is_unsupported():

    authoritative = finance_authority()

    proposed = ClaimSet([
        build_model_claim(
            "monthly_emi",
            8678.23,
        ),
        build_model_claim(
            "fake_total",
            999999.99,
        ),
    ])

    report = ClaimVerifier().verify(
        authoritative,
        proposed,
    )

    assert not report.passed
    assert len(report.unsupported) == 1
    assert (
        report.unsupported[0]["field"]
        == "fake_total"
    )


def test_wrong_total_payment_is_detected():

    authoritative = finance_authority()

    proposed = ClaimSet([
        build_model_claim(
            "monthly_emi",
            8678.23,
        ),
        build_model_claim(
            "total_payment",
            1082775.76,
        ),
        build_model_claim(
            "total_interest",
            1082775.76,
        ),
    ])

    report = ClaimVerifier().verify(
        authoritative,
        proposed,
    )

    assert not report.passed

    fields = {
        item["field"]
        for item in report.mismatched
    }

    assert "total_payment" in fields


def test_string_claims_are_case_insensitive():

    authoritative = ClaimSet([
        Claim(
            field="currency",
            value="INR",
            claim_type=ClaimType.TOOL_VERIFIED,
            authority_source=(
                "tool:get_account_balance"
            ),
            verification_status=(
                VerificationStatus.VERIFIED
            ),
        )
    ])

    proposed = ClaimSet([
        build_model_claim(
            "currency",
            "inr",
        )
    ])

    report = ClaimVerifier().verify(
        authoritative,
        proposed,
    )

    assert report.passed
    assert len(report.matched) == 1


def test_numeric_formatting_differences_are_allowed():

    authoritative = ClaimSet([
        Claim(
            field="balance",
            value=58240.75,
            claim_type=ClaimType.TOOL_VERIFIED,
            authority_source=(
                "tool:get_account_balance"
            ),
            verification_status=(
                VerificationStatus.VERIFIED
            ),
        )
    ])

    proposed = ClaimSet([
        build_model_claim(
            "balance",
            "58,240.75",
        )
    ])

    report = ClaimVerifier().verify(
        authoritative,
        proposed,
    )

    assert report.passed


def test_unverified_authority_cannot_pass():

    authoritative = ClaimSet([
        Claim(
            field="balance",
            value=58240.75,
            claim_type=ClaimType.TOOL_VERIFIED,
            authority_source=(
                "tool:get_account_balance"
            ),
            verification_status=(
                VerificationStatus.PENDING
            ),
        )
    ])

    proposed = ClaimSet([
        build_model_claim(
            "balance",
            58240.75,
        )
    ])

    report = ClaimVerifier().verify(
        authoritative,
        proposed,
    )

    assert not report.passed
    assert (
        len(report.authority_violations)
        >= 1
    )


def test_empty_authority_fails():

    authoritative = ClaimSet()

    proposed = ClaimSet([
        build_model_claim(
            "balance",
            58240.75,
        )
    ])

    report = ClaimVerifier().verify(
        authoritative,
        proposed,
    )

    assert not report.passed
    assert (
        len(report.authority_violations)
        == 1
    )


def test_rejected_proposed_claim_fails():

    authoritative = finance_authority()

    proposed = ClaimSet([
        Claim(
            field="monthly_emi",
            value=8678.23,
            claim_type=ClaimType.MODEL_INFERRED,
            authority_source="llm",
            verification_status=(
                VerificationStatus.REJECTED
            ),
        )
    ])

    report = ClaimVerifier().verify(
        authoritative,
        proposed,
    )

    assert not report.passed
    assert len(report.rejected_claims) == 1


def test_report_is_dictionary_serializable():

    authoritative = finance_authority()

    proposed = ClaimSet([
        build_model_claim(
            "monthly_emi",
            8678.23,
        ),
        build_model_claim(
            "total_payment",
            2082775.76,
        ),
        build_model_claim(
            "total_interest",
            1082775.76,
        ),
    ])

    report = ClaimVerifier().verify(
        authoritative,
        proposed,
    )

    data = report.to_dict()

    assert isinstance(data, dict)
    assert data["passed"] is True
    assert len(data["matched"]) == 3

def test_missing_required_fields_fail():

    authoritative = finance_authority()

    proposed = ClaimSet([
        build_model_claim(
            "monthly_emi",
            8678.23,
        ),
    ])

    report = ClaimVerifier().verify(
        authoritative,
        proposed,
        required_fields=[
            "monthly_emi",
            "total_payment",
            "total_interest",
        ],
    )

    assert not report.passed

    assert set(
        report.missing_required_fields
    ) == {
        "total_payment",
        "total_interest",
    }


def test_all_required_fields_pass():

    authoritative = finance_authority()

    proposed = ClaimSet([
        build_model_claim(
            "monthly_emi",
            8678.23,
        ),
        build_model_claim(
            "total_payment",
            2082775.76,
        ),
        build_model_claim(
            "total_interest",
            1082775.76,
        ),
    ])

    report = ClaimVerifier().verify(
        authoritative,
        proposed,
        required_fields=[
            "monthly_emi",
            "total_payment",
            "total_interest",
        ],
    )

    assert report.passed
    assert report.missing_required_fields == []
