"""Contract tests for the experimental Retrieval Lab HTTP API."""
from types import SimpleNamespace

from fastapi.testclient import TestClient

from app.main import app
from app import retrieval_lab_api

client = TestClient(app)


def lexical_docs():
    return [
        SimpleNamespace(
            document_id=7,
            title="UPI complaint process",
            source="RBI",
            date="2025-01-01",
            text="Evidence excerpt",
            score=1.25,
        )
    ]


def hybrid_docs():
    return [
        SimpleNamespace(
            document_id=7,
            title="UPI complaint process",
            source="RBI",
            date="2025-01-01",
            text="Evidence excerpt",
            lexical_score=1.1,
            semantic_score=0.7,
            fused_score=0.03,
        )
    ]


def test_compare_mode_returns_independent_vectorless_and_hybrid_results(monkeypatch):
    monkeypatch.setattr(
        retrieval_lab_api,
        "_get_vectorless",
        lambda: SimpleNamespace(retrieve=lambda query, top_k: lexical_docs()),
    )
    monkeypatch.setattr(
        retrieval_lab_api,
        "_get_hybrid",
        lambda: SimpleNamespace(retrieve=lambda query, top_k: hybrid_docs()),
    )

    response = client.post(
        "/api/v1/retrieval-lab/search",
        json={"query": "UPI complaints", "mode": "compare", "top_k": 3},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["results_by_mode"]["vectorless"]["status"] == "available"
    assert body["results_by_mode"]["hybrid"]["status"] == "available"
    assert body["results_by_mode"]["vectorless"]["results"][0]["document_id"] == 7
    assert body["results_by_mode"]["vectorless"]["results"][0]["semantic_score"] is None
    assert body["results_by_mode"]["hybrid"]["results"][0]["fused_score"] == 0.03
    assert "not probabilities" in body["notice"]


def test_compare_mode_keeps_vectorless_results_when_hybrid_assets_missing(monkeypatch):
    monkeypatch.setattr(
        retrieval_lab_api,
        "_get_vectorless",
        lambda: SimpleNamespace(retrieve=lambda query, top_k: lexical_docs()),
    )

    def unavailable_hybrid():
        raise FileNotFoundError("internal path should not escape to response")

    monkeypatch.setattr(retrieval_lab_api, "_get_hybrid", unavailable_hybrid)

    response = client.post(
        "/api/v1/retrieval-lab/search",
        json={"query": "UPI", "mode": "compare", "top_k": 5},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["results_by_mode"]["vectorless"]["status"] == "available"
    assert body["results_by_mode"]["hybrid"]["status"] == "unavailable"
    assert "internal path" not in str(body)


def test_single_hybrid_mode_reports_unavailable_assets_as_503(monkeypatch):
    monkeypatch.setattr(
        retrieval_lab_api,
        "_get_hybrid",
        lambda: (_ for _ in ()).throw(FileNotFoundError("not public")),
    )

    response = client.post(
        "/api/v1/retrieval-lab/search",
        json={"query": "UPI", "mode": "hybrid"},
    )

    assert response.status_code == 503
    assert "not public" not in response.text


def test_retrieval_lab_validates_query_and_top_k():
    blank = client.post(
        "/api/v1/retrieval-lab/search",
        json={"query": "   ", "mode": "vectorless", "top_k": 5},
    )
    too_many = client.post(
        "/api/v1/retrieval-lab/search",
        json={"query": "UPI", "mode": "vectorless", "top_k": 11},
    )

    assert blank.status_code == 422
    assert too_many.status_code == 422

def test_compare_mode_does_not_create_a_missing_vectorless_database(monkeypatch, tmp_path):
    missing_db = tmp_path / "not-built-yet.db"
    monkeypatch.setattr(retrieval_lab_api, "DB_PATH", missing_db)
    monkeypatch.setattr(retrieval_lab_api, "FAISS_PATH", tmp_path / "missing.faiss")
    monkeypatch.setattr(retrieval_lab_api, "DOC_IDS_PATH", tmp_path / "missing.npy")
    monkeypatch.setattr(retrieval_lab_api, "_vectorless", None)
    monkeypatch.setattr(retrieval_lab_api, "_hybrid", None)

    response = client.post(
        "/api/v1/retrieval-lab/search",
        json={"query": "budget planning", "mode": "compare", "top_k": 3},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["results_by_mode"]["vectorless"]["status"] == "unavailable"
    assert body["results_by_mode"]["hybrid"]["status"] == "unavailable"
    assert not missing_db.exists()
