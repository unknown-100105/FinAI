from orchestrator.hybrid_engine import FinAIHybridEngine


def test_complete_emi_exposes_compute_execution_plan():

    engine = FinAIHybridEngine()

    result = engine.process(
        user_text=(
            "Calculate EMI for ₹10 lakh at "
            "8.5% for 20 years"
        )
    )

    plan = result["execution_plan"]

    assert plan["intent"] == "EMI_QUERY"
    assert plan["decision"] == "EXECUTE"
    assert plan["capability"] == "finance_engine"
    assert plan["execution_class"] == "COMPUTE"
    assert (
        plan["authority_source"]
        == "deterministic_finance_engine"
    )


def test_incomplete_emi_still_uses_compute_path():

    engine = FinAIHybridEngine()

    result = engine.process(
        user_text="Calculate my EMI"
    )

    plan = result["execution_plan"]

    assert plan["intent"] == "EMI_QUERY"
    assert plan["capability"] == "finance_engine"
    assert plan["execution_class"] == "COMPUTE"


def test_account_balance_exposes_tool_lookup_plan():

    engine = FinAIHybridEngine()

    result = engine.process(
        user_text="How much is my account balance?",
        authenticated=True,
    )

    plan = result["execution_plan"]

    assert plan["intent"] == "ACCOUNT_BALANCE"
    assert plan["decision"] == "EXECUTE"
    assert plan["capability"] == "tool_engine"
    assert plan["execution_class"] == "TOOL_LOOKUP"
    assert plan["tool"] == "get_account_balance"


def test_lost_card_exposes_high_risk_action_plan():

    engine = FinAIHybridEngine()

    result = engine.process(
        user_text="My card is lost",
        authenticated=False,
        confirmed=False,
    )

    plan = result["execution_plan"]

    assert plan["intent"] == "CARD_LOST"
    assert plan["risk_level"] == "high"
    assert plan["capability"] == "tool_engine"
    assert plan["execution_class"] == "ACT"
    assert plan["tool"] == "block_card"
    assert plan["authentication_required"] is True
    assert plan["confirmation_required"] is True


def test_ambiguous_payment_does_not_execute():

    engine = FinAIHybridEngine()

    result = engine.process(
        user_text="The payment failed"
    )

    plan = result["execution_plan"]

    assert plan["decision"] in {
        "CLARIFY",
        "REJECT",
    }

    assert plan["execution_class"] == "NONE"
    assert plan["capability"] in {
        "none",
        "unknown",
    }
