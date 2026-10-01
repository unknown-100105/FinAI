from xai.claims import (
    ClaimSet,
    build_finance_claims,
    build_model_claim,
)
from xai.integration import XAIIntegration
from xai.trace import XAITrace


def test_xai_trace_records_verified_finance_claims():

    trace = XAITrace("claim-test-session")

    claims = build_finance_claims(
        result={
            "monthly_emi": 8678.23,
            "total_payment": 2082775.76,
            "total_interest": 1082775.76,
        },
        source="deterministic_finance_engine",
        operation="EMI_CALCULATION",
    )

    trace.record_claims(claims)

    assert trace.data["claims"]["total_count"] == 3
    assert (
        trace.data["claims"]["authoritative_count"]
        == 3
    )
    assert trace.data["claims"]["all_verified"] is True


def test_xai_trace_records_model_claim_as_unverified():

    trace = XAITrace("model-claim-session")

    claims = ClaimSet([
        build_model_claim(
            field="balance",
            value=60000,
        )
    ])

    trace.record_claims(claims)

    assert trace.data["claims"]["total_count"] == 1
    assert (
        trace.data["claims"]["authoritative_count"]
        == 0
    )
    assert (
        trace.data["claims"]["all_verified"]
        is False
    )

    assert (
        trace.data["claims"]["items"][0]["claim_type"]
        == "MODEL_INFERRED"
    )


def test_xai_trace_handles_mixed_claims():

    trace = XAITrace("mixed-claim-session")

    financial = build_finance_claims(
        result={
            "monthly_emi": 8678.23,
        },
        source="deterministic_finance_engine",
        operation="EMI_CALCULATION",
    )

    financial.add(
        build_model_claim(
            field="unsupported_claim",
            value="unknown",
        )
    )

    trace.record_claims(financial)

    assert trace.data["claims"]["total_count"] == 2
    assert (
        trace.data["claims"]["authoritative_count"]
        == 1
    )
    assert (
        trace.data["claims"]["all_verified"]
        is False
    )


def test_xai_integration_forwards_claims():

    integration = XAIIntegration(
        session_id="integration-claim-session",
        user_text="Calculate EMI",
    )

    claims = build_finance_claims(
        result={
            "monthly_emi": 8678.23,
        },
        source="deterministic_finance_engine",
        operation="EMI_CALCULATION",
    )

    integration.record_claims(claims)

    assert (
        integration.trace.data["claims"]["total_count"]
        == 1
    )

    assert (
        integration.trace.data["claims"]
        ["authoritative_count"]
        == 1
    )


def test_xai_trace_saves_claims():

    trace = XAITrace("save-claim-session")

    claims = build_finance_claims(
        result={
            "monthly_emi": 8678.23,
        },
        source="deterministic_finance_engine",
        operation="EMI_CALCULATION",
    )

    trace.record_claims(claims)

    path = trace.save()

    assert path.exists()
    assert path.suffix == ".json"
