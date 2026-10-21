# FinAI Retrieval Lab: Vectorless RAG and Hybrid RAG

## What this adds

The Retrieval Lab exposes an experimental UI and API for inspecting two retrieval paths on the same query:

- **Vectorless:** SQLite FTS5/BM25 only. It uses the existing document database and does not load an embedding model or FAISS index.
- **Hybrid:** the existing FTS5 + FAISS retrieval path with Reciprocal Rank Fusion (RRF).
- **Compare:** runs both paths and reports each path's availability independently, so a missing vector index does not hide usable vectorless results.

This is an evidence-retrieval diagnostic, not a financial answer generator. Retrieval scores are ranking signals, not calibrated probabilities, causal evidence, or proof that a passage is correct.

## API

POST /api/v1/retrieval-lab/search

Example request:

    {
      "query": "RBI UPI payment dispute complaint rules",
      "mode": "compare",
      "top_k": 5
    }

Modes: vectorless, hybrid, compare. top_k is limited to 1–10 at the API boundary. The response includes per-mode status, latency, result count, source metadata, text, lexical/semantic scores and fused score when available. Hybrid model loading is lazy.

## Local setup

1. Build the document database from approved source chunks:

       .\.venv\Scripts\python.exe scripts\build_rag_index.py

2. For hybrid retrieval, build the embedding index as well:

       .\.venv\Scripts\python.exe scripts\build_rag_faiss.py

3. Start the API and frontend using the repository's normal development commands.
4. Open **Retrieval Lab** from the left navigation and run the same query in compare mode.

Vectorless mode requires only data/rag/finai_rag.db with its documents_fts index. Hybrid mode additionally requires data/rag/embeddings/finai_rag.faiss, document_ids.npy, and the embedding model dependencies/assets.

## Evaluation guidance

Do not infer that one mode is better from a single demo query. For a defensible comparison, create a fixed held-out query set with judged relevant document IDs and report:

- Recall@k and MRR (and nDCG@k if graded relevance labels exist)
- p50/p95 latency after separately reporting cold-start model-loading time
- evidence/source coverage and no-result rate
- results by query class (exact regulatory identifier, named entity, paraphrase, multilingual query)
- index/model versions, dataset snapshot, hardware and seeds

Avoid comparing a cold hybrid first call against a warmed vectorless call without reporting the difference. Do not describe vectorless retrieval as semantic retrieval; it is lexical retrieval over the FTS5 index.
