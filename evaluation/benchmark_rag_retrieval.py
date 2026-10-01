from __future__ import annotations

import argparse
import json
import sqlite3
import time
from pathlib import Path
from statistics import mean, median
from typing import Callable, Dict, Iterable, List, Sequence

import faiss
import numpy as np


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_GOLD = ROOT / "evaluation" / "rag_retrieval_gold_v1.json"
DEFAULT_DB = ROOT / "data" / "rag" / "finai_rag.db"
DEFAULT_INDEX = ROOT / "data" / "rag" / "embeddings" / "finai_rag.faiss"
DEFAULT_IDS = ROOT / "data" / "rag" / "embeddings" / "document_ids.npy"
DEFAULT_OUTPUT = ROOT / "evaluation" / "rag_retrieval_benchmark_v1.json"


def load_gold(path: Path) -> List[dict]:
    data = json.loads(path.read_text(encoding="utf-8"))
    cases = data.get("cases") or []
    if not cases:
        raise ValueError("Gold set contains no cases.")
    return cases


def database_document_count(db_path: Path) -> int:
    with sqlite3.connect(str(db_path)) as con:
        row = con.execute("SELECT COUNT(*) FROM documents").fetchone()
    return int(row[0])


def verify_faiss_complete(
    db_path: Path,
    index_path: Path,
    ids_path: Path,
) -> dict:
    if not index_path.exists():
        raise FileNotFoundError(index_path)
    if not ids_path.exists():
        raise FileNotFoundError(ids_path)

    index = faiss.read_index(str(index_path))
    ids = np.load(ids_path).astype(np.int64)
    db_count = database_document_count(db_path)

    if index.ntotal != len(ids):
        raise ValueError(
            f"FAISS vector count ({index.ntotal}) != ID count ({len(ids)})."
        )

    if index.ntotal != db_count:
        raise RuntimeError(
            "Production FAISS index is incomplete: "
            f"{index.ntotal} vectors vs {db_count} database documents."
        )

    if index.d != 1024:
        raise ValueError(f"Expected FAISS dimension 1024, got {index.d}.")

    return {
        "database_documents": db_count,
        "faiss_vectors": int(index.ntotal),
        "faiss_dimension": int(index.d),
        "document_ids": int(len(ids)),
        "complete": True,
    }


def normalize_hits(results: Sequence) -> List[int]:
    ids: List[int] = []
    for item in results:
        if isinstance(item, dict):
            doc_id = item.get("document_id")
        else:
            doc_id = getattr(item, "document_id", None)
        if doc_id is not None:
            ids.append(int(doc_id))
    return ids


def evaluate_case(
    query: str,
    gold_ids: Iterable[int],
    retrieve: Callable[[str, int], Sequence],
    top_k: int,
) -> dict:
    gold = {int(x) for x in gold_ids}

    started = time.perf_counter()
    try:
        raw = retrieve(query, top_k)
        error = None
    except Exception as exc:  # benchmark must record query-specific failures
        raw = []
        error = f"{type(exc).__name__}: {exc}"
    latency = time.perf_counter() - started

    hits = normalize_hits(raw)
    first_relevant_rank = next(
        (
            rank
            for rank, doc_id in enumerate(hits, start=1)
            if doc_id in gold
        ),
        None,
    )

    return {
        "retrieved_document_ids": hits,
        "gold_document_ids": sorted(gold),
        "recall": 1.0 if gold.intersection(hits) else 0.0,
        "mrr": (1.0 / first_relevant_rank) if first_relevant_rank else 0.0,
        "first_relevant_rank": first_relevant_rank,
        "latency_seconds": latency,
        "error": error,
    }


def summarize(case_results: Sequence[dict]) -> dict:
    latencies = [
        float(item["latency_seconds"])
        for item in case_results
        if item.get("error") is None
    ]
    return {
        "cases": len(case_results),
        "recall_at_k": mean(
            float(item["recall"]) for item in case_results
        ) if case_results else 0.0,
        "mrr": mean(
            float(item["mrr"]) for item in case_results
        ) if case_results else 0.0,
        "mean_latency_seconds": mean(latencies) if latencies else None,
        "median_latency_seconds": median(latencies) if latencies else None,
        "failed_cases": sum(
            1 for item in case_results if item.get("error") is not None
        ),
    }


def build_fts_retriever(db_path: Path):
    class FTSOnly:
        def __init__(self, path: Path):
            self.db_path = path

        def retrieve(self, query: str, top_k: int):
            from rag.hybrid_retriever import HybridRetriever

            fts_query = HybridRetriever._build_fts5_query(query.strip())

            if fts_query == '""':
                return []

            with sqlite3.connect(str(self.db_path)) as con:
                rows = con.execute(
                    """
                    SELECT
                        d.id,
                        d.title,
                        d.source,
                        d.date,
                        d.text
                    FROM documents_fts
                    JOIN documents d
                      ON d.id = documents_fts.rowid
                    WHERE documents_fts MATCH ?
                    ORDER BY bm25(documents_fts)
                    LIMIT ?
                    """,
                    (fts_query, top_k),
                ).fetchall()

            return [
                {
                    "document_id": int(row[0]),
                    "title": row[1] or "",
                    "source": row[2] or "",
                    "date": row[3] or "",
                    "text": row[4] or "",
                }
                for row in rows
            ]

    return FTSOnly(db_path)


