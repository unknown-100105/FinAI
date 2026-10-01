from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

import faiss
import numpy as np


@dataclass(frozen=True)
class RetrievedDocument:
    document_id: int
    title: str
    source: str
    date: str
    text: str
    lexical_score: Optional[float] = None
    semantic_score: Optional[float] = None
    fused_score: float = 0.0


class HybridRetriever:

    def __init__(
        self,
        db_path: str | Path,
        faiss_index_path: str | Path,
        document_ids_path: str | Path,
        embedding_adapter=None,
        rrf_k: int = 60,
    ):
        self.db_path = Path(db_path)
        self.faiss_index_path = Path(
            faiss_index_path
        )
        self.document_ids_path = Path(
            document_ids_path
        )

        self.embedding_adapter = embedding_adapter

        if rrf_k <= 0:
            raise ValueError(
                "rrf_k must be positive."
            )

        self.rrf_k = rrf_k

        self._index = None
        self._document_ids = None

    def _load_faiss(self):
        if self._index is None:
            if not self.faiss_index_path.exists():
                raise FileNotFoundError(
                    f"FAISS index not found: "
                    f"{self.faiss_index_path}"
                )

            if not self.document_ids_path.exists():
                raise FileNotFoundError(
                    f"Document ID map not found: "
                    f"{self.document_ids_path}"
                )

            self._index = faiss.read_index(
                str(self.faiss_index_path)
            )

            self._document_ids = np.load(
                self.document_ids_path
            ).astype(np.int64)

            if (
                self._index.ntotal
                != len(self._document_ids)
            ):
                raise ValueError(
                    "FAISS vector count does not match "
                    "document ID count."
                )

        return self._index, self._document_ids

    def _fts_search(
        self,
        query: str,
        top_k: int,
    ) -> List[dict]:

        query = query.strip()

        if not query:
            return []

        results = []

        with sqlite3.connect(
            str(self.db_path)
        ) as con:

            rows = con.execute(
                """
                SELECT
                    d.id,
                    d.title,
                    d.source,
                    d.date,
                    d.text,
                    bm25(documents_fts) AS score
                FROM documents_fts
                JOIN documents d
                  ON d.id = documents_fts.rowid
                WHERE documents_fts MATCH ?
                ORDER BY bm25(documents_fts)
                LIMIT ?
                """,
                (
                    query,
                    top_k,
                ),
            ).fetchall()

        for row in rows:
            # SQLite FTS5 BM25 is conventionally negative;
            # negate it so larger values mean better lexical match.
            results.append(
                {
                    "document_id": int(row[0]),
                    "title": row[1] or "",
                    "source": row[2] or "",
                    "date": row[3] or "",
                    "text": row[4] or "",
                    "score": float(-row[5]),
                }
            )

        return results

    def _semantic_search(
        self,
        query: str,
        top_k: int,
    ) -> List[dict]:

        if self.embedding_adapter is None:
            raise RuntimeError(
                "An embedding_adapter is required "
                "for semantic retrieval."
            )

        index, document_ids = (
            self._load_faiss()
        )

        query_vector = (
            self.embedding_adapter.embed(
                [query],
                is_query=True,
                batch_size=1,
                normalize_embeddings=True,
            )
        )

        query_vector = np.asarray(
            query_vector,
            dtype=np.float32,
        )

        scores, positions = index.search(
            query_vector,
            top_k,
        )

        results = []

        for score, position in zip(
            scores[0],
            positions[0],
        ):
            if position < 0:
                continue

            document_id = int(
                document_ids[position]
            )

            results.append(
                {
                    "document_id": document_id,
                    "score": float(score),
                }
            )

        if not results:
            return []

        ids = [
            item["document_id"]
            for item in results
        ]

        placeholders = ",".join(
            "?" for _ in ids
        )

        with sqlite3.connect(
            str(self.db_path)
        ) as con:

            rows = con.execute(
                f"""
                SELECT
                    id,
                    title,
                    source,
                    date,
                    text
                FROM documents
                WHERE id IN ({placeholders})
                """,
                ids,
            ).fetchall()

        metadata = {
            int(row[0]): {
                "title": row[1] or "",
                "source": row[2] or "",
                "date": row[3] or "",
                "text": row[4] or "",
            }
            for row in rows
        }

        enriched = []

        for item in results:
            doc = metadata.get(
                item["document_id"]
            )

            if doc is None:
                continue

            enriched.append(
                {
                    "document_id": item[
                        "document_id"
                    ],
                    **doc,
                    "score": item["score"],
                }
            )

        return enriched

    def retrieve(
        self,
        query: str,
        top_k: int = 5,
        candidate_k: Optional[int] = None,
    ) -> List[RetrievedDocument]:

        if top_k <= 0:
            raise ValueError(
                "top_k must be positive."
            )

        if candidate_k is None:
            candidate_k = max(
                top_k * 4,
                20,
            )

        if candidate_k < top_k:
            candidate_k = top_k

        lexical = self._fts_search(
            query,
            candidate_k,
        )

        semantic = self._semantic_search(
            query,
            candidate_k,
        )

        merged = {}

        for rank, item in enumerate(
            lexical,
            start=1,
        ):
            doc_id = item["document_id"]

            entry = merged.setdefault(
                doc_id,
                {
                    "document_id": doc_id,
                    "title": item["title"],
                    "source": item["source"],
                    "date": item["date"],
                    "text": item["text"],
                    "lexical_score": None,
                    "semantic_score": None,
                    "fused_score": 0.0,
                },
            )

            entry["lexical_score"] = (
                item["score"]
            )

            entry["fused_score"] += (
                1.0
                / (self.rrf_k + rank)
            )

        for rank, item in enumerate(
            semantic,
            start=1,
        ):
            doc_id = item["document_id"]

            entry = merged.setdefault(
                doc_id,
                {
                    "document_id": doc_id,
                    "title": "",
                    "source": "",
                    "date": "",
                    "text": "",
                    "lexical_score": None,
                    "semantic_score": None,
                    "fused_score": 0.0,
                },
            )

            entry["semantic_score"] = (
                item["score"]
            )

            entry["fused_score"] += (
                1.0
                / (self.rrf_k + rank)
            )

            if not entry["text"]:
                entry.update(
                    {
                        "title": item["title"],
                        "source": item["source"],
                        "date": item["date"],
                        "text": item["text"],
                    }
                )

        ranked = sorted(
            merged.values(),
            key=lambda x: x["fused_score"],
            reverse=True,
        )

        return [
            RetrievedDocument(
                document_id=item["document_id"],
                title=item["title"],
                source=item["source"],
                date=item["date"],
                text=item["text"],
                lexical_score=item[
                    "lexical_score"
                ],
                semantic_score=item[
                    "semantic_score"
                ],
                fused_score=item[
                    "fused_score"
                ],
            )
            for item in ranked[:top_k]
        ]
