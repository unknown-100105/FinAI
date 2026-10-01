from xai.claim_extractor import (
    FinancialClaimExtractor,
)


def test_extracts_all_emi_values():

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

    assert len(claims.claims) == 3

    values = {
        claim.field: claim.value
        for claim in claims.claims
    }

    assert values["monthly_emi"] == 8678.23
    assert values["total_payment"] == 2082775.76
    assert values["total_interest"] == 1082775.76


def test_extracts_rupee_formatting():

    response = (
        "EMI: ₹8,678.23"
    )

    claims = FinancialClaimExtractor.extract(
        response=response,
        expected_fields=["monthly_emi"],
    )

    assert len(claims.claims) == 1
    assert claims.claims[0].value == 8678.23


def test_extracts_rs_formatting():

    response = (
        "Monthly EMI is Rs. 8,678.23"
    )

    claims = FinancialClaimExtractor.extract(
        response=response,
        expected_fields=["monthly_emi"],
    )

    assert len(claims.claims) == 1
    assert claims.claims[0].value == 8678.23


def test_missing_field_is_not_invented():

    response = (
        "Your EMI is ₹8,678.23."
    )

    claims = FinancialClaimExtractor.extract(
        response=response,
        expected_fields=[
            "monthly_emi",
            "total_payment",
        ],
    )

    fields = {
        claim.field
        for claim in claims.claims
    }

    assert "monthly_emi" in fields
    assert "total_payment" not in fields


def test_extracted_claims_are_model_inferred():

    response = (
        "Total payment is ₹2,082,775.76."
    )

    claims = FinancialClaimExtractor.extract(
        response=response,
        expected_fields=["total_payment"],
    )

    claim = claims.claims[0]

    assert (
        claim.claim_type.value
        == "MODEL_INFERRED"
    )

    assert claim.authority_source == "llm"

    assert (
        claim.verification_status.value
        == "PENDING"
    )


def test_wrong_total_payment_can_be_extracted():

    response = (
        "Total payment is ₹1,082,775.76."
    )

    claims = FinancialClaimExtractor.extract(
        response=response,
        expected_fields=["total_payment"],
    )

    assert len(claims.claims) == 1
    assert (
        claims.claims[0].value
        == 1082775.76
    )

def test_extractor_and_verifier_work_end_to_end():

    from xai.claim_extractor import (
        FinancialClaimExtractor,
    )
    from xai.claim_verifier import (
        ClaimVerifier,
    )
    from xai.claims import build_finance_claims

    authoritative = build_finance_claims(
        result={
            "monthly_emi": 8678.23,
            "total_payment": 2082775.76,
            "total_interest": 1082775.76,
        },
        source="deterministic_finance_engine",
        operation="EMI_CALCULATION",
    )

    response = (
        "Your monthly EMI is ₹8,678.23. "
        "Total payment is ₹2,082,775.76. "
        "Total interest is ₹1,082,775.76."
    )

    proposed = FinancialClaimExtractor.extract(
        response=response,
        expected_fields=[
            "monthly_emi",
            "total_payment",
            "total_interest",
        ],
    )

    report = ClaimVerifier().verify(
        authoritative=authoritative,
        proposed=proposed,
    )

    assert report.passed
    assert len(report.matched) == 3


def test_extractor_and_verifier_reject_wrong_payment():

    from xai.claim_extractor import (
        FinancialClaimExtractor,
    )
    from xai.claim_verifier import (
        ClaimVerifier,
    )
    from xai.claims import build_finance_claims

    authoritative = build_finance_claims(
        result={
            "monthly_emi": 8678.23,
            "total_payment": 2082775.76,
            "total_interest": 1082775.76,
        },
        source="deterministic_finance_engine",
        operation="EMI_CALCULATION",
    )

    response = (
        "Your monthly EMI is ₹8,678.23. "
        "Total payment is ₹1,082,775.76. "
        "Total interest is ₹1,082,775.76."
    )

    proposed = FinancialClaimExtractor.extract(
        response=response,
        expected_fields=[
            "monthly_emi",
            "total_payment",
            "total_interest",
        ],
    )

    report = ClaimVerifier().verify(
        authoritative=authoritative,
        proposed=proposed,
    )

    assert not report.passed

    mismatched_fields = {
        item["field"]
        for item in report.mismatched
    }

    assert "total_payment" in mismatched_fields

def test_extracts_reverse_total_interest_phrase():

    response = (
        "Your monthly EMI is ₹8,678.23. "
        "Total payment is ₹2,082,775.76, "
        "including ₹1,082,775.76 in total interest."
    )

    claims = FinancialClaimExtractor.extract(
        response=response,
        expected_fields=[
            "monthly_emi",
            "total_payment",
            "total_interest",
        ],
    )

    values = {
        claim.field: claim.value
        for claim in claims.claims
    }

    assert values["monthly_emi"] == 8678.23
    assert values["total_payment"] == 2082775.76
    assert values["total_interest"] == 1082775.76


def test_extracts_multiline_rllm_emi_response_without_cross_field_leakage():

    response = (
        "The EMI for a loan of ₹10 lakh at an annual interest rate "
        "of 8.5% for 20 years (240 months) is ₹8,678.23 per month.\n\n"
        "Total payment over the tenure: ₹2,082,775.76\n"
        "Total interest paid: ₹1,082,775.76\n"
    )

    claims = FinancialClaimExtractor.extract(
        response=response,
        expected_fields=[
            "monthly_emi",
            "total_payment",
            "total_interest",
        ],
    )

    values = {
        claim.field: claim.value
        for claim in claims.claims
    }

    assert values["monthly_emi"] == 8678.23
    assert values["total_payment"] == 2082775.76
    assert values["total_interest"] == 1082775.76


def test_reverse_pattern_does_not_cross_newline():

    response = (
        "Total payment over the tenure: ₹2,082,775.76\n"
        "Total interest paid: ₹1,082,775.76"
    )

    claims = FinancialClaimExtractor.extract(
        response=response,
        expected_fields=["total_interest"],
    )

    assert len(claims.claims) == 1
    assert claims.claims[0].value == 1082775.76
