from xai.integration import XAIIntegration


def test_finance_xai_trace():

    integration = XAIIntegration(
        session_id="finance-test-001",
        user_text=(
            "Calculate EMI for ₹10 lakh "
            "at 8.5% for 20 years"
        ),
    )

    integration.record_finance(
        operation="EMI_CALCULATION",
        status="CALCULATED",
        parameters={
            "principal": 1_000_000,
            "annual_rate": 8.5,
            "tenure_months": 240,
        },
        result={
            "monthly_emi": 8678.23,
            "total_payment": 2082775.76,
            "total_interest": 1082775.76,
        },
        source="deterministic_finance_engine",
    )

    integration.record_final(
        stage="finance_engine",
        status="CALCULATED",
        message="EMI calculated successfully.",
    )

    path = integration.save()

    assert path.exists()

    assert (
        integration.trace.data["finance"]["operation"]
        == "EMI_CALCULATION"
    )

    assert (
        integration.trace.data["finance"]["source"]
        == "deterministic_finance_engine"
    )

    assert (
        integration.trace.data["finance"]["result"]["monthly_emi"]
        == 8678.23
    )
