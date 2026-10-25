"""Experimental retrieval diagnostics API for Vectorless RAG and hybrid RAG."""
from __future__ import annotations

import time
from pathlib import Path
from typing import Any, Dict, Literal, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from rag.vectorless_retriever import VectorlessRetriever

router = APIRouter(prefix="/api/v1/retrieval-lab", tags=["retrieval-lab"])
ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "data" / "rag" / "finai_rag.db"
FAISS_PATH = ROOT / "data" / "rag" / "embeddings" / "finai_rag.faiss"
DOC_IDS_PATH = ROOT / "data" / "rag" / "embeddings" / "document_ids.npy"
_vectorless: Optional[VectorlessRetriever] = None
_hybrid = None
_embedding_adapter = None


class RetrievalSearchRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=1000)
    mode: Literal["vectorless", "hybrid", "compare"] = "compare"
    top_k: int = Field(default=5, ge=1, le=10)


def _get_vectorless() -> VectorlessRetriever:
    global _vectorless
    # sqlite3.connect creates a new empty database when the path is absent.
    # Fail closed before constructing the retriever so a diagnostic API request
    # cannot manufacture a misleading, unusable "RAG database" in the checkout.
    if not DB_PATH.is_file():
        raise FileNotFoundError(
            "Vectorless RAG database is unavailable; build data/rag/finai_rag.db first."
        )
    if _vectorless is None or _vectorless.db_path != DB_PATH:
        _vectorless = VectorlessRetriever(DB_PATH)
    return _vectorless


def _get_hybrid():
    global _hybrid, _embedding_adapter
    missing = [str(path) for path in (DB_PATH, FAISS_PATH, DOC_IDS_PATH) if not path.is_file()]
    if missing:
        raise FileNotFoundError(
            "Hybrid retrieval assets are unavailable: " + ", ".join(missing)
        )
    if _hybrid is None:
        from llm.qwen_embedding_adapter import QwenEmbeddingAdapter
        from rag.hybrid_retriever import HybridRetriever

        _embedding_adapter = QwenEmbeddingAdapter(device=None, max_seq_length=640)
        _hybrid = HybridRetriever(
            db_path=DB_PATH,
            faiss_index_path=FAISS_PATH,
            document_ids_path=DOC_IDS_PATH,
            embedding_adapter=_embedding_adapter,
        )
    return _hybrid


def _document_dict(document: Any, mode: str) -> Dict[str, Any]:
    if mode == "vectorless":
        return {
            "document_id": document.document_id,
            "title": document.title,
            "source": document.source,
            "date": document.date,
            "text": document.text,
            "lexical_score": document.score,
            "semantic_score": None,
            "fused_score": None,
        }
    return {
        "document_id": document.document_id,
        "title": document.title,
        "source": document.source,
        "date": document.date,
        "text": document.text,
        "lexical_score": document.lexical_score,
        "semantic_score": document.semantic_score,
        "fused_score": document.fused_score,
    }


def _run_mode(query: str, top_k: int, mode: str) -> Dict[str, Any]:
    started = time.perf_counter()
    if mode == "vectorless":
        documents = _get_vectorless().retrieve(query, top_k=top_k)
    else:
        documents = _get_hybrid().retrieve(query, top_k=top_k)
    elapsed_ms = round((time.perf_counter() - started) * 1000, 3)
    return {
        "mode": mode,
        "latency_ms": elapsed_ms,
        "result_count": len(documents),
        "results": [_document_dict(document, mode) for document in documents],
        "status": "available",
    }


@router.post("/search")
def retrieval_search(request: RetrievalSearchRequest) -> Dict[str, Any]:
    query = request.query.strip()
    if not query:
        raise HTTPException(status_code=422, detail="query cannot be blank")

    response: Dict[str, Any] = {
        "query": query,
        "top_k": request.top_k,
        "mode": request.mode,
        "results_by_mode": {},
        "notice": (
            "Retrieval scores are ranking signals, not probabilities or proof of correctness. "
            "This lab retrieves evidence; it does not generate a financial answer."
        ),
    }
    modes = ("vectorless", "hybrid") if request.mode == "compare" else (request.mode,)
    for mode in modes:
        try:
            response["results_by_mode"][mode] = _run_mode(query, request.top_k, mode)
        except FileNotFoundError:
            reason = (
                "Vectorless RAG database is unavailable; build data/rag/finai_rag.db first."
                if mode == "vectorless"
                else "Hybrid RAG assets are unavailable; build the SQLite database and FAISS index first."
            )
            response["results_by_mode"][mode] = {
                "mode": mode, "status": "unavailable", "results": [],
                "result_count": 0, "latency_ms": None, "reason": reason,
            }
        except (RuntimeError, ValueError) as exc:
            response["results_by_mode"][mode] = {
                "mode": mode, "status": "error", "results": [],
                "result_count": 0, "latency_ms": None, "reason": str(exc),
            }
        except Exception:
            # Avoid leaking filesystem/provider internals through the API.
            response["results_by_mode"][mode] = {
                "mode": mode, "status": "error", "results": [],
                "result_count": 0, "latency_ms": None,
                "reason": "Retrieval failed. Check backend logs and local RAG assets.",
            }

    if request.mode != "compare":
        only = response["results_by_mode"][request.mode]
        if only["status"] == "unavailable":
            raise HTTPException(status_code=503, detail=only["reason"])
        if only["status"] == "error":
            raise HTTPException(status_code=500, detail=only["reason"])
    return response
