import json
from pathlib import Path

from finai.router import (
    INTENT_TO_TOOL,
    NO_TOOL_INTENTS,
)


ROOT = Path(__file__).resolve().parent.parent

DATASET = (
    ROOT
    / "data"
    / "sft_final"
    / "train.jsonl"
)


def load_dataset_intents():

    intents = set()

    with DATASET.open(
        "r",
        encoding="utf-8",
    ) as file:

        for line in file:

            line = line.strip()

            if not line:
                continue

            record = json.loads(line)

            intent = str(
                record.get(
                    "intent",
                    "",
                )
            ).strip().upper()

            if intent:
                intents.add(intent)

    return intents


def main():

    print("=" * 70)
    print("FINAI INTENT COVERAGE TEST")
    print("=" * 70)

    dataset_intents = (
        load_dataset_intents()
    )

    tool_intents = set(
        INTENT_TO_TOOL.keys()
    )

    no_tool_intents = set(
        NO_TOOL_INTENTS
    )

    supported = (
        tool_intents
        | no_tool_intents
    )

    missing = (
        dataset_intents
        - supported
    )

    extra = (
        supported
        - dataset_intents
    )

    print(
        "\nDataset intents:",
        len(dataset_intents),
    )

    print(
        "Tool intents:",
        len(tool_intents),
    )

    print(
        "No-tool intents:",
        len(no_tool_intents),
    )

    print(
        "Supported intents:",
        len(supported),
    )

    print(
        "Missing from router:",
        len(missing),
    )

    if missing:

        print("\nMissing intents:")

        for intent in sorted(missing):

            print(
                " ",
                intent,
            )

    print(
        "\nExtra router intents:",
        len(extra),
    )

    if (
        len(dataset_intents) == 50
        and not missing
    ):

        print(
            "\nINTENT COVERAGE PASSED"
        )

    else:

        print(
            "\nINTENT COVERAGE NEEDS ATTENTION"
        )

    print("=" * 70)


if __name__ == "__main__":
    main()