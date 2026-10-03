from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Dict, Iterable, List, Tuple


@dataclass(frozen=True)
class CausalNode:
    node_id: str
    label: str
    kind: str


@dataclass(frozen=True)
class CausalEdge:
    source: str
    target: str
    weight: float
    lag: int = 0
    modality: str = "structural"


DEFAULT_NODES: Tuple[CausalNode, ...] = (
    CausalNode("rates", "Central-bank rates", "macro"),
    CausalNode("usd", "USD / INR", "macro"),
    CausalNode("oil", "Energy prices", "commodity"),
    CausalNode("supply", "East Asia supply", "supply_chain"),
    CausalNode("credit", "Credit spreads", "funding"),
    CausalNode("liquidity", "Market liquidity", "market"),
    CausalNode("equity", "Equity risk", "market"),
    CausalNode("portfolio", "Portfolio drawdown", "outcome"),
)

DEFAULT_EDGES: Tuple[CausalEdge, ...] = (
    CausalEdge("rates", "credit", 0.72),
    CausalEdge("rates", "equity", 0.64),
    CausalEdge("usd", "oil", 0.35),
    CausalEdge("usd", "equity", 0.41),
    CausalEdge("oil", "credit", 0.28),
    CausalEdge("oil", "equity", 0.52),
    CausalEdge("supply", "oil", 0.23),
    CausalEdge("supply", "liquidity", 0.61),
    CausalEdge("credit", "liquidity", 0.68),
    CausalEdge("credit", "equity", 0.57),
    CausalEdge("liquidity", "equity", 0.74),
    CausalEdge("equity", "portfolio", 0.83),
)


def graph_payload(
    nodes: Iterable[CausalNode] = DEFAULT_NODES,
    edges: Iterable[CausalEdge] = DEFAULT_EDGES,
) -> Dict[str, Any]:
    return {
        "nodes": [asdict(node) for node in nodes],
        "edges": [asdict(edge) for edge in edges],
    }


def validate_graph(nodes: Iterable[CausalNode], edges: Iterable[CausalEdge]) -> List[str]:
    node_ids = {node.node_id for node in nodes}
    errors: List[str] = []
    for edge in edges:
        if edge.source not in node_ids or edge.target not in node_ids:
            errors.append(f"unknown endpoint: {edge.source}->{edge.target}")
        if edge.source == edge.target and edge.lag == 0:
            errors.append(f"contemporaneous self-loop: {edge.source}")
    return errors
