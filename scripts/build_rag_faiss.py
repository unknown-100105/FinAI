from __future__ import annotations

import json
import os
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import faiss
import numpy as np
from llm.qwen_embedding_adapter import QwenEmbeddingAdapter


DB_PATH = Path("data/rag/finai_rag.db")
OUT_DIR = Path(
    os.getenv(
        "FINAI_RAG_OUT_DIR",
        "data/rag/embeddings",
    )
)

INDEX_PATH = OUT_DIR / "finai_rag.faiss"
IDS_PATH = OUT_DIR / "document_ids.npy"
CHECKPOINT_PATH = OUT_DIR / "checkpoint.json"

MODEL_ID = "Qwen/Qwen3-Embedding-0.6B"

BATCH_SIZE = 32
MAX_SEQ_LENGTH = 640
SAVE_EVERY = 5000

MAX_DOCUMENTS = int(
    os.getenv(
        "FINAI_RAG_MAX_DOCUMENTS",
        "0",
    )
)


def load_checkpoint() -> dict:
    if not CHECKPOINT_PATH.exists():
        return {
            "last_id": 0,
            "indexed_count": 0,
        }

    return json.loads(
        CHECKPOINT_PATH.read_text(encoding="utf-8")
    )


def save_checkpoint(
    last_id: int,
    indexed_count: int,
) -> None:
    CHECKPOINT_PATH.write_text(
        json.dumps(
            {
                "model_id": MODEL_ID,
                "last_id": last_id,
                "indexed_count": indexed_count,
                "batch_size": BATCH_SIZE,
                "max_seq_length": MAX_SEQ_LENGTH,
            },
            indent=2,
        ),
        encoding="utf-8",
    )


def main() -> None:
    OUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    if not DB_PATH.exists():
        raise FileNotFoundError(
            f"RAG database not found: {DB_PATH}"
        )

    checkpoint = load_checkpoint()

    last_id = int(
        checkpoint.get("last_id", 0)
    )
    indexed_count = int(
        checkpoint.get("indexed_count", 0)
    )

    print("MODEL:", MODEL_ID)
    print("MAX SEQ LENGTH:", MAX_SEQ_LENGTH)
    print("BATCH SIZE:", BATCH_SIZE)
    print("MAX DOCUMENTS:", MAX_DOCUMENTS or "ALL")
    print("DATABASE:", DB_PATH)
    print("OUTPUT:", OUT_DIR)
    print("RESUME LAST ID:", last_id)
    print("RESUME COUNT:", indexed_count)

    print("\nLoading embedding model...")

    adapter = QwenEmbeddingAdapter(
        device="cuda",
        max_seq_length=MAX_SEQ_LENGTH,
    )

    dimension = adapter.embedding_dimension()

    if dimension is None:
        raise RuntimeError(
            "Could not determine embedding dimension."
        )

    print("EMBEDDING DIMENSION:", dimension)

    if INDEX_PATH.exists():
        print("Loading existing FAISS index...")
        index = faiss.read_index(
            str(INDEX_PATH)
        )
    else:
        print("Creating FAISS IndexFlatIP...")
        index = faiss.IndexFlatIP(
            dimension
        )

    if IDS_PATH.exists():
        document_ids = np.load(
            IDS_PATH
        ).astype(np.int64).tolist()
    else:
        document_ids = []

    con = sqlite3.connect(
        str(DB_PATH)
    )
    cur = con.cursor()

    last_saved_count = indexed_count

    try:
        while True:
            if MAX_DOCUMENTS > 0:
                remaining = (
                    MAX_DOCUMENTS
                    - indexed_count
                )

                if remaining <= 0:
                    break

                limit = min(
                    BATCH_SIZE,
                    remaining,
                )
            else:
                limit = BATCH_SIZE

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

            index.add(embeddings)

            document_ids.extend(ids)

            last_id = ids[-1]
            indexed_count += len(ids)

            if (
                indexed_count - last_saved_count
                >= SAVE_EVERY
                or len(rows) < BATCH_SIZE
                or (
                    MAX_DOCUMENTS > 0
                    and indexed_count
                    >= MAX_DOCUMENTS
                )
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

                save_checkpoint(
                    last_id,
                    indexed_count,
                )

                last_saved_count = indexed_count

                print(
                    f"CHECKPOINT: "
                    f"{indexed_count} documents | "
                    f"last_id={last_id}"
                )

    finally:
        con.close()

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

    save_checkpoint(
        last_id,
        indexed_count,
    )

    print("\nINDEXING COMPLETE")
    print("DOCUMENTS INDEXED:", indexed_count)
    print("FAISS VECTORS:", index.ntotal)
    print("DIMENSION:", dimension)
    print("INDEX:", INDEX_PATH)
    print("IDS:", IDS_PATH)
    print("CHECKPOINT:", CHECKPOINT_PATH)


if __name__ == "__main__":
    main()
