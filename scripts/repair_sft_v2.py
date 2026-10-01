import json
import sys
from pathlib import Path


# ------------------------------------------------------------
# Add the FinAI project root to Python's import path.
# This allows scripts/ to import the finai package.
# ------------------------------------------------------------

ROOT = Path(__file__).resolve().parent.parent

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


from finai.router import INTENT_TO_TOOL


INPUT_DIR = ROOT / "data" / "sft_v2"
OUTPUT_DIR = ROOT / "data" / "sft_final"

FILES = {
    "train": (
        INPUT_DIR / "train.jsonl",
        OUTPUT_DIR / "train.jsonl",
    ),
    "validation": (
        INPUT_DIR / "validation.jsonl",
        OUTPUT_DIR / "validation.jsonl",
    ),
    "test": (
        INPUT_DIR / "test.jsonl",
        OUTPUT_DIR / "test.jsonl",
    ),
}


def load_jsonl(path):

    records = []

    with path.open(
        "r",
        encoding="utf-8",
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
        encoding="utf-8",
    ) as f:

        for record in records:

            f.write(
                json.dumps(
                    record,
                    ensure_ascii=False,
                )
                + "\n"
            )


def repair_record(record):

    repaired = dict(record)

    intent = str(
        repaired.get(
            "intent",
            "",
        )
    ).strip().upper()

    expected_tool = INTENT_TO_TOOL.get(
        intent
    )

    if expected_tool:

        repaired["requires_tool"] = True
        repaired["tool_name"] = expected_tool

    else:

        repaired["requires_tool"] = False
        repaired["tool_name"] = ""

    repaired["training_stage"] = "sft_final"

    return repaired


def main():

    print("=" * 70)
    print("FINAI FINAL SFT DATASET REPAIR")
    print("=" * 70)

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    total_before = 0
    total_after = 0
    changes = 0

    for split, (
        input_file,
        output_file,
    ) in FILES.items():

        print("\nProcessing:", split)

        records = load_jsonl(
            input_file
        )

        print(
            "Input records:",
            len(records)
        )

        repaired_records = []

        for record in records:

            old_requires_tool = record.get(
                "requires_tool"
            )

            old_tool = record.get(
                "tool_name",
                ""
            )

            repaired = repair_record(
                record
            )

            if (
                old_requires_tool
                != repaired["requires_tool"]
                or old_tool
                != repaired["tool_name"]
            ):

                changes += 1

            repaired_records.append(
                repaired
            )

        save_jsonl(
            output_file,
            repaired_records
        )

        total_before += len(records)
        total_after += len(
            repaired_records
        )

        print(
            "Output records:",
            len(repaired_records)
        )

        print(
            "Saved:",
            output_file
        )

    print("\n" + "=" * 70)
    print("FINAL SFT DATASET REPAIR COMPLETE")
    print("=" * 70)

    print(
        "Records before:",
        total_before
    )

    print(
        "Records after:",
        total_after
    )

    print(
        "Metadata changes:",
        changes
    )

    print("\nFinal dataset:")

    print(
        OUTPUT_DIR
    )

    print("=" * 70)


if __name__ == "__main__":
    main()


ROOT = Path(__file__).resolve().parent.parent

INPUT_DIR = ROOT / "data" / "sft_v2"
OUTPUT_DIR = ROOT / "data" / "sft_final"

FILES = {
    "train": (
        INPUT_DIR / "train.jsonl",
        OUTPUT_DIR / "train.jsonl",
    ),
    "validation": (
        INPUT_DIR / "validation.jsonl",
        OUTPUT_DIR / "validation.jsonl",
    ),
    "test": (
        INPUT_DIR / "test.jsonl",
        OUTPUT_DIR / "test.jsonl",
    ),
}


def load_jsonl(path):

    records = []

    with path.open(
        "r",
        encoding="utf-8",
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
        encoding="utf-8",
    ) as f:

        for record in records:

            f.write(
                json.dumps(
                    record,
                    ensure_ascii=False,
                )
                + "\n"
            )


def repair_record(record):

    repaired = dict(record)

    intent = str(
        repaired.get(
            "intent",
            "",
        )
    ).strip().upper()

    expected_tool = INTENT_TO_TOOL.get(
        intent
    )

    # --------------------------------------------------------
    # Use the server-side router as the authoritative source.
    # --------------------------------------------------------

    if expected_tool:

        repaired["requires_tool"] = True
        repaired["tool_name"] = expected_tool

    else:

        repaired["requires_tool"] = False
        repaired["tool_name"] = ""

    # Keep the fields used by the SFT trainer.
    repaired["training_stage"] = "sft_final"

    return repaired


def main():

    print("=" * 70)
    print("FINAI FINAL SFT DATASET REPAIR")
    print("=" * 70)

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    total_before = 0
    total_after = 0

    changes = 0

    for split, (
        input_file,
        output_file,
    ) in FILES.items():

        print("\nProcessing:", split)

        records = load_jsonl(
            input_file
        )

        print(
            "Input records:",
            len(records)
        )

        repaired_records = []

        for record in records:

            old_requires_tool = record.get(
                "requires_tool"
            )

            old_tool = record.get(
                "tool_name",
                ""
            )

            repaired = repair_record(
                record
            )

            if (
                old_requires_tool
                != repaired["requires_tool"]
                or old_tool
                != repaired["tool_name"]
            ):

                changes += 1

            repaired_records.append(
                repaired
            )

        save_jsonl(
            output_file,
            repaired_records
        )

        total_before += len(records)
        total_after += len(
            repaired_records
        )

        print(
            "Output records:",
            len(repaired_records)
        )

        print(
            "Saved:",
            output_file
        )

    print("\n" + "=" * 70)
    print("FINAL SFT DATASET REPAIR COMPLETE")
    print("=" * 70)

    print(
        "Records before:",
        total_before
    )

    print(
        "Records after:",
        total_after
    )

    print(
        "Metadata changes:",
        changes
    )

    print("\nFinal dataset:")

    print(
        OUTPUT_DIR
    )

    print("=" * 70)


if __name__ == "__main__":
    main()