"""Text-to-graph alignment utilities with explicit embedding provenance."""
from __future__ import annotations

from typing import Any, Mapping, Sequence

import numpy as np


def cosine_similarity(a: Sequence[float], b: Sequence[float]) -> float:
    left = np.asarray(a, dtype=float)
    right = np.asarray(b, dtype=float)
    if left.ndim != 1 or right.ndim != 1 or left.shape != right.shape:
        raise ValueError("embedding vectors must be 1-D and have equal dimensions")
    if not np.isfinite(left).all() or not np.isfinite(right).all():
        raise ValueError("embeddings must be finite")
    denominator = float(np.linalg.norm(left) * np.linalg.norm(right))
    return 0.0 if denominator < 1e-12 else float(np.dot(left, right) / denominator)


def align_text_to_graph(
    text_embedding: Sequence[float],
    node_embeddings: Mapping[str, Sequence[float]],
    *,
    min_similarity: float = 0.0,
) -> dict[str, Any]:
    """Return deterministic semantic candidates from supplied embeddings.

    This function performs alignment only; it does not claim that semantic
    similarity implies a causal or factual relation.
    """
    if not node_embeddings:
        return {"status":"NO_GRAPH_EMBEDDINGS","matches":[]}
    scores=[]
    for node_id, embedding in node_embeddings.items():
        similarity=cosine_similarity(text_embedding, embedding)
        if similarity >= min_similarity:
            scores.append({"node_id":str(node_id),"similarity":round(similarity,6)})
    scores.sort(key=lambda item:(-item["similarity"],item["node_id"]))
    return {
        "status":"TEXT_GRAPH_ALIGNMENT_READY",
        "matches":scores,
        "semantics":"Embedding similarity proposes semantic links; it does not establish causality or factual truth."
    }
