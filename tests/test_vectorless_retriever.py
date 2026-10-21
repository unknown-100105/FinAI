import sqlite3
from pathlib import Path

import pytest

from rag.vectorless_retriever import VectorlessRetriever


def build_db(path: Path) -> Path:
    with sqlite3.connect(path) as con:
        con.execute(
            """CREATE TABLE documents (
                id INTEGER PRIMARY KEY, title TEXT, source TEXT, date TEXT, text TEXT
            )"""
        )
        con.executemany(
            "INSERT INTO documents(id,title,source,date,text) VALUES(?,?,?,?,?)",
            [
                (1, "UPI disputes", "RBI", "2025-01-01", "UPI payment dispute complaint rules"),
                (2, "Home loans", "Bank", "2025-02-01", "Home loan interest and repayment"),
                (3, "Card safety", "Bank", "2025-03-01", "Credit card transaction security"),
            ],
        )
        con.execute(
            "CREATE VIRTUAL TABLE documents_fts USING fts5(text, content='documents', content_rowid='id')"
        )
        con.execute("INSERT INTO documents_fts(rowid,text) SELECT id,text FROM documents")
    return path


def test_vectorless_retrieval_uses_fts5_without_embedding_assets(tmp_path):
    db = build_db(tmp_path / "finai.db")
    docs = VectorlessRetriever(db).retrieve("UPI dispute rules", top_k=2)
    assert docs
    assert docs[0].document_id == 1
    assert docs[0].source == "RBI"
    assert docs[0].score >= 0


def test_vectorless_query_quotes_fts_syntax_and_handles_unicode():
    built = VectorlessRetriever.build_query("RBI's UPI? भुगतान!")
    assert "?" not in built
    assert '"RBI"' in built
    assert '"भुगतान"' in built


@pytest.mark.parametrize("query,top_k", [("", 3), ("   ", 3), ("valid", 0), ("valid", 21), ("valid", True)])
def test_vectorless_retrieval_rejects_invalid_inputs(tmp_path, query, top_k):
    db = build_db(tmp_path / "finai.db")
    with pytest.raises(ValueError):
        VectorlessRetriever(db).retrieve(query, top_k=top_k)


def test_vectorless_missing_database_fails_clearly(tmp_path):
    with pytest.raises(FileNotFoundError):
        VectorlessRetriever(tmp_path / "missing.db").retrieve("RBI", top_k=3)


def test_vectorless_retrieval_empty_query_terms_returns_empty(tmp_path):
    db = build_db(tmp_path / "finai.db")
    assert VectorlessRetriever(db).retrieve("??? !!!", top_k=3) == []
