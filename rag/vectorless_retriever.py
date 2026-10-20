"""Embedding-free retrieval using the repository's existing SQLite FTS5 index.

This retriever is intentionally lexical: it does not load embeddings, FAISS,
or an LLM. Scores are retrieval scores, not probabilities or factual confidence.
"""
from __future__ import annotations

import re
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import List


@dataclass(frozen=True)
class VectorlessDocument:
    document_id: int
    title: str
    source: str
    date: str
    text: str
    score: float


class VectorlessRetriever:
    """Search indexed document chunks using SQLite FTS5/BM25 only."""

    def __init__(self, db_path: str | Path):
        self.db_path = Path(db_path)

    @staticmethod
    def build_query(query: str) -> str:
        """Turn user text into a safe OR query of individually quoted terms."""
        tokens = re.findall(r"\\w+", query, flags=re.UNICODE)
        if not tokens:
            return ""
        return " OR ".join('"' + token.replace('"', '""') + '"' for token in tokens)

    def retrieve(self, query: str, top_k: int = 5) -> List[VectorlessDocument]:
        if not isinstance(query, str) or not query.strip():
            raise ValueError("query must contain at least one non-whitespace character")
        if len(query) > 1000:
            raise ValueError("query must be at most 1000 characters")
        if not isinstance(top_k, int) or isinstance(top_k, bool) or not 1 <= top_k <= 20:
            raise ValueError("top_k must be between 1 and 20")
        if not self.db_path.is_file():
            raise FileNotFoundError(f"FinAI RAG database not found: {self.db_path}")

        fts_query = self.build_query(query)
        if not fts_query:
            return []

        try:
            with sqlite3.connect(str(self.db_path), timeout=5.0) as con:
                rows = con.execute(
                    """
                    SELECT d.id, d.title, d.source, d.date, d.text,
                           bm25(documents_fts) AS score
                    FROM documents_fts
                    JOIN documents d ON d.id = documents_fts.rowid
                    WHERE documents_fts MATCH ?
                    ORDER BY bm25(documents_fts) ASC
                    LIMIT ?
                    """,
                    (fts_query, top_k),
                ).fetchall()
        except sqlite3.OperationalError as exc:
            raise RuntimeError(
                "Unable to query the FTS5 index. Rebuild data/rag/finai_rag.db "
                "with scripts/build_rag_index.py if the index is missing or stale."
            ) from exc

        return [
            VectorlessDocument(
                document_id=int(row[0]),
                title=row[1] or "",
                source=row[2] or "",
                date=row[3] or "",
                text=row[4] or "",
                # FTS5 BM25 is usually negative; invert it for an intuitive
                # higher-is-better display. It is not a calibrated probability.
                score=float(-row[5]),
            )
            for row in rows
        ]
