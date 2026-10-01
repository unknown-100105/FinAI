import json
from collections import Counter, defaultdict
from pathlib import Path

from finai.router import INTENT_TO_TOOL


ROOT = Path(__file__).resolve().parent.parent

TRAIN_FILE = (
    ROOT
    / "data"
    / "sft_final"
    / "train.jsonl"
)

MISSING_INTENTS = {
    "BANK_TRANSFER_FAILED",
    "BENEFICIARY_ISSUE",
    "CARD_ACTIVATION",
    "CARD_PAYMENT_FAILED",
    "KYC_DOCUMENTS",
    "KYC_FAILED",
    "LIMIT_QUERY",
    "LOAN_ELIGIBILITY",
    "PAYMENT_FAILED",
    "PAYMENT_LIMIT",
    "PIN_FAILED",
    "SUPPORT_REQUEST",
    "UPI_COLLECT_REQUEST",
    "UPI_ID_ISSUE",
    "UPI_PAYMENT_FAILED",
}


def main():

    print("=" * 70)
    print("FINAI - MISSING INTENT TOOL INSPECTION")
    print("=" * 70)

    if not TRAIN_FILE.exists():
        print("ERROR: Dataset not found:")
        print(TRAIN_FILE)
        return

    tool_counts = defaultdict(Counter)

    with TRAIN_FILE.open(
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

            if intent not in MISSING_INTENTS:
                continue

            tool = str(
                record.get(
                    "tool_name",
                    "",
                )
            ).strip()

            if not tool:
                tool = "<NO TOOL>"

            tool_counts[intent][tool] += 1

    print()
    print(
        "DATASET TOOL MAPPING FOR THE 15 MISSING INTENTS"
    )
    print("-" * 70)

    for intent in sorted(MISSING_INTENTS):

        print()
        print(intent)

        dataset_tools = tool_counts.get(
            intent,
            {}
        )

        if not dataset_tools:
            print("  No records found")
            continue

        for tool, count in dataset_tools.most_common():

            print(
                f"  {tool}: {count}"
            )

        router_tool = INTENT_TO_TOOL.get(
            intent
        )

        if router_tool:

            print(
                f"  Current router mapping: {router_tool}"
            )

        else:

            print(
                "  Current router mapping: MISSING"
            )

    print()
    print("=" * 70)
    print("INSPECTION COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    main()