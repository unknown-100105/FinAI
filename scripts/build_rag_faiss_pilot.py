from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import json
import time
import sqlite3
from pathlib import Path

import faiss
import numpy as np

from llm.qwen_embedding_adapter import QwenEmbeddingAdapter


DB_PATH = Path("data/rag/finai_rag.db")
OUT_DIR = Path("data/rag/embeddings_pilot")

INDEX_PATH = OUT_DIR / "finai_rag_pilot.faiss"
IDS_PATH = OUT_DIR / "document_ids.npy"
CHECKPOINT_PATH = OUT_DIR / "checkpoint.json"

TARGET_DOCUMENTS = 5000
BATCH_SIZE = 32
SAVE_EVERY = 1000


def main() -> None:

    OUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    adapter = QwenEmbeddingAdapter(
        device="cuda"
    )

    print("MODEL:", adapter.model_id)
    print("TARGET DOCUMENTS:", TARGET_DOCUMENTS)
    print("BATCH SIZE:", BATCH_SIZE)

    dimension = adapter.embedding_dimension()

    print("EMBEDDING DIMENSION:", dimension)

    index = faiss.IndexFlatIP(
        dimension
    )

    document_ids = []

    con = sqlite3.connect(
        str(DB_PATH)
    )

    cur = con.cursor()

    last_id = 0
    indexed_count = 0
    last_saved_count = 0

    start_time = time.perf_counter()

    try:
        while indexed_count < TARGET_DOCUMENTS:

            remaining = (
                TARGET_DOCUMENTS
                - indexed_count
            )

            limit = min(
                BATCH_SIZE,
                remaining,
            )

            rows = cur.execute(
                """
                SELECT id, text
                FROM documents
                WHERE id > ?
                  AND text IS NOT NULL
                  AND text != ''
                ORDER BY id
                LIMIT ?
                """,
                (
                    last_id,
                    limit,
                ),
            ).fetchall()

            if not rows:
                break

            ids = [
                int(row[0])
                for row in rows
            ]

            texts = [
                row[1]
                for row in rows
            ]

            embeddings = adapter.embed(
                texts,
                is_query=False,
                batch_size=BATCH_SIZE,
                normalize_embeddings=True,
            )

            index.add(
                embeddings
            )

            document_ids.extend(
                ids
            )

            last_id = ids[-1]
            indexed_count += len(rows)

            if (
                indexed_count - last_saved_count
                >= SAVE_EVERY
                or indexed_count
                >= TARGET_DOCUMENTS
            ):

                faiss.write_index(
                    index,
                    str(INDEX_PATH),
                )

                np.save(
                    IDS_PATH,
                    np.asarray(
                        document_ids,
                        dtype=np.int64,
                    ),
                )

                checkpoint = {
                    "model_id": adapter.model_id,
                    "target_documents": TARGET_DOCUMENTS,
                    "indexed_count": indexed_count,
                    "last_id": last_id,
                    "dimension": dimension,
                }

                CHECKPOINT_PATH.write_text(
                    json.dumps(
                        checkpoint,
                        indent=2,
                    ),
                    encoding="utf-8",
                )

                elapsed = (
                    time.perf_counter()
                    - start_time
                )

                rate = (
                    indexed_count
                    / elapsed
                    if elapsed > 0
                    else 0
                )

                print(
                    f"CHECKPOINT: "
                    f"{indexed_count}/{TARGET_DOCUMENTS} | "
                    f"{rate:.2f} docs/sec"
                )

                last_saved_count = indexed_count

    finally:
        con.close()

    elapsed = (
        time.perf_counter()
        - start_time
    )

    rate = (
        indexed_count / elapsed
        if elapsed > 0
        else 0
    )

    print("\nPILOT COMPLETE")
    print("DOCUMENTS:", indexed_count)
    print("VECTORS:", index.ntotal)
    print("DIMENSION:", dimension)
    print("ELAPSED_SECONDS:", round(elapsed, 2))
    print("DOCS_PER_SECOND:", round(rate, 2))
    print(
        "EST_FULL_HOURS:",
        round(
            332385 / rate / 3600,
            2,
        )
        if rate > 0
        else "N/A",
    )
    print("INDEX:", INDEX_PATH)
    print("IDS:", IDS_PATH)
    print("CHECKPOINT:", CHECKPOINT_PATH)


if __name__ == "__main__":
    main()
