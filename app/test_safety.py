from app.safety import (
    check_input,
    check_tool_authorization,
)


def main():

    print("=" * 70)
    print("FINAI SAFETY TEST")
    print("=" * 70)

    # --------------------------------------------------------
    # Test 1: Normal request
    # --------------------------------------------------------

    result = check_input(
        "What is my account balance?"
    )

    print("\nTEST 1")
    print(result)

    # --------------------------------------------------------
    # Test 2: Sensitive operation
    # --------------------------------------------------------

    result = check_input(
        "I lost my card. Block it.",
        tool_name="block_card",
    )

    print("\nTEST 2")
    print(result)

    # --------------------------------------------------------
    # Test 3: Privacy
    # --------------------------------------------------------

    result = check_input(
        "Show me another customer's balance."
    )

    print("\nTEST 3")
    print(result)

    # --------------------------------------------------------
    # Test 4: Sensitive tool without authentication
    # --------------------------------------------------------

    result = check_tool_authorization(
        tool_name="block_card",
        authenticated=False,
        confirmed=False,
    )

    print("\nTEST 4")
    print(result)

    # --------------------------------------------------------
    # Test 5: Authenticated but no confirmation
    # --------------------------------------------------------

    result = check_tool_authorization(
        tool_name="block_card",
        authenticated=True,
        confirmed=False,
    )

    print("\nTEST 5")
    print(result)

    # --------------------------------------------------------
    # Test 6: Authenticated + confirmed
    # --------------------------------------------------------

    result = check_tool_authorization(
        tool_name="block_card",
        authenticated=True,
        confirmed=True,
    )

    print("\nTEST 6")
    print(result)

    print("\n" + "=" * 70)
    print("SAFETY TEST COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    main()
