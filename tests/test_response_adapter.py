from llm.response_adapter import SarvamResponseAdapter


def test_prompt_contains_verified_result():

    adapter = SarvamResponseAdapter()

    verified = {
        "monthly_emi": 8678.23,
        "total_payment": 2082775.76,
        "total_interest": 1082775.76,
    }

    prompt = adapter.build_prompt(
        user_text="Calculate my EMI",
        intent="EMI_QUERY",
        verified_result=verified,
        source="deterministic_finance_engine",
    )

    assert "EMI_QUERY" in prompt
    assert "8678.23" in prompt
    assert "2082775.76" in prompt
    assert "1082775.76" in prompt
    assert "Do not change, recalculate, invent" in prompt


def test_fallback_preserves_emi_numbers():

    adapter = SarvamResponseAdapter()

    result = adapter.generate(
        user_text="Calculate my EMI",
        intent="EMI_QUERY",
        verified_result={
            "monthly_emi": 8678.23,
            "total_payment": 2082775.76,
            "total_interest": 1082775.76,
        },
        source="deterministic_finance_engine",
    )

    assert result["status"] == "FALLBACK"
    assert "₹8,678.23" in result["response"]
    assert "₹2,082,775.76" in result["response"]
    assert "₹1,082,775.76" in result["response"]


def test_fallback_interest():

    adapter = SarvamResponseAdapter()

    result = adapter.generate(
        user_text="Calculate compound interest",
        intent="INTEREST_QUERY",
        verified_result={
            "final_amount": 148984.57,
            "total_interest": 48984.57,
        },
        source="deterministic_finance_engine",
    )

    assert result["status"] == "FALLBACK"
    assert "₹148,984.57" in result["response"]
    assert "₹48,984.57" in result["response"]


def test_persona_is_preserved():

    adapter = SarvamResponseAdapter()

    result = adapter.generate(
        user_text="Calculate my EMI",
        intent="EMI_QUERY",
        verified_result={
            "monthly_emi": 8678.23,
            "total_payment": 2082775.76,
            "total_interest": 1082775.76,
        },
        source="deterministic_finance_engine",
        persona="stern",
    )

    assert result["persona"] == "stern"
