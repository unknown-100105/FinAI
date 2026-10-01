import json
from pathlib import Path
from collections import defaultdict


ROOT = Path(__file__).resolve().parent.parent

DATASET = ROOT / "data" / "sft_final" / "train.jsonl"


TARGET_INTENTS = [
    "KYC_STATUS",
    "KYC_COMPLETED",

    "MERCHANT_NOT_CREDITED",
    "CASH_WITHDRAWAL_FAILED",
    "CASH_CUT_FAILED",
    "CASH_PAYOUT_FAILED",

    "CARD_LOST",
    "CARD_STOLEN",
    "DONT_SHARE",
]


def main():

    print("=" * 70)
    print("FINAI INTENT-CONFUSION INSPECTION")
    print("=" * 70)

    grouped = defaultdict(list)

    with DATASET.open("r", encoding="utf-8") as f:

        for line in f:

            if not line.strip():
                continue

            row = json.loads(line)

            intent = str(
                row.get("intent", "")
            ).strip().upper()

            if intent in TARGET_INTENTS:

                grouped[intent].append(row)

    for intent in TARGET_INTENTS:

        rows = grouped.get(intent, [])

        print("\n" + "=" * 70)
        print(intent)
        print("Examples:", len(rows))
        print("=" * 70)

        for i, row in enumerate(rows[:10], start=1):

            question = (
                row.get("question")
                or row.get("text")
                or ""
            )

            print(f"\n{i}.")
            print(question)

    print("\n" + "=" * 70)
    print("INSPECTION COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    main()