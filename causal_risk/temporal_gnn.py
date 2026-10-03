from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Sequence

import numpy as np
import torch
from torch import Tensor, nn


@dataclass(frozen=True)
class TemporalEdgeBatch:
    source: Tensor
    target: Tensor
    time_delta: Tensor


class TemporalGraphAttention(nn.Module):
    """Compact TGAT-style continuous-time attention layer."""

    def __init__(self, in_features: int, hidden_features: int = 32, heads: int = 4):
        super().__init__()
        if in_features < 1 or hidden_features < 1 or heads < 1:
            raise ValueError("in_features, hidden_features and heads must be positive")
        self.heads = heads
        self.hidden = hidden_features
        self.proj = nn.Linear(in_features, hidden_features * heads, bias=False)
        self.time_proj = nn.Linear(1, hidden_features * heads, bias=False)
        self.score = nn.Parameter(torch.empty(heads, hidden_features * 2))
        nn.init.xavier_uniform_(self.score)
        self.out = nn.Linear(hidden_features * heads, hidden_features)
        self.norm = nn.LayerNorm(hidden_features)

    def forward(self, node_features: Tensor, edges: TemporalEdgeBatch) -> Tensor:
        if node_features.ndim != 2:
            raise ValueError("node_features must be [num_nodes, features]")
        n = node_features.shape[0]
        if edges.source.numel() != edges.target.numel() or edges.source.numel() != edges.time_delta.numel():
            raise ValueError("edge tensors must have equal lengths")
        if edges.source.numel() and (edges.source.min() < 0 or edges.target.min() < 0 or edges.source.max() >= n or edges.target.max() >= n):
            raise ValueError("edge indices are outside node range")
        h = self.proj(node_features).view(n, self.heads, self.hidden)
        if edges.source.numel() == 0:
            return self.norm(self.out(h.reshape(n, -1)))

        source = h[edges.source]
        target = h[edges.target]
        temporal = self.time_proj(
            edges.time_delta.float().reshape(-1, 1)
        ).view(-1, self.heads, self.hidden)
        message = source + temporal

        logits = []
        for head in range(self.heads):
            pair = torch.cat([message[:, head, :], target[:, head, :]], dim=-1)
            logits.append(
                torch.nn.functional.leaky_relu(
                    pair @ self.score[head],
                    negative_slope=0.2,
                )
            )
        logits = torch.stack(logits, dim=1)

        aggregate = torch.zeros_like(h)
        for dst in torch.unique(edges.target):
            mask = edges.target == dst
            weights = torch.softmax(logits[mask], dim=0)
            aggregate[dst] += torch.sum(
                weights.unsqueeze(-1) * message[mask],
                dim=0,
            )

        return self.norm(self.out((h + aggregate).reshape(n, -1)))


class TemporalRiskGNN(nn.Module):
    """Temporal graph encoder plus node-risk regression head."""

    def __init__(
        self,
        in_features: int,
        hidden_features: int = 32,
        heads: int = 4,
    ) -> None:
        super().__init__()
        self.encoder = TemporalGraphAttention(
            in_features,
            hidden_features,
            heads,
        )
        self.risk_head = nn.Sequential(
            nn.Linear(hidden_features, hidden_features),
            nn.GELU(),
            nn.Linear(hidden_features, 1),
        )

    def forward(self, node_features: Tensor, edges: TemporalEdgeBatch) -> Tensor:
        return self.risk_head(self.encoder(node_features, edges)).squeeze(-1)


def build_temporal_edges(
    edge_sources: Sequence[int],
    edge_targets: Sequence[int],
    time_deltas: Sequence[float],
) -> TemporalEdgeBatch:
    if not (
        len(edge_sources)
        == len(edge_targets)
        == len(time_deltas)
    ):
        raise ValueError("temporal edge arrays must have equal lengths")
    return TemporalEdgeBatch(
        torch.tensor(edge_sources, dtype=torch.long),
        torch.tensor(edge_targets, dtype=torch.long),
        torch.tensor(time_deltas, dtype=torch.float32),
    )


def train_temporal_risk_model(
    node_features: Sequence[Sequence[float]],
    target: Sequence[float],
    edges: TemporalEdgeBatch,
    *,
    hidden_features: int = 32,
    heads: int = 4,
    epochs: int = 100,
    learning_rate: float = 1e-3,
    seed: int = 42,
) -> dict[str, Any]:
    """Train the temporal risk model on a single graph snapshot.

    This is a reproducible research training routine. For real temporal
    evaluation, callers must supply time-sliced graphs and hold out future data.
    """
    X = torch.tensor(np.asarray(node_features, dtype=np.float32))
    y = torch.tensor(np.asarray(target, dtype=np.float32))
    if X.ndim != 2 or X.shape[0] < 2:
        raise ValueError("node_features must contain at least two nodes")
    if y.ndim != 1 or len(y) != X.shape[0]:
        raise ValueError("target must align with node count")
    if not torch.isfinite(X).all() or not torch.isfinite(y).all():
        raise ValueError("node_features and target must be finite")
    if epochs < 1 or epochs > 5000:
        raise ValueError("epochs must be between 1 and 5000")
    torch.manual_seed(seed)

    model = TemporalRiskGNN(
        X.shape[1],
        hidden_features=hidden_features,
        heads=heads,
    )
    optimizer = torch.optim.Adam(model.parameters(), lr=learning_rate)
    losses: list[float] = []

    for _ in range(epochs):
        model.train()
        prediction = model(X, edges)
        loss = torch.mean((prediction - y) ** 2)
        optimizer.zero_grad()
        loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), 5.0)
        optimizer.step()
        losses.append(float(loss.detach()))

    model.eval()
    with torch.no_grad():
        prediction = model(X, edges)
    mae = float(torch.mean(torch.abs(prediction - y)))
    return {
        "status": "TGAT_RESEARCH_TRAINED",
        "epochs": epochs,
        "seed": seed,
        "final_train_mse": round(losses[-1], 8),
        "train_mae": round(mae, 8),
        "model": model,
    }


def architecture_metadata() -> dict[str, object]:
    return {
        "name": "FinAI Temporal Graph Attention",
        "family": "TGAT-style continuous-time message passing",
        "status": "research_implementation",
        "training_status": "reproducible_training_routine_available",
        "inputs": ["node_features", "directed_temporal_edges", "time_delta"],
        "outputs": ["temporal_node_embeddings", "node_risk_score"],
        "evaluation_boundary": "Training on a snapshot does not establish out-of-sample temporal validity; future-held-out evaluation is required.",
    }
