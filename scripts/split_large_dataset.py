import json
import random
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

INPUT = ROOT / "data" / "large" / "financial_20k.jsonl"
OUTPUT = ROOT / "data" / "processed_large"

TRAIN = OUTPUT / "train.jsonl"
VALIDATION = OUTPUT / "validation.jsonl"
TEST = OUTPUT / "test.jsonl"


SEED = 42

TRAIN_PER_PAIR = 64
VAL_PER_PAIR = 8
TEST_PER_PAIR = 8


def save_jsonl(path, records):
    with path.open("w", encoding="utf-8") as f:
        for record in records:
            f.write(
                json.dumps(record, ensure_ascii=False) + "\n"
            )


def main():
    random.seed(SEED)

    groups = defaultdict(list)

    with INPUT.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()

            if line:
                record = json.loads(line)

                key = (
                    record["language"],
                    record["intent"]
                )

                groups[key].append(record)

    train = []
    validation = []
    test = []

    for key, records in sorted(groups.items()):

        if len(records) != 80:
            raise ValueError(
                f"{key} has {len(records)} records, expected 80."
            )

        # Keep curated examples in training when available.
        curated = [
            r for r in records
            if r["source_type"] == "human_curated_seed"
        ]

        synthetic = [
            r for r in records
            if r["source_type"] != "human_curated_seed"
        ]

        random.shuffle(synthetic)

        ordered = curated + synthetic

        train.extend(
            ordered[:TRAIN_PER_PAIR]
        )

        validation.extend(
            ordered[
                TRAIN_PER_PAIR:
                TRAIN_PER_PAIR + VAL_PER_PAIR
            ]
        )

        test.extend(
            ordered[
                TRAIN_PER_PAIR + VAL_PER_PAIR:
            ]
        )

    random.shuffle(train)
    random.shuffle(validation)
    random.shuffle(test)

    OUTPUT.mkdir(parents=True, exist_ok=True)

    save_jsonl(TRAIN, train)
    save_jsonl(VALIDATION, validation)
    save_jsonl(TEST, test)

    print("=" * 70)
    print("FINAI LARGE DATASET SPLIT")
    print("=" * 70)

    print(f"Total       : {len(train) + len(validation) + len(test)}")
    print(f"Train       : {len(train)}")
    print(f"Validation  : {len(validation)}")
    print(f"Test        : {len(test)}")

    print("\nExpected:")
    print("Train      : 16000")
    print("Validation : 2000")
    print("Test       : 2000")

    print("\nSPLIT COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    main()