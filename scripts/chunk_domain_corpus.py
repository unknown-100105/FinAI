import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent

INPUT_FILES = [
    ROOT / "data" / "domain" / "finllm_india_clean.jsonl",
    ROOT / "data" / "domain" / "indian_financial_news_clean.jsonl",
]

OUTPUT_DIR = ROOT / "data" / "domain_chunks"

CHUNK_SIZE = 1800
OVERLAP = 250


def normalize_text(text):
    if text is None:
        return ""

    text = str(text)
    text = re.sub(r"\s+", " ", text)

    return text.strip()


def chunk_text(text):
    text = normalize_text(text)

    if not text:
        return []

    chunks = []

    start = 0
    length = len(text)

    while start < length:

        end = min(
            start + CHUNK_SIZE,
            length
        )

        chunk = text[start:end].strip()

        if chunk:
            chunks.append(chunk)

        if end >= length:
            break

        start = end - OVERLAP

    return chunks


def process_file(input_file):

    print("\n" + "=" * 80)
    print("PROCESSING")
    print("=" * 80)
    print(input_file)

    output_file = (
        OUTPUT_DIR /
        f"{input_file.stem}_chunks.jsonl"
    )

    total_documents = 0
    total_chunks = 0

    with input_file.open(
        "r",
        encoding="utf-8"
    ) as source, output_file.open(
        "w",
        encoding="utf-8"
    ) as destination:

        for line in source:

            line = line.strip()

            if not line:
                continue

            record = json.loads(line)

            text = record.get(
                "text",
                ""
            )

            chunks = chunk_text(text)

            total_documents += 1

            for chunk_index, chunk in enumerate(
                chunks
            ):

                output_record = {
                    "source": record.get(
                        "source",
                        input_file.stem
                    ),

                    "document_id":
                        total_documents,

                    "chunk_id":
                        chunk_index,

                    "text": chunk,
                }

                # Preserve useful metadata.
                for field in [
                    "title",
                    "company",
                    "ticker",
                    "exchange",
                    "date",
                    "source_url",
                    "url",
                    "summary",
                    "sentiment",
                ]:

                    if field in record:

                        output_record[field] = (
                            record[field]
                        )

                destination.write(
                    json.dumps(
                        output_record,
                        ensure_ascii=False,
                    )
                    + "\n"
                )

                total_chunks += 1

            if total_documents % 5000 == 0:

                print(
                    "Processed documents:",
                    total_documents,
                    "| chunks:",
                    total_chunks
                )

    print("\nCompleted")
    print("Documents:", total_documents)
    print("Chunks   :", total_chunks)
    print("Output   :", output_file)

    return total_documents, total_chunks


def main():

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    print("=" * 80)
    print("FINAI DOMAIN CORPUS CHUNKING")
    print("=" * 80)

    total_documents = 0
    total_chunks = 0

    for input_file in INPUT_FILES:

        documents, chunks = process_file(
            input_file
        )

        total_documents += documents
        total_chunks += chunks

    print("\n" + "=" * 80)
    print("DOMAIN CHUNKING COMPLETE")
    print("=" * 80)

    print(
        "Total documents:",
        total_documents
    )

    print(
        "Total chunks:",
        total_chunks
    )

    print(
        "Output directory:",
        OUTPUT_DIR
    )

    print("=" * 80)


if __name__ == "__main__":
    main()