import json
from collections import Counter
from pathlib import Path

from finai.router import INTENT_TO_TOOL


ROOT = Path(__file__).resolve().parent.parent

DATA_DIR = ROOT / "data" / "sft_final"

SPLITS = {
    "train": 16000,
    "validation": 2000,
    "test": 2000,
}


def load_jsonl(path):
    records = []

    with path.open("r", encoding="utf-8") as file:
        for line_number, line in enumerate(file, start=1):

            line = line.strip()

            if not line:
                continue

            try:
                record = json.loads(line)
            except json.JSONDecodeError as error:
                raise ValueError(
                    f"Invalid JSON in {path} at line {line_number}: {error}"
                )

            records.append(record)

    return records


def validate_split(name, expected_count):

    path = DATA_DIR / f"{name}.jsonl"

    if not path.exists():
        raise FileNotFoundError(
            f"Missing file: {path}"
        )

    records = load_jsonl(path)

    print(f"{name}: {len(records)} records "
          f"(expected {expected_count})")

    if len(records) != expected_count:
        print(
            f"WARNING: {name} count does not match expected count."
        )

    return records


def main():

    print("=" * 70)
    print("FINAI FINAL SFT DATASET VALIDATION")
    print("=" * 70)

    if not DATA_DIR.exists():
        raise FileNotFoundError(
            f"Dataset directory not found: {DATA_DIR}"
        )

    all_records = []

    split_records = {}

    # --------------------------------------------------------
    # Load all splits
    # --------------------------------------------------------

    for name, expected_count in SPLITS.items():

        records = validate_split(
            name,
            expected_count
        )

        split_records[name] = records

        all_records.extend(records)

    # --------------------------------------------------------
    # Counters
    # --------------------------------------------------------

    languages = Counter()
    intents = Counter()
    tools = Counter()

    missing_prompt = 0
    missing_completion = 0
    missing_language = 0
    missing_intent = 0

    malformed_records = 0

    tool_required_without_tool = 0
    tool_mapping_mismatch = 0

    # --------------------------------------------------------
    # Analyze records
    # --------------------------------------------------------

    for index, record in enumerate(
        all_records,
        start=1
    ):

        prompt = str(
            record.get("prompt", "")
        ).strip()

        completion = str(
            record.get("completion", "")
        ).strip()

        language = str(
            record.get("language", "")
        ).strip().lower()

        intent = str(
            record.get("intent", "")
        ).strip().upper()

        requires_tool = bool(
            record.get("requires_tool", False)
        )

        tool_name = str(
            record.get("tool_name", "")
        ).strip()

        # Required fields
        if not prompt:
            missing_prompt += 1

        if not completion:
            missing_completion += 1

        if not language:
            missing_language += 1

        if not intent:
            missing_intent += 1

        # Counters
        languages[language] += 1
        intents[intent] += 1

        if tool_name:
            tools[tool_name] += 1

        # Tool consistency
        expected_tool = INTENT_TO_TOOL.get(intent)

        if requires_tool and not tool_name:
            tool_required_without_tool += 1

        if (
            expected_tool is not None
            and tool_name
            and tool_name != expected_tool
        ):
            tool_mapping_mismatch += 1

    # --------------------------------------------------------
    # Print report
    # --------------------------------------------------------

    print("\n" + "-" * 70)
    print("TOTAL")
    print("-" * 70)

    print(
        "Total records:",
        len(all_records)
    )

    print(
        "Unique intents:",
        len(intents)
    )

    print("\nLanguage distribution:")

    for language, count in languages.most_common():
        print(
            f"  {language}: {count}"
        )

    print("\nIntent distribution:")

    for intent, count in intents.most_common():
        print(
            f"  {intent}: {count}"
        )

    print("\nTool distribution:")

    for tool, count in tools.most_common():
        print(
            f"  {tool}: {count}"
        )

    print("\n" + "-" * 70)
    print("QUALITY CHECKS")
    print("-" * 70)

    print(
        "Missing prompt:",
        missing_prompt
    )

    print(
        "Missing completion:",
        missing_completion
    )

    print(
        "Missing language:",
        missing_language
    )

    print(
        "Missing intent:",
        missing_intent
    )

    print(
        "Tool required without tool:",
        tool_required_without_tool
    )

    print(
        "Tool mapping mismatches:",
        tool_mapping_mismatch
    )

    print("\n" + "=" * 70)

    if (
        len(all_records) == 20000
        and missing_prompt == 0
        and missing_completion == 0
        and missing_language == 0
        and missing_intent == 0
        and tool_required_without_tool == 0
        and tool_mapping_mismatch == 0
    ):

        print("FINAL SFT VALIDATION PASSED ✅")

    else:

        print("FINAL SFT VALIDATION NEEDS ATTENTION ⚠️")

    print("=" * 70)


if __name__ == "__main__":
    main()