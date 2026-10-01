from datasets import load_dataset


def inspect_dataset(name, split="train", rows=3):

    print("\n" + "=" * 80)
    print(f"DATASET: {name}")
    print("=" * 80)

    try:
        dataset = load_dataset(
            name,
            split=split,
            streaming=True,
        )

        print("Streaming dataset opened successfully.")
        print("Reading first", rows, "records...\n")

        for index, record in enumerate(dataset):

            print("-" * 80)
            print(f"RECORD {index + 1}")

            print("Fields:")
            print(list(record.keys()))

            for key, value in record.items():

                text = str(value)

                if len(text) > 700:
                    text = text[:700] + "... [truncated]"

                print(f"\n{key}:")
                print(text)

            if index + 1 >= rows:
                break

    except Exception as error:

        print("\nFAILED")
        print(type(error).__name__)
        print(str(error))


def main():

    print("=" * 80)
    print("FINAI EXTERNAL DATASET INSPECTION")
    print("=" * 80)

    # --------------------------------------------------------
    # Indian financial / corporate dataset
    # --------------------------------------------------------

    inspect_dataset(
        "TaanishChauhan/finllm-india",
        split="train",
        rows=3,
    )

    # --------------------------------------------------------
    # Indian financial news dataset
    # --------------------------------------------------------

    inspect_dataset(
        "kdave/Indian_Financial_News",
        split="train",
        rows=3,
    )

    # --------------------------------------------------------
    # BhashaBench is intentionally NOT loaded here.
    # It is a gated benchmark and will be handled separately.
    # --------------------------------------------------------

    print("\n" + "=" * 80)
    print("BhashaBench-Finance")
    print("=" * 80)
    print("Skipped for now.")
    print("We will use it as a held-out evaluation benchmark.")
    print("It requires Hugging Face access approval/token.")

    print("\n" + "=" * 80)
    print("INSPECTION COMPLETE")
    print("=" * 80)


if __name__ == "__main__":
    main()