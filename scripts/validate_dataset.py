import json
from collections import Counter
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATASET = PROJECT_ROOT / "data" / "financial_intents.jsonl"


def main():
    if not DATASET.exists():
        raise FileNotFoundError(
            f"Dataset not found: {DATASET}"
        )

    examples = []

    with DATASET.open("r", encoding="utf-8") as f:
        for line_number, line in enumerate(f, start=1):
            line = line.strip()

            if not line:
                continue

            try:
                item = json.loads(line)
            except json.JSONDecodeError as e:
                raise ValueError(
                    f"Invalid JSON on line {line_number}: {e}"
                ) from e

            required_fields = {
                "language",
                "intent",
                "text",
                "response",
            }

            missing = required_fields - set(item.keys())

            if missing:
                raise ValueError(
                    f"Line {line_number} is missing: {missing}"
                )

            for field in required_fields:
                if not isinstance(item[field], str):
                    raise ValueError(
                        f"Line {line_number}: '{field}' must be text"
                    )

                if not item[field].strip():
                    raise ValueError(
                        f"Line {line_number}: '{field}' is empty"
                    )

            examples.append(item)

    if not examples:
        raise ValueError("Dataset is empty.")

    language_counts = Counter(
        item["language"] for item in examples
    )

    intent_counts = Counter(
        item["intent"] for item in examples
    )

    print("=" * 60)
    print("FINAI DATASET VALIDATION")
    print("=" * 60)

    print(f"Dataset : {DATASET}")
    print(f"Examples: {len(examples)}")

    print("\nExamples by language:")
    for language, count in sorted(language_counts.items()):
        print(f"  {language}: {count}")

    print("\nExamples by intent:")
    for intent, count in sorted(intent_counts.items()):
        print(f"  {intent}: {count}")

    print("\nFirst example:")
    print(
        json.dumps(
            examples[0],
            ensure_ascii=False,
            indent=2
        )
    )

    print("\nDataset validation PASSED")
    print("=" * 60)


if __name__ == "__main__":
    main()