from finai.rag import retrieve_context


def run_test(question):

    print("\n" + "=" * 80)
    print("QUESTION")
    print("=" * 80)

    print(question)

    results, context = retrieve_context(
        question,
        top_k=3,
    )

    print("\n" + "=" * 80)
    print("RETRIEVED DOCUMENTS")
    print("=" * 80)

    print(
        "Documents retrieved:",
        len(results)
    )

    for index, result in enumerate(
        results,
        start=1,
    ):

        print(
            f"\n[{index}]"
        )

        print(
            "Source:",
            result.get(
                "source"
            )
        )

        print(
            "Title:",
            result.get(
                "title",
                ""
            )
        )

        print(
            "Company:",
            result.get(
                "company",
                ""
            )
        )

        print(
            "Date:",
            result.get(
                "date",
                ""
            )
        )

        text = result.get(
            "text",
            ""
        )

        print(
            "Text:",
            text[:500],
            "..."
        )

    print("\n" + "=" * 80)
    print("FORMATTED RAG CONTEXT")
    print("=" * 80)

    print(
        context[:4000]
    )


def main():

    print("=" * 80)
    print("FINAI RAG TEST")
    print("=" * 80)

    questions = [
        "Indian banking financial market",
        "RBI monetary policy and interest rates",
        "company financial results",
    ]

    for question in questions:

        run_test(question)

    print("\n" + "=" * 80)
    print("RAG TEST COMPLETE")
    print("=" * 80)


if __name__ == "__main__":
    main()