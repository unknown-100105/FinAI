"""Typed multimodal graph primitives and deterministic fusion encoder."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Sequence

import numpy as np


@dataclass(frozen=True)
class GraphNode:
    node_id: str
    node_type: str
    modality: str
    features: tuple[float, ...]
    provenance: str


@dataclass(frozen=True)
class GraphEdge:
    source: str
    target: str
    relation: str
    weight: float
    modality: str
    provenance: str


class MultimodalGraph:
    """Small typed graph with explicit provenance and missing-modality handling."""

    ALLOWED_MODALITIES = {"market", "macro", "text", "event", "entity", "portfolio"}

    def __init__(
        self,
        nodes: Sequence[GraphNode] | None = None,
        edges: Sequence[GraphEdge] | None = None,
    ) -> None:
        self.nodes = {node.node_id: node for node in (nodes or [])}
        self.edges = list(edges or [])
        self._validate()

    def _validate(self) -> None:
        for node in self.nodes.values():
            if node.modality not in self.ALLOWED_MODALITIES:
                raise ValueError(f"unsupported node modality: {node.modality}")
            if not node.node_id or not node.provenance:
                raise ValueError("nodes require non-empty ids and provenance")
            if not np.isfinite(np.asarray(node.features, dtype=float)).all():
                raise ValueError("node features must be finite")
        for edge in self.edges:
            if edge.source not in self.nodes or edge.target not in self.nodes:
                raise ValueError("edge references an unknown node")
            if not np.isfinite(float(edge.weight)):
                raise ValueError("edge weight must be finite")
            if not edge.relation or not edge.provenance:
                raise ValueError("edges require relation and provenance")

    def adjacency_messages(self, node_id: str) -> list[dict[str, Any]]:
        if node_id not in self.nodes:
            raise ValueError(f"unknown node: {node_id}")
        messages = []
        for edge in self.edges:
            if edge.target == node_id:
                messages.append({
                    "source": edge.source,
                    "relation": edge.relation,
                    "weight": float(edge.weight),
                    "modality": edge.modality,
                    "provenance": edge.provenance,
                })
        return messages

    def fuse_node(
        self,
        node_id: str,
        modality_vectors: Mapping[str, Sequence[float]],
        *,
        output_dim: int = 16,
    ) -> np.ndarray:
        """Fuse whatever modalities are available; absent modalities are omitted."""
        if output_dim < 1:
            raise ValueError("output_dim must be positive")
        base = np.zeros(output_dim, dtype=float)
        count = 0
        for modality, vector in sorted(modality_vectors.items()):
            if modality not in self.ALLOWED_MODALITIES:
                continue
            arr = np.asarray(vector, dtype=float).reshape(-1)
            if not np.isfinite(arr).all():
                raise ValueError(f"non-finite {modality} vector")
            # Deterministic projection without a learned dependency.
            projected = np.resize(arr, output_dim)
            scale = 1.0 / max(np.linalg.norm(projected), 1.0)
            base += projected * scale
            count += 1

        node = self.nodes[node_id]
        if node.features:
            projected = np.resize(np.asarray(node.features, dtype=float), output_dim)
            base += projected / max(np.linalg.norm(projected), 1.0)
            count += 1

        for message in self.adjacency_messages(node_id):
            source = self.nodes[message["source"]]
            projected = np.resize(np.asarray(source.features, dtype=float), output_dim)
            base += projected * float(message["weight"]) / max(np.linalg.norm(projected), 1.0)
            count += 1

        return base / max(count, 1)

    def payload(self) -> dict[str, Any]:
        return {
            "nodes": [
                {
                    "node_id": node.node_id,
                    "node_type": node.node_type,
                    "modality": node.modality,
                    "feature_dimension": len(node.features),
                    "provenance": node.provenance,
                }
                for node in self.nodes.values()
            ],
            "edges": [
                {
                    "source": edge.source,
                    "target": edge.target,
                    "relation": edge.relation,
                    "weight": edge.weight,
                    "modality": edge.modality,
                    "provenance": edge.provenance,
                }
                for edge in self.edges
            ],
            "semantics": "Typed multimodal research graph with explicit provenance; fusion is deterministic unless replaced by a trained encoder.",
        }
