import json
import random
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent

INPUT_DIR = ROOT / "data" / "sft"
OUTPUT_DIR = ROOT / "data" / "sft_v2"

TRAIN_IN = INPUT_DIR / "train.jsonl"
VAL_IN = INPUT_DIR / "validation.jsonl"
TEST_IN = INPUT_DIR / "test.jsonl"

TRAIN_OUT = OUTPUT_DIR / "train.jsonl"
VAL_OUT = OUTPUT_DIR / "validation.jsonl"
TEST_OUT = OUTPUT_DIR / "test.jsonl"

SEED = 42


def load_jsonl(path):

    records = []

    with path.open(
        "r",
        encoding="utf-8"
    ) as f:

        for line in f:

            line = line.strip()

            if line:
                records.append(
                    json.loads(line)
                )

    return records


def save_jsonl(path, records):

    with path.open(
        "w",
        encoding="utf-8"
    ) as f:

        for record in records:

            f.write(
                json.dumps(
                    record,
                    ensure_ascii=False
                )
                + "\n"
            )


def normalize_record(record):

    new_record = dict(record)

    # Preserve all existing information.
    new_record.setdefault(
        "language",
        ""
    )

    new_record.setdefault(
        "intent",
        ""
    )

    new_record.setdefault(
        "question",
        ""
    )

    new_record.setdefault(
        "response",
        ""
    )

    new_record["training_stage"] = "sft_v2"

    return new_record


def main():

    random.seed(SEED)

    print("=" * 70)
    print("FINAI-v2 SFT DATA PREPARATION")
    print("=" * 70)

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    print("\nLoading original SFT datasets...")

    train = load_jsonl(TRAIN_IN)
    validation = load_jsonl(VAL_IN)
    test = load_jsonl(TEST_IN)

    print(
        "Original train:",
        len(train)
    )

    print(
        "Original validation:",
        len(validation)
    )

    print(
        "Original test:",
        len(test)
    )

    print("\nNormalizing records...")

    train = [
        normalize_record(x)
        for x in train
    ]

    validation = [
        normalize_record(x)
        for x in validation
    ]

    test = [
        normalize_record(x)
        for x in test
    ]

    # --------------------------------------------------------
    # IMPORTANT:
    # DO NOT REMOVE DUPLICATES HERE.
    #
    # The previous version reduced the dataset from
    # 16k/2k/2k to 250/250/250.
    #
    # We preserve the complete dataset for training.
    # --------------------------------------------------------

    random.shuffle(train)

    save_jsonl(
        TRAIN_OUT,
        train
    )

    save_jsonl(
        VAL_OUT,
        validation
    )

    save_jsonl(
        TEST_OUT,
        test
    )

    print("\n" + "=" * 70)
    print("FINAI-v2 SFT PREPARATION COMPLETE")
    print("=" * 70)

    print(
        "Train:",
        len(train)
    )

    print(
        "Validation:",
        len(validation)
    )

    print(
        "Test:",
        len(test)
    )

    print("\nOutputs:")
    print(TRAIN_OUT)
    print(VAL_OUT)
    print(TEST_OUT)

    print("=" * 70)


if __name__ == "__main__":
    main()