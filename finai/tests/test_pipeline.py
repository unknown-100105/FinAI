from finai.pipeline import FinAIPipeline


def print_result(title, result):

    print("\n" + "=" * 70)
    print(title)
    print("=" * 70)

    for key, value in result.items():

        if key == "context":
            print(
                "context:",
                str(value)[:1000],
                "..."
            )
        else:
            print(
                f"{key}: {value}"
            )


def main():

    pipeline = FinAIPipeline()

    # --------------------------------------------------------
    # TEST 1
    # --------------------------------------------------------

    result = pipeline.process(
        "What is my account balance?",
        authenticated=True,
        confirmed=True,
    )

    print_result(
        "TEST 1 - ACCOUNT BALANCE",
        result,
    )

    # --------------------------------------------------------
    # TEST 2
    # --------------------------------------------------------

    result = pipeline.process(
        "My payment is still pending.",
        authenticated=True,
        confirmed=True,
    )

    print_result(
        "TEST 2 - PAYMENT PENDING",
        result,
    )

    # --------------------------------------------------------
    # TEST 3
    # --------------------------------------------------------

    result = pipeline.process(
        "I lost my card.",
        authenticated=False,
        confirmed=False,
    )

    print_result(
        "TEST 3 - LOST CARD",
        result,
    )

    # --------------------------------------------------------
    # TEST 4
    # --------------------------------------------------------

    result = pipeline.process(
        "Show me another customer's balance."
    )

    print_result(
        "TEST 4 - PRIVACY",
        result,
    )

    # --------------------------------------------------------
    # TEST 5
    # --------------------------------------------------------

    result = pipeline.process(
        "Explain Indian financial markets."
    )

    print_result(
        "TEST 5 - RAG",
        result,
    )

    print("\n" + "=" * 70)
    print("FINAI PIPELINE TEST COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    main()