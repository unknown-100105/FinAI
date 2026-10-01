import json
from pathlib import Path
from collections import defaultdict

PROJECT_ROOT = Path(__file__).resolve().parent.parent

INPUT_FILE = PROJECT_ROOT / "data" / "financial_intents.jsonl"
OUTPUT_DIR = PROJECT_ROOT / "data" / "processed"

TRAIN_FILE = OUTPUT_DIR / "train.jsonl"
VAL_FILE = OUTPUT_DIR / "validation.jsonl"
TEST_FILE = OUTPUT_DIR / "test.jsonl"


def load_dataset():
    records = []

    with INPUT_FILE.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()

            if line:
                records.append(json.loads(line))

    return records


def save_jsonl(path, records):
    with path.open("w", encoding="utf-8") as f:
        for record in records:
            f.write(
                json.dumps(
                    record,
                    ensure_ascii=False
                ) + "\n"
            )


def main():
    if not INPUT_FILE.exists():
        raise FileNotFoundError(
            f"Dataset not found: {INPUT_FILE}"
        )

    records = load_dataset()

    # Group examples by intent.
    # Each intent currently has 5 language examples.
    intent_groups = defaultdict(list)

    for record in records:
        intent_groups[record["intent"]].append(record)

    intents = sorted(intent_groups.keys())

    # 20 intents:
    # 16 -> train
    # 2  -> validation
    # 2  -> test
    train_intents = intents[:16]
    validation_intents = intents[16:18]
    test_intents = intents[18:20]

    train_records = []
    validation_records = []
    test_records = []

    for intent in train_intents:
        train_records.extend(intent_groups[intent])

    for intent in validation_intents:
        validation_records.extend(intent_groups[intent])

    for intent in test_intents:
        test_records.extend(intent_groups[intent])

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    save_jsonl(TRAIN_FILE, train_records)
    save_jsonl(VAL_FILE, validation_records)
    save_jsonl(TEST_FILE, test_records)

    print("=" * 60)
    print("FINAI DATASET SPLIT")
    print("=" * 60)

    print(f"Total examples     : {len(records)}")
    print(f"Training examples  : {len(train_records)}")
    print(f"Validation examples: {len(validation_records)}")
    print(f"Test examples      : {len(test_records)}")

    print("\nTraining intents:")
    for intent in train_intents:
        print(f"  {intent}")

    print("\nValidation intents:")
    for intent in validation_intents:
        print(f"  {intent}")

    print("\nTest intents:")
    for intent in test_intents:
        print(f"  {intent}")

    print("\nFiles created:")
    print(f"  {TRAIN_FILE}")
    print(f"  {VAL_FILE}")
    print(f"  {TEST_FILE}")

    print("\nSPLIT COMPLETE")
    print("=" * 60)
if __name__ == "__main__":
    main()