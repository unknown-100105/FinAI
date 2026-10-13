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


DB_PATH = ROOT / "data" / "rag" / "finai_rag.db"
OUT_DIR = Path(
    os.getenv(
        "FINAI_RAG_OUT_DIR",
        str(ROOT / "data" / "rag" / "embeddings"),
    )
).expanduser()
if not OUT_DIR.is_absolute():
    OUT_DIR = ROOT / OUT_DIR

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


def validate_resume_state(
    *,
    vector_count: int,
    document_ids: list[int],
    checkpoint: dict,
    checkpoint_exists: bool,
) -> tuple[int, int]:
    """Validate vector/ID/checkpoint alignment and recover a stale checkpoint."""
    if vector_count != len(document_ids):
        raise ValueError(
            "FAISS vector count does not match the document ID map: "
            f"{vector_count} vectors vs {len(document_ids)} IDs. "
            "Back up the current artifacts and rebuild the index."
        )

    if any(left >= right for left, right in zip(document_ids, document_ids[1:])):
        raise ValueError(
            "Document IDs must be strictly increasing and unique; refusing to append "
            "vectors to a potentially corrupted index."
        )

    latest_id = document_ids[-1] if document_ids else 0
    if not checkpoint_exists:
        # This can happen if the process stopped after saving the index/ID map but
        # before writing the checkpoint. The aligned ID map is the recovery source.
        return latest_id, len(document_ids)

    checkpoint_model = checkpoint.get("model_id")
    if checkpoint_model and checkpoint_model != MODEL_ID:
        raise ValueError(
            f"Checkpoint model '{checkpoint_model}' does not match index builder "
            f"model '{MODEL_ID}'. Rebuild with one embedding model per index."
        )

    checkpoint_count = int(checkpoint.get("indexed_count", 0))
    checkpoint_last_id = int(checkpoint.get("last_id", 0))
    if checkpoint_count < 0 or checkpoint_count > len(document_ids):
        raise ValueError(
            "Checkpoint count is inconsistent with the saved vector/ID files."
        )

    expected_checkpoint_id = (
        document_ids[checkpoint_count - 1] if checkpoint_count else 0
    )
    if checkpoint_last_id != expected_checkpoint_id:
        raise ValueError(
            "Checkpoint last_id does not match the ID map at indexed_count; "
            "refusing to continue with ambiguous index state."
        )

    # If the index and ID map were saved but the checkpoint write was interrupted,
    # the verified ID map may be ahead. Resume after its last ID to avoid duplicates.
    return latest_id, len(document_ids)


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

    checkpoint_exists = CHECKPOINT_PATH.exists()
    checkpoint = load_checkpoint()

    print("MODEL:", MODEL_ID)
    print("MAX SEQ LENGTH:", MAX_SEQ_LENGTH)
    print("BATCH SIZE:", BATCH_SIZE)
    print("MAX DOCUMENTS:", MAX_DOCUMENTS or "ALL")
    print("DATABASE:", DB_PATH)
    print("OUTPUT:", OUT_DIR)

    print("\nLoading embedding model...")
    configured_device = os.getenv("FINAI_RAG_DEVICE", "").strip() or None
    adapter = QwenEmbeddingAdapter(
        device=configured_device,
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

    last_id, indexed_count = validate_resume_state(
        vector_count=int(index.ntotal),
        document_ids=document_ids,
        checkpoint=checkpoint,
        checkpoint_exists=checkpoint_exists,
    )
    if not checkpoint_exists and indexed_count:
        print(
            "WARNING: checkpoint.json is missing; recovered resume position "
            "from the aligned FAISS index and document ID map."
        )
    print("RESUME LAST ID:", last_id)
    print("RESUME COUNT:", indexed_count)

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
