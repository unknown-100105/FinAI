import json
from collections import Counter
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATASET = PROJECT_ROOT / "data" / "financial_intents.jsonl"

EXPECTED_LANGUAGES = {"en", "ta", "te", "kn", "ml"}
EXPECTED_EXAMPLES = 100
EXPECTED_PER_LANGUAGE = 20
EXPECTED_PER_INTENT = 5


def load_dataset():
    if not DATASET.exists():
        raise FileNotFoundError(f"Dataset not found:\n{DATASET}")

    records = []

    with DATASET.open("r", encoding="utf-8") as f:
        for line_number, line in enumerate(f, start=1):
            line = line.strip()

            if not line:
                continue

            try:
                record = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(
                    f"Invalid JSON on line {line_number}: {exc}"
                ) from exc

            records.append(record)

    return records


def main():
    records = load_dataset()

    print("=" * 65)
    print("FINAI DATASET QUALITY CHECK")
    print("=" * 65)

    errors = []

    # ------------------------------------------------------------
    # 1. Total count
    # ------------------------------------------------------------
    if len(records) != EXPECTED_EXAMPLES:
        errors.append(
            f"Expected {EXPECTED_EXAMPLES} examples, "
            f"found {len(records)}."
        )

    # ------------------------------------------------------------
    # 2. Required fields
    # ------------------------------------------------------------
    required = {"language", "intent", "text", "response"}

    for index, record in enumerate(records, start=1):
        missing = required - set(record.keys())

        if missing:
            errors.append(
                f"Example {index}: missing fields {missing}"
            )

        for field in required:
            if field in record:
                if not isinstance(record[field], str):
                    errors.append(
                        f"Example {index}: {field} is not a string"
                    )
                elif not record[field].strip():
                    errors.append(
                        f"Example {index}: {field} is empty"
                    )

    # ------------------------------------------------------------
    # 3. Language distribution
    # ------------------------------------------------------------
    language_counts = Counter(
        r.get("language") for r in records
    )

    print("\nLanguage distribution:")

    for language in sorted(EXPECTED_LANGUAGES):
        count = language_counts.get(language, 0)
        print(f"  {language}: {count}")

        if count != EXPECTED_PER_LANGUAGE:
            errors.append(
                f"Language '{language}' has {count} examples; "
                f"expected {EXPECTED_PER_LANGUAGE}."
            )

    unexpected_languages = set(language_counts) - EXPECTED_LANGUAGES

    if unexpected_languages:
        errors.append(
            f"Unexpected languages: {unexpected_languages}"
        )

    # ------------------------------------------------------------
    # 4. Intent distribution
    # ------------------------------------------------------------
    intent_counts = Counter(
        r.get("intent") for r in records
    )

    print("\nIntent distribution:")

    for intent, count in sorted(intent_counts.items()):
        print(f"  {intent}: {count}")

        if count != EXPECTED_PER_INTENT:
            errors.append(
                f"Intent '{intent}' has {count} examples; "
                f"expected {EXPECTED_PER_INTENT}."
            )

    # ------------------------------------------------------------
    # 5. Duplicate detection
    # ------------------------------------------------------------
    texts = [
        r.get("text", "").strip().casefold()
        for r in records
    ]

    text_counts = Counter(texts)

    duplicates = {
        text: count
        for text, count in text_counts.items()
        if text and count > 1
    }

    print("\nDuplicate user messages:")

    if duplicates:
        for text, count in duplicates.items():
            print(f"  {count}x: {text}")
            errors.append(
                f"Duplicate user message found: {text}"
            )
    else:
        print("  None")

    # ------------------------------------------------------------
    # 6. Check language-intent combinations
    # ------------------------------------------------------------
    combinations = Counter(
        (r.get("language"), r.get("intent"))
        for r in records
    )

    print("\nLanguage × intent coverage:")

    for language in sorted(EXPECTED_LANGUAGES):
        missing_intents = []

        for intent in intent_counts:
            if combinations[(language, intent)] != 1:
                missing_intents.append(intent)

        if missing_intents:
            errors.append(
                f"{language} missing/duplicated intents: "
                f"{missing_intents}"
            )

        print(
            f"  {language}: "
            f"{len(intent_counts) - len(missing_intents)} / "
            f"{len(intent_counts)} intents"
        )

    # ------------------------------------------------------------
    # 7. Final result
    # ------------------------------------------------------------
    print("\n" + "=" * 65)

    if errors:
        print("QUALITY CHECK FAILED")
        print("=" * 65)

        print("\nProblems found:")

        for error in errors:
            print(f"  - {error}")

        raise SystemExit(1)

    print("QUALITY CHECK PASSED")
    print("=" * 65)
    print("\nDataset is structurally ready for the next stage.")


if __name__ == "__main__":
    main()