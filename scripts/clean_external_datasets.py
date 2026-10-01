import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent

FINLLM_INPUT = (
    ROOT
    / "data"
    / "external"
    / "finllm_india"
    / "full.jsonl"
)

NEWS_INPUT = (
    ROOT
    / "data"
    / "external"
    / "indian_financial_news"
    / "full.jsonl"
)

OUTPUT_DIR = ROOT / "data" / "domain"

FINLLM_OUTPUT = OUTPUT_DIR / "finllm_india_clean.jsonl"
NEWS_OUTPUT = OUTPUT_DIR / "indian_financial_news_clean.jsonl"
COMBINED_OUTPUT = OUTPUT_DIR / "combined_domain.jsonl"


def normalize_text(text):
    if text is None:
        return ""

    text = str(text)

    # Normalize whitespace.
    text = re.sub(r"\s+", " ", text)

    # Remove obvious repeated separator characters.
    text = re.sub(r"[ \t]+", " ", text)

    return text.strip()


def valid_text(text):
    if not text:
        return False

    # Ignore extremely short fragments.
    if len(text) < 100:
        return False

    # Ignore obvious non-content placeholders.
    bad_values = {
        "nan",
        "none",
        "null",
        "n/a",
        "na",
    }

    if text.lower() in bad_values:
        return False

    return True


def write_jsonl(path, records):
    with path.open("w", encoding="utf-8") as f:
        for record in records:
            f.write(
                json.dumps(
                    record,
                    ensure_ascii=False,
                )
                + "\n"
            )


def clean_finllm():
    print("\n" + "=" * 80)
    print("CLEANING FINLLM-INDIA")
    print("=" * 80)

    if not FINLLM_INPUT.exists():
        raise FileNotFoundError(FINLLM_INPUT)

    records = []

    seen = set()

    total = 0
    kept = 0
    duplicate = 0
    empty = 0

    with FINLLM_INPUT.open(
        "r",
        encoding="utf-8"
    ) as f:

        for line in f:

            line = line.strip()

            if not line:
                continue

            total += 1

            record = json.loads(line)

            # Find the main text field.
            text = ""

            for candidate in [
                "text",
                "content",
                "article",
                "body",
                "description",
            ]:
                if candidate in record and record[candidate]:
                    text = normalize_text(
                        record[candidate]
                    )
                    if text:
                        break

            if not valid_text(text):
                empty += 1
                continue

            key = text.casefold()

            if key in seen:
                duplicate += 1
                continue

            seen.add(key)

            cleaned = {
                "source": "finllm-india",
                "text": text,
            }

            # Preserve useful metadata if available.
            for field in [
                "title",
                "company",
                "ticker",
                "exchange",
                "date",
                "source",
                "source_url",
            ]:
                if field in record and record[field] not in [
                    None,
                    "",
                ]:
                    cleaned[field] = record[field]

            records.append(cleaned)
            kept += 1

    write_jsonl(
        FINLLM_OUTPUT,
        records
    )

    print("Total records :", total)
    print("Kept          :", kept)
    print("Duplicates    :", duplicate)
    print("Empty/invalid :", empty)
    print("Output        :", FINLLM_OUTPUT)

    return records


def clean_news():
    print("\n" + "=" * 80)
    print("CLEANING INDIAN FINANCIAL NEWS")
    print("=" * 80)

    if not NEWS_INPUT.exists():
        raise FileNotFoundError(NEWS_INPUT)

    records = []

    seen = set()

    total = 0
    kept = 0
    duplicate = 0
    empty = 0

    with NEWS_INPUT.open(
        "r",
        encoding="utf-8"
    ) as f:

        for line in f:

            line = line.strip()

            if not line:
                continue

            total += 1

            record = json.loads(line)

            content = normalize_text(
                record.get("Content", "")
            )

            summary = normalize_text(
                record.get("Summary", "")
            )

            if not valid_text(content):
                empty += 1
                continue

            # Use article content as the primary identity.
            key = content.casefold()

            if key in seen:
                duplicate += 1
                continue

            seen.add(key)

            cleaned = {
                "source": "Indian_Financial_News",
                "text": content,
            }

            if summary:
                cleaned["summary"] = summary

            if record.get("Sentiment"):
                cleaned["sentiment"] = record[
                    "Sentiment"
                ]

            if record.get("URL"):
                cleaned["url"] = record[
                    "URL"
                ]

            records.append(cleaned)
            kept += 1

    write_jsonl(
        NEWS_OUTPUT,
        records
    )

    print("Total records :", total)
    print("Kept          :", kept)
    print("Duplicates    :", duplicate)
    print("Empty/invalid :", empty)
    print("Output        :", NEWS_OUTPUT)

    return records


def main():

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    finllm_records = clean_finllm()
    news_records = clean_news()

    combined = (
        finllm_records
        + news_records
    )

    write_jsonl(
        COMBINED_OUTPUT,
        combined
    )

    print("\n" + "=" * 80)
    print("EXTERNAL DATA CLEANING COMPLETE")
    print("=" * 80)

    print(
        "FinLLM cleaned      :",
        len(finllm_records)
    )

    print(
        "News cleaned        :",
        len(news_records)
    )

    print(
        "Combined domain     :",
        len(combined)
    )

    print(
        "Combined output     :",
        COMBINED_OUTPUT
    )

    print("=" * 80)


if __name__ == "__main__":
    main()