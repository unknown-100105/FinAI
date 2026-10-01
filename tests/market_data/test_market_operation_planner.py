from orchestrator.market_operation_planner import (
    OP_ANALYTICS,
    OP_HISTORY,
    OP_QUOTE,
    plan_market_operations,
)


def test_default_quote():
    result = plan_market_operations(
        "What is NIFTY 50 today?"
    )

    assert result.operations == (OP_QUOTE,)


def test_history_request():
    result = plan_market_operations(
        "Show NIFTY 50 price history"
    )

    assert result.operations == (OP_HISTORY,)


def test_analytics_request():
    result = plan_market_operations(
        "What is NIFTY volatility and RSI?"
    )

    assert result.operations == (OP_ANALYTICS,)


def test_history_and_analytics():
    result = plan_market_operations(
        "Show NIFTY for the last year and calculate return"
    )

    assert result.operations == (
        OP_HISTORY,
        OP_ANALYTICS,
    )


def test_empty_text_defaults_to_quote():
    result = plan_market_operations("")

    assert result.operations == (OP_QUOTE,)
