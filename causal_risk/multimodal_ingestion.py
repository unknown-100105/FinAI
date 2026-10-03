"""Adapters from structured text/events/exposures into the typed research graph."""
from __future__ import annotations

from typing import Any, Mapping, Sequence

from causal_risk.multimodal_graph import GraphEdge, GraphNode


def build_document_nodes(documents: Sequence[Mapping[str, Any]]) -> list[GraphNode]:
    nodes=[]
    for index, document in enumerate(documents):
        text=str(document.get("text","")).strip()
        if not text:
            continue
        doc_id=str(document.get("id") or f"document-{index}")
        embedding=tuple(float(value) for value in document.get("embedding", ()))
        nodes.append(GraphNode(
            node_id=doc_id,
            node_type=str(document.get("type") or "document"),
            modality="text",
            features=embedding,
            provenance=str(document.get("source") or "user-supplied"),
        ))
    return nodes


def build_event_nodes(events: Sequence[Mapping[str, Any]]) -> list[GraphNode]:
    nodes=[]
    for index, event in enumerate(events):
        event_id=str(event.get("id") or f"event-{index}")
        severity=float(event.get("severity",0.0))
        nodes.append(GraphNode(
            node_id=event_id,
            node_type=str(event.get("type") or "market_event"),
            modality="event",
            features=(severity,),
            provenance=str(event.get("source") or "user-supplied"),
        ))
    return nodes


def build_relation_edges(
    relations: Sequence[Mapping[str, Any]],
) -> list[GraphEdge]:
    edges=[]
    for relation in relations:
        source=str(relation.get("source","")).strip()
        target=str(relation.get("target","")).strip()
        if not source or not target:
            continue
        edges.append(GraphEdge(
            source=source,
            target=target,
            relation=str(relation.get("relation") or "related_to"),
            weight=float(relation.get("weight",1.0)),
            modality=str(relation.get("modality") or "entity"),
            provenance=str(relation.get("source_document") or "user-supplied"),
        ))
    return edges


def build_portfolio_edges(
    exposures: Sequence[Mapping[str, Any]],
) -> list[GraphEdge]:
    edges=[]
    for exposure in exposures:
        asset=str(exposure.get("asset","")).strip()
        factor=str(exposure.get("factor","")).strip()
        if not asset or not factor:
            continue
        edges.append(GraphEdge(
            source=factor,
            target=asset,
            relation="portfolio_exposure",
            weight=float(exposure.get("weight",0.0)),
            modality="portfolio",
            provenance=str(exposure.get("source") or "portfolio-input"),
        ))
    return edges
