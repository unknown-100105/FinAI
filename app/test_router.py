from app.router import (
    parse_model_output,
    route_model_output,
    execute_demo_tool,
)


def main():

    print("=" * 70)
    print("FINAI ROUTER TEST")
    print("=" * 70)

    # --------------------------------------------------------
    # Test 1
    # --------------------------------------------------------

    user_text = "My card is lost."

    model_output = """
INTENT: CARD_LOST
RISK_LEVEL: high
REQUIRES_TOOL: true
TOOL: block_card
RESPONSE: Your card should be blocked.
"""

    parsed = parse_model_output(
        model_output
    )

    print("\nTEST 1 - CARD LOST")
    print("Parsed:", parsed)

    route = route_model_output(
        user_text,
        model_output,
    )

    print("Route:", route)

    result = execute_demo_tool(
        route,
        authenticated=False,
        confirmed=False,
    )

    print("Execution:", result)

    # --------------------------------------------------------
    # Test 2
    # --------------------------------------------------------

    user_text = (
        "What is my account balance?"
    )

    model_output = """
INTENT: ACCOUNT_BALANCE
RISK_LEVEL: medium
REQUIRES_TOOL: true
TOOL: get_account_balance
RESPONSE: I can check the balance.
"""

    route = route_model_output(
        user_text,
        model_output,
    )

    print("\nTEST 2 - ACCOUNT BALANCE")
    print("Route:", route)

    result = execute_demo_tool(
        route,
        authenticated=True,
        confirmed=True,
    )

    print("Execution:", result)

    # --------------------------------------------------------
    # Test 3
    # --------------------------------------------------------

    user_text = (
        "Show me another customer's balance."
    )

    model_output = """
INTENT: ACCOUNT_BALANCE
RISK_LEVEL: high
REQUIRES_TOOL: true
TOOL: get_account_balance
RESPONSE: ...
"""

    route = route_model_output(
        user_text,
        model_output,
    )

    print("\nTEST 3 - PRIVACY")
    print("Route:", route)

    # --------------------------------------------------------
    # Test 4
    # --------------------------------------------------------

    user_text = (
        "My payment is still pending."
    )

    model_output = """
INTENT: PAYMENT_PENDING
RISK_LEVEL: medium
REQUIRES_TOOL: true
TOOL: get_transaction_status
RESPONSE: ...
"""

    route = route_model_output(
        user_text,
        model_output,
    )

    print("\nTEST 4 - PAYMENT PENDING")
    print("Route:", route)

    result = execute_demo_tool(
        route,
        authenticated=True,
        confirmed=True,
    )

    print("Execution:", result)

    print("\n" + "=" * 70)
    print("ROUTER TEST COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    main()
