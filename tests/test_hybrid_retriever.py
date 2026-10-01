import sqlite3
from pathlib import Path

import faiss
import numpy as np

from rag.hybrid_retriever import HybridRetriever


class FakeEmbeddingAdapter:

    def embed(self, texts, **kwargs):
        assert len(texts) == 1
        return np.array(
            [[1.0, 0.0]],
            dtype=np.float32,
        )


def build_test_database(tmp_path: Path):
    db_path = tmp_path / "test.db"

    con = sqlite3.connect(db_path)

    con.execute(
        """
        CREATE TABLE documents (
            id INTEGER PRIMARY KEY,
            source TEXT,
            document_id TEXT,
            chunk_id TEXT,
            title TEXT,
            company TEXT,
            ticker TEXT,
            exchange TEXT,
            date TEXT,
            url TEXT,
            text TEXT,
            sentiment TEXT,
            summary TEXT
        )
        """
    )

    rows = [
        (
            1,
            "test",
            "doc1",
            "0",
            "Home Loan Interest",
            "",
            "",
            "",
            "2025-01-01",
            "",
            "Home loan interest rates affect monthly repayment.",
            "",
            "",
        ),
        (
            2,
            "test",
            "doc2",
            "0",
            "UPI Fraud",
            "",
            "",
            "",
            "2025-01-02",
            "",
            "UPI fraud detection and transaction security.",
            "",
            "",
        ),
        (
            3,
            "test",
            "doc3",
            "0",
            "Credit Card",
            "",
            "",
            "",
            "2025-01-03",
            "",
            "Credit card payment processing information.",
            "",
            "",
        ),
    ]

    con.executemany(
        """
        INSERT INTO documents VALUES (
            ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
        )
        """,
        rows,
    )

    con.execute(
        """
        CREATE VIRTUAL TABLE documents_fts
        USING fts5(
            text,
            content='documents',
            content_rowid='id'
        )
        """
    )

    con.execute(
        """
        INSERT INTO documents_fts(
            rowid,
            text
        )
        SELECT
            id,
            text
        FROM documents
        """
    )

    con.commit()
    con.close()

    return db_path


def build_test_faiss(tmp_path: Path):
    index_path = tmp_path / "test.faiss"
    ids_path = tmp_path / "ids.npy"

    vectors = np.array(
        [
            [1.0, 0.0],
            [0.0, 1.0],
            [0.7, 0.7],
        ],
        dtype=np.float32,
    )

    index = faiss.IndexFlatIP(2)
    index.add(vectors)

    faiss.write_index(
        index,
        str(index_path),
    )

    np.save(
        ids_path,
        np.array(
            [1, 2, 3],
            dtype=np.int64,
        ),
    )

    return index_path, ids_path


def test_fts_query_handles_punctuation():
    query = HybridRetriever._build_fts5_query(
        "What did RBI require payment data?"
    )

    assert "?" not in query
    assert '"RBI"' in query
    assert '"data"' in query


def test_fts_search(tmp_path):

    db_path = build_test_database(
        tmp_path
    )

    index_path, ids_path = build_test_faiss(
        tmp_path
    )

    retriever = HybridRetriever(
        db_path=db_path,
        faiss_index_path=index_path,
        document_ids_path=ids_path,
        embedding_adapter=FakeEmbeddingAdapter(),
    )

    results = retriever._fts_search(
        "loan interest",
        top_k=3,
    )

    assert results
    assert results[0]["document_id"] == 1
    assert "Home Loan Interest" in results[0]["title"]


def test_semantic_search(tmp_path):

    db_path = build_test_database(
        tmp_path
    )

    index_path, ids_path = build_test_faiss(
        tmp_path
    )

    retriever = HybridRetriever(
        db_path=db_path,
        faiss_index_path=index_path,
        document_ids_path=ids_path,
        embedding_adapter=FakeEmbeddingAdapter(),
    )

    results = retriever._semantic_search(
        "loan repayment",
        top_k=3,
    )

    assert results
    assert results[0]["document_id"] == 1
    assert results[0]["score"] > 0.9


def test_hybrid_retrieval_merges_results(tmp_path):

    db_path = build_test_database(
        tmp_path
    )

    index_path, ids_path = build_test_faiss(
        tmp_path
    )

    retriever = HybridRetriever(
        db_path=db_path,
        faiss_index_path=index_path,
        document_ids_path=ids_path,
        embedding_adapter=FakeEmbeddingAdapter(),
    )

    results = retriever.retrieve(
        "loan interest",
        top_k=3,
        candidate_k=3,
    )

    assert len(results) == 3

    ids = [
        result.document_id
        for result in results
    ]

    assert 1 in ids

    for result in results:
        assert result.fused_score > 0


def test_duplicate_documents_are_merged(tmp_path):

    db_path = build_test_database(
        tmp_path
    )

    index_path, ids_path = build_test_faiss(
        tmp_path
    )

    retriever = HybridRetriever(
        db_path=db_path,
        faiss_index_path=index_path,
        document_ids_path=ids_path,
        embedding_adapter=FakeEmbeddingAdapter(),
    )

    results = retriever.retrieve(
        "loan interest",
        top_k=3,
        candidate_k=3,
    )

    ids = [
        result.document_id
        for result in results
    ]

    assert len(ids) == len(set(ids))


def test_missing_faiss_index_fails(tmp_path):

    db_path = build_test_database(
        tmp_path
    )

    retriever = HybridRetriever(
        db_path=db_path,
        faiss_index_path=tmp_path / "missing.faiss",
        document_ids_path=tmp_path / "missing.npy",
        embedding_adapter=FakeEmbeddingAdapter(),
    )

    import pytest

    with pytest.raises(FileNotFoundError):
        retriever._semantic_search(
            "loan",
            top_k=3,
        )


def test_faiss_id_count_mismatch_fails(tmp_path):

    db_path = build_test_database(
        tmp_path
    )

    index_path, ids_path = build_test_faiss(
        tmp_path
    )

    np.save(
        ids_path,
        np.array(
            [1, 2],
            dtype=np.int64,
        ),
    )

    retriever = HybridRetriever(
        db_path=db_path,
        faiss_index_path=index_path,
        document_ids_path=ids_path,
        embedding_adapter=FakeEmbeddingAdapter(),
    )

    import pytest

    with pytest.raises(ValueError):
        retriever._semantic_search(
            "loan",
            top_k=3,
        )
