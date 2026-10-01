from finai.router import (
    parse_model_output,
    route_model_output,
    execute_tool,
)


def main():

    print("=" * 70)
    print("FINAI ROUTER TEST")
    print("=" * 70)

    # ========================================================
    # TEST 1 — CARD LOST
    # ========================================================

    user_text = "I lost my debit card."

    model_output = """
INTENT: CARD_LOST
RISK_LEVEL: high
REQUIRES_TOOL: true
TOOL: block_card
RESPONSE: Your card should be blocked.
"""

    print("\nTEST 1 — CARD LOST")

    print(
        "Parsed:",
        parse_model_output(model_output)
    )

    route = route_model_output(
        user_text,
        model_output,
    )

    print("Route:")
    print(route)

    result = execute_tool(
        route,
        authenticated=False,
        confirmed=False,
    )

    print("Execution:")
    print(result)

    # ========================================================
    # TEST 2 — ACCOUNT BALANCE
    # ========================================================

    user_text = "What is my account balance?"

    model_output = """
INTENT: ACCOUNT_BALANCE
RISK_LEVEL: medium
REQUIRES_TOOL: true
TOOL: get_account_balance
RESPONSE: I can check your balance.
"""

    print("\nTEST 2 — ACCOUNT BALANCE")

    route = route_model_output(
        user_text,
        model_output,
    )

    print("Route:")
    print(route)

    result = execute_tool(
        route,
        authenticated=True,
        confirmed=True,
    )

    print("Execution:")
    print(result)

    # ========================================================
    # TEST 3 — PRIVACY
    # ========================================================

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

    print("\nTEST 3 — PRIVACY PROTECTION")

    route = route_model_output(
        user_text,
        model_output,
    )

    print("Route:")
    print(route)

    # ========================================================
    # TEST 4 — PAYMENT PENDING
    # ========================================================

    user_text = "My payment is still pending."

    model_output = """
INTENT: PAYMENT_PENDING
RISK_LEVEL: medium
REQUIRES_TOOL: true
TOOL: get_transaction_status
RESPONSE: I can check the transaction.
"""

    print("\nTEST 4 — PAYMENT PENDING")

    route = route_model_output(
        user_text,
        model_output,
    )

    print("Route:")
    print(route)

    result = execute_tool(
        route,
        authenticated=True,
        confirmed=True,
    )

    print("Execution:")
    print(result)

    # ========================================================
    # TEST 5 — WRONG MODEL TOOL
    # ========================================================

    user_text = "What is my balance?"

    model_output = """
INTENT: ACCOUNT_BALANCE
RISK_LEVEL: medium
REQUIRES_TOOL: true
TOOL: block_card
RESPONSE: ...
"""

    print("\nTEST 5 — TOOL MISMATCH")

    route = route_model_output(
        user_text,
        model_output,
    )

    print("Route:")
    print(route)

    print("\n" + "=" * 70)
    print("ROUTER TEST COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    main()