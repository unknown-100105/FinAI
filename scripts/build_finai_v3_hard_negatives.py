from pathlib import Path
import json
import hashlib
from collections import Counter, defaultdict

ROOT = Path(__file__).resolve().parents[1]

INPUT = ROOT / "data" / "sft_v3_work" / "finai_v3_intent_seed.jsonl"
OUTPUT = ROOT / "data" / "sft_v3_work" / "finai_v3_hard_negatives.jsonl"
MANIFEST = ROOT / "data" / "manifests" / "finai_v3_hard_negative_manifest.json"


# The most important intent boundaries for the FinAI router.
CONFUSION_PAIRS = [
    ("PAYMENT_FAILED", "PAYMENT_PENDING"),
    ("UPI_PAYMENT_FAILED", "CARD_PAYMENT_FAILED"),
    ("REFUND_PENDING", "REFUND_RECEIVED"),
    ("CARD_LOST", "CARD_STOLEN"),
    ("ACCOUNT_BALANCE", "TRANSACTION_HISTORY"),
    ("KYC_STATUS", "KYC_COMPLETED"),
    ("MERCHANT_NOT_CREDITED", "PAYMENT_FAILED"),
    ("BANK_TRANSFER_FAILED", "BANK_TRANSFER_PENDING"),
    ("UNKNOWN_TRANSACTION", "FRAUD_REPORT"),
    ("DUPLICATE_TRANSACTION", "WRONG_AMOUNT"),
    ("CASH_WITHDRAWAL_FAILED", "CASH_WITHDRAWAL_STATUS"),
]


def stable_key(record):
    text = (
        record.get("intent", "")
        + "\n"
        + record.get("language", "")
        + "\n"
        + record.get("user", "")
        + "\n"
        + record.get("assistant", "")
    )

    return hashlib.sha256(
        text.lower().encode("utf-8")
    ).hexdigest()


def main():

    print("=" * 72)
    print("FINAI-V3 HARD-NEGATIVE / CONFUSION DATASET")
    print("=" * 72)

    if not INPUT.exists():
        raise FileNotFoundError(
            f"Missing input: {INPUT}"
        )

    groups = defaultdict(list)

    with INPUT.open(
        "r",
        encoding="utf-8"
    ) as file:

        for line in file:

            if not line.strip():
                continue

            record = json.loads(line)

            intent = record.get("intent", "")
            language = record.get("language", "")

            if intent and language:
                groups[
                    (intent, language)
                ].append(record)

    selected = []

    # Keep examples from both sides of every confusion boundary.
    # This does not invent labels; it reuses real verified examples.
    PER_SIDE_PER_LANGUAGE = 20

    for left, right in CONFUSION_PAIRS:

        for language in (
            "en",
            "ta",
            "te",
            "kn",
            "ml",
        ):

            left_records = sorted(
                groups.get(
                    (left, language),
                    []
                ),
                key=stable_key
            )

            right_records = sorted(
                groups.get(
                    (right, language),
                    []
                ),
                key=stable_key
            )

            selected.extend(
                left_records[
                    :PER_SIDE_PER_LANGUAGE
                ]
            )

            selected.extend(
                right_records[
                    :PER_SIDE_PER_LANGUAGE
                ]
            )

    # Remove exact duplicates.
    seen = set()
    unique = []

    for record in selected:

        key = stable_key(record)

        if key in seen:
            continue

        seen.add(key)
        unique.append(record)

    unique.sort(
        key=stable_key
    )

    OUTPUT.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    with OUTPUT.open(
        "w",
        encoding="utf-8"
    ) as file:

        for record in unique:
            file.write(
                json.dumps(
                    record,
                    ensure_ascii=False
                )
                + "\n"
            )

    by_intent = Counter(
        record.get(
            "intent",
            "UNKNOWN"
        )
        for record in unique
    )

    by_language = Counter(
        record.get(
            "language",
            "UNKNOWN"
        )
        for record in unique
    )

    by_pair = Counter()

    for left, right in CONFUSION_PAIRS:

        pair_count = 0

        for record in unique:

            intent = record.get(
                "intent",
                ""
            )

            if intent in (left, right):
                pair_count += 1

        by_pair[
            f"{left} <-> {right}"
        ] = pair_count

    manifest = {
        "dataset": "FinAI-V3 hard-negative boundary set",
        "source": str(INPUT),
        "confusion_pairs": [
            list(pair)
            for pair in CONFUSION_PAIRS
        ],
        "per_side_per_language_target": PER_SIDE_PER_LANGUAGE,
        "records": len(unique),
        "records_by_intent": dict(
            by_intent
        ),
        "records_by_language": dict(
            by_language
        ),
        "records_by_pair": dict(
            by_pair
        ),
        "generation_method": (
            "Selected real verified multilingual "
            "examples from both sides of defined "
            "intent-confusion boundaries."
        ),
    }

    MANIFEST.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    MANIFEST.write_text(
        json.dumps(
            manifest,
            ensure_ascii=False,
            indent=2
        ),
        encoding="utf-8"
    )

    print()
    print(
        "CONFUSION PAIRS:",
        len(CONFUSION_PAIRS)
    )

    print()
    print(
        "FINAL HARD-NEGATIVE RECORDS:",
        len(unique)
    )

    print()
    print("BY LANGUAGE:")
    for language, count in sorted(
        by_language.items()
    ):
        print(
            f"  {language}: {count}"
        )

    print()
    print("BY INTENT:")
    for intent, count in sorted(
        by_intent.items()
    ):
        print(
            f"  {intent}: {count}"
        )

    print()
    print("[OK] Dataset:")
    print(OUTPUT)

    print()
    print("[OK] Manifest:")
    print(MANIFEST)

    print("=" * 72)
    print("FINAI-V3 HARD-NEGATIVE BUILD COMPLETE")
    print("=" * 72)


if __name__ == "__main__":
    main()
