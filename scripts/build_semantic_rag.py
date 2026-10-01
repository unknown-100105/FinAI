import json
from pathlib import Path

import numpy as np
from sentence_transformers import SentenceTransformer


ROOT = Path(__file__).resolve().parent.parent

INPUT_FILES = [
    ROOT
    / "data"
    / "domain_chunks"
    / "finllm_india_clean_chunks.jsonl",

    ROOT
    / "data"
    / "domain_chunks"
    / "indian_financial_news_clean_chunks.jsonl",
]

OUTPUT_DIR = ROOT / "data" / "rag"

EMBEDDINGS_FILE = OUTPUT_DIR / "embeddings.npy"
METADATA_FILE = OUTPUT_DIR / "metadata.jsonl"

MODEL_NAME = "intfloat/multilingual-e5-small"

BATCH_SIZE = 32


def load_chunks():

    records = []

    for input_file in INPUT_FILES:

        print("=" * 70)
        print("Reading:")
        print(input_file)
        print("=" * 70)

        with input_file.open(
            "r",
            encoding="utf-8"
        ) as f:

            for line in f:

                line = line.strip()

                if not line:
                    continue

                record = json.loads(line)

                text = str(
                    record.get("text", "")
                ).strip()

                if not text:
                    continue

                records.append(record)

                if len(records) % 25000 == 0:

                    print(
                        "Loaded chunks:",
                        len(records)
                    )

    return records


def main():

    print("=" * 70)
    print("FINAI SEMANTIC RAG BUILDER")
    print("=" * 70)

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    print("\nLoading documents...")

    records = load_chunks()

    print(
        "\nTotal chunks:",
        len(records)
    )

    print(
        "\nLoading multilingual embedding model..."
    )

    # IMPORTANT:
    # CPU only, so this will not compete with
    # the running FinAI training process.
    model = SentenceTransformer(
        MODEL_NAME,
        device="cpu",
    )

    texts = [
        "passage: " + record["text"]
        for record in records
    ]

    all_embeddings = []

    print("\nGenerating embeddings...")

    for start in range(
        0,
        len(texts),
        BATCH_SIZE
    ):

        batch = texts[
            start:start + BATCH_SIZE
        ]

        embeddings = model.encode(
            batch,
            batch_size=BATCH_SIZE,
            normalize_embeddings=True,
            convert_to_numpy=True,
            show_progress_bar=False,
        )

        all_embeddings.append(
            embeddings.astype(
                np.float32
            )
        )

        completed = min(
            start + BATCH_SIZE,
            len(texts)
        )

        if completed % 5000 < BATCH_SIZE:

            print(
                f"Embedded {completed:,} / "
                f"{len(texts):,}"
            )

    embeddings = np.vstack(
        all_embeddings
    )

    print(
        "\nEmbedding shape:",
        embeddings.shape
    )

    print("\nSaving embeddings...")

    np.save(
        EMBEDDINGS_FILE,
        embeddings,
    )

    print("Saving metadata...")

    with METADATA_FILE.open(
        "w",
        encoding="utf-8"
    ) as f:

        for record in records:

            f.write(
                json.dumps(
                    record,
                    ensure_ascii=False,
                )
                + "\n"
            )

    print("\n" + "=" * 70)
    print("SEMANTIC RAG BUILD COMPLETE")
    print("=" * 70)

    print(
        "Vectors:",
        embeddings.shape[0]
    )

    print(
        "Dimensions:",
        embeddings.shape[1]
    )

    print(
        "Embeddings:",
        EMBEDDINGS_FILE
    )

    print(
        "Metadata:",
        METADATA_FILE
    )

    print("=" * 70)


if __name__ == "__main__":
    main()