def build_semantic_retriever(
    db_path: Path,
    index_path: Path,
    ids_path: Path,
):
    from llm.qwen_embedding_adapter import QwenEmbeddingAdapter
    from rag.hybrid_retriever import HybridRetriever

    adapter = QwenEmbeddingAdapter(
        device="cuda",
        max_seq_length=640,
    )

    # Warm the model before timing benchmark queries.
    adapter.embed(
        ["FinAI RAG benchmark warmup"],
        is_query=True,
        batch_size=1,
        normalize_embeddings=True,
    )

    retriever = HybridRetriever(
        db_path=db_path,
        faiss_index_path=index_path,
        document_ids_path=ids_path,
        embedding_adapter=adapter,
    )
    return retriever


def run_benchmark(
    gold_cases: Sequence[dict],
    retrievers: Dict[str, Callable[[str, int], Sequence]],
    top_ks: Sequence[int],
) -> dict:
    output = {
        "benchmark": "FinAI RAG Retrieval Benchmark",
        "version": "v1",
        "gold_set": str(DEFAULT_GOLD.relative_to(ROOT)),
        "top_k_values": list(top_ks),
        "methods": {},
    }

    for method_name, retriever in retrievers.items():
        method_data = {}

        for top_k in top_ks:
            case_results = []
            for case in gold_cases:
                result = evaluate_case(
                    query=case["query"],
                    gold_ids=case["gold_document_ids"],
                    retrieve=retriever,
                    top_k=top_k,
                )
                case_results.append(
                    {
                        "case_id": case["case_id"],
                        "topic": case.get("topic"),
                        "query": case["query"],
                        **result,
                    }
                )

            summary = summarize(case_results)
            method_data[f"top_{top_k}"] = {
                "summary": summary,
                "cases": case_results,
            }

        output["methods"][method_name] = method_data

    return output


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Benchmark FinAI RAG retrieval against the curated gold set."
    )
    parser.add_argument("--gold", type=Path, default=DEFAULT_GOLD)
    parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    parser.add_argument("--index", type=Path, default=DEFAULT_INDEX)
    parser.add_argument("--ids", type=Path, default=DEFAULT_IDS)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument(
        "--top-k",
        nargs="+",
        type=int,
        default=[5, 10],
    )
    parser.add_argument(
        "--skip-semantic",
        action="store_true",
        help="Run FTS5 only; useful while the production FAISS index is still building.",
    )

    args = parser.parse_args()

    for path in [args.gold, args.db]:
        if not path.exists():
            raise FileNotFoundError(path)

    gold_cases = load_gold(args.gold)

    retrievers: Dict[str, Callable[[str, int], Sequence]] = {
        "fts5": build_fts_retriever(args.db).retrieve,
    }

    integrity = None
    if not args.skip_semantic:
        integrity = verify_faiss_complete(
            args.db,
            args.index,
            args.ids,
        )
        semantic = build_semantic_retriever(
            args.db,
            args.index,
            args.ids,
        )
        retrievers["faiss"] = (
            lambda query, top_k: semantic._semantic_search(query, top_k)
        )
        retrievers["hybrid_rrf"] = (
            lambda query, top_k: semantic.retrieve(
                query,
                top_k=top_k,
                candidate_k=max(top_k * 4, 20),
            )
        )

    output = run_benchmark(
        gold_cases=gold_cases,
        retrievers=retrievers,
        top_ks=args.top_k,
    )

    output["corpus_integrity"] = integrity
    output["gold_cases"] = len(gold_cases)
    output["notes"] = [
        "Recall@k uses at least one gold document appearing in the top-k results.",
        "MRR uses the rank of the first gold document.",
        "Model load time is excluded from per-query latency via a warmup call.",
        "FAISS/Hybrid runs require a complete production index unless --skip-semantic is used.",
    ]

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(output, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    print("RAG RETRIEVAL BENCHMARK COMPLETE")
    print("GOLD CASES:", len(gold_cases))
    print("METHODS:", ", ".join(retrievers))
    print("OUTPUT:", args.output)

    for method_name, method_data in output["methods"].items():
        for k, result in method_data.items():
            summary = result["summary"]
            print(
                f"{method_name} {k}: "
                f"Recall={summary['recall_at_k']:.4f} "
                f"MRR={summary['mrr']:.4f} "
                f"MeanLatency={summary['mean_latency_seconds']}"
            )


if __name__ == "__main__":
    main()
