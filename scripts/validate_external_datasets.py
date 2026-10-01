import json
import re
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent

DATASETS = {
    "finllm_india": (
        ROOT / "data" / "external" / "finllm_india" / "full.jsonl"
    ),
    "indian_financial_news": (
        ROOT / "data" / "external" / "indian_financial_news" / "full.jsonl"
    ),
}


def normalize_text(text):
    text = str(text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def inspect_file(name, path):

    print("\n" + "=" * 80)
    print(name.upper())
    print("=" * 80)

    if not path.exists():
        print("FILE NOT FOUND:", path)
        return

    total = 0
    valid = 0
    empty = 0
    malformed = 0
    duplicates = 0

    seen = set()

    lengths = []

    columns = Counter()

    with path.open("r", encoding="utf-8") as f:

        for line_number, line in enumerate(f, 1):

            line = line.strip()

            if not line:
                continue

            total += 1

            try:
                record = json.loads(line)

            except json.JSONDecodeError:

                malformed += 1
                continue

            columns.update(record.keys())

            # Collect textual content from all string fields.
            text_parts = []

            for key, value in record.items():

                if isinstance(value, str):

                    cleaned = normalize_text(value)

                    if cleaned:
                        text_parts.append(cleaned)

            combined = " ".join(text_parts)

            if not combined:
                empty += 1
                continue

            # Duplicate detection.
            duplicate_key = combined.casefold()

            if duplicate_key in seen:
                duplicates += 1

            else:
                seen.add(duplicate_key)

            valid += 1
            lengths.append(len(combined))

    print("File:", path)

    print("\nRecords")
    print("-------")
    print("Total:", total)
    print("Valid:", valid)
    print("Empty:", empty)
    print("Malformed:", malformed)
    print("Duplicates:", duplicates)

    print("\nFields observed")
    print("----------------")
    for column, count in columns.most_common():
        print(f"{column}: {count}")

    if lengths:

        print("\nText length")
        print("-----------")
        print("Minimum:", min(lengths))
        print("Maximum:", max(lengths))
        print(
            "Average:",
            round(sum(lengths) / len(lengths), 2)
        )

        short = sum(1 for x in lengths if x < 50)
        long = sum(1 for x in lengths if x > 10000)

        print("Under 50 chars:", short)
        print("Over 10,000 chars:", long)


def main():

    print("=" * 80)
    print("FINAI EXTERNAL DATASET QUALITY CHECK")
    print("=" * 80)

    for name, path in DATASETS.items():

        inspect_file(
            name,
            path
        )

    print("\n" + "=" * 80)
    print("EXTERNAL DATASET INSPECTION COMPLETE")
    print("=" * 80)


if __name__ == "__main__":
    main()