import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

DATASET = ROOT / "data" / "large" / "financial_20k.jsonl"
TAXONOMY = ROOT / "data" / "intent_taxonomy.json"
TOOL_MAP = ROOT / "data" / "intent_tool_map.json"

LANGUAGES = {"en", "ta", "te", "kn", "ml"}
EXPECTED_INTENTS = 50
EXPECTED_PER_PAIR = 80
EXPECTED_TOTAL = 20000


def load_json(path):
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def main():
    taxonomy = load_json(TAXONOMY)
    tool_map = load_json(TOOL_MAP)

    intents = {
        item["intent"]: item
        for item in taxonomy
    }

    records = []

    with DATASET.open("r", encoding="utf-8") as f:
        for line_number, line in enumerate(f, 1):
            line = line.strip()

            if not line:
                continue

            try:
                record = json.loads(line)
            except json.JSONDecodeError as e:
                raise ValueError(
                    f"Invalid JSON at line {line_number}: {e}"
                )

            records.append(record)

    errors = []

    # ----------------------------------------------------------
    # Total count
    # ----------------------------------------------------------
    if len(records) != EXPECTED_TOTAL:
        errors.append(
            f"Expected {EXPECTED_TOTAL} records, "
            f"found {len(records)}"
        )

    # ----------------------------------------------------------
    # Basic fields
    # ----------------------------------------------------------
    required = {
        "id",
        "language",
        "category",
        "intent",
        "text",
        "response",
        "risk_level",
        "requires_tool",
        "tool_name",
        "variation_type",
        "source_type",
    }

    ids = set()
    text_keys = set()

    for index, record in enumerate(records, 1):

        missing = required - set(record)

        if missing:
            errors.append(
                f"Record {index}: missing {missing}"
            )
            continue

        if record["id"] in ids:
            errors.append(
                f"Duplicate ID: {record['id']}"
            )

        ids.add(record["id"])

        if not record["text"].strip():
            errors.append(
                f"Record {index}: empty text"
            )

        if not record["response"].strip():
            errors.append(
                f"Record {index}: empty response"
            )

        if record["language"] not in LANGUAGES:
            errors.append(
                f"Unexpected language: {record['language']}"
            )

        if record["intent"] not in intents:
            errors.append(
                f"Unknown intent: {record['intent']}"
            )

        # Detect duplicate text within the same language/intent.
        key = (
            record["language"],
            record["intent"],
            record["text"].strip().casefold()
        )

        if key in text_keys:
            errors.append(
                f"Duplicate text: {key}"
            )

        text_keys.add(key)

    # ----------------------------------------------------------
    # Language counts
    # ----------------------------------------------------------
    language_counts = Counter(
        r["language"] for r in records
    )

    # ----------------------------------------------------------
    # Intent counts
    # ----------------------------------------------------------
    intent_counts = Counter(
        r["intent"] for r in records
    )

    # ----------------------------------------------------------
    # Language × intent counts
    # ----------------------------------------------------------
    pair_counts = Counter(
        (r["language"], r["intent"])
        for r in records
    )

    for language in LANGUAGES:

        if language_counts[language] != 4000:
            errors.append(
                f"{language}: expected 4000, "
                f"found {language_counts[language]}"
            )

        for intent in intents:

            count = pair_counts[(language, intent)]

            if count != EXPECTED_PER_PAIR:
                errors.append(
                    f"{language}/{intent}: "
                    f"expected {EXPECTED_PER_PAIR}, "
                    f"found {count}"
                )

    # ----------------------------------------------------------
    # Tool consistency
    # ----------------------------------------------------------
    for intent, item in intents.items():

        expected_tool = tool_map[intent]["tool_name"]
        requires_tool = item["requires_tool"]

        for record in records:

            if record["intent"] != intent:
                continue

            if record["tool_name"] != expected_tool:
                errors.append(
                    f"{record['id']}: incorrect tool for {intent}"
                )

            if record["requires_tool"] != requires_tool:
                errors.append(
                    f"{record['id']}: requires_tool mismatch"
                )

    # ----------------------------------------------------------
    # Report
    # ----------------------------------------------------------
    print("=" * 70)
    print("FINAI 20K DATASET VALIDATION")
    print("=" * 70)

    print(f"Total records : {len(records)}")
    print(f"Languages     : {len(LANGUAGES)}")
    print(f"Intents       : {len(intents)}")
    print(f"Unique IDs    : {len(ids)}")

    print("\nLanguage counts:")
    for language in sorted(LANGUAGES):
        print(
            f"  {language}: "
            f"{language_counts[language]}"
        )

    print("\nSource counts:")
    source_counts = Counter(
        r["source_type"] for r in records
    )

    for source, count in sorted(source_counts.items()):
        print(f"  {source}: {count}")

    if errors:
        print("\nVALIDATION FAILED")
        print(f"Problems found: {len(errors)}")

        for error in errors[:50]:
            print(" -", error)

        if len(errors) > 50:
            print(
                f" ... and {len(errors) - 50} more"
            )

        raise SystemExit(1)

    print("\nALL CHECKS PASSED")
    print("20K DATASET IS STRUCTURALLY VALID")
    print("=" * 70)


if __name__ == "__main__":
    main()