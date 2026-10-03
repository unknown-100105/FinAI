from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import torch
from torch import Tensor, nn


@dataclass(frozen=True)
class TemporalEdgeBatch:
    source: Tensor
    target: Tensor
    time_delta: Tensor


class TemporalGraphAttention(nn.Module):
    """Compact TGAT-style temporal attention layer.

    This is an architecture implementation for experimentation. Training,
    feature normalization and financial graph construction remain dataset-specific.
    """

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
        h = self.proj(node_features).view(n, self.heads, self.hidden)
        if edges.source.numel() == 0:
            return self.norm(self.out(h.reshape(n, -1)))

        source = h[edges.source]
        target = h[edges.target]
        temporal = self.time_proj(edges.time_delta.float().reshape(-1, 1)).view(-1, self.heads, self.hidden)
        message = source + temporal

        scores = []
        for head in range(self.heads):
            pair = torch.cat([message[:, head, :], target[:, head, :]], dim=-1)
            scores.append(torch.leaky_relu(pair @ self.score[head], negative_slope=0.2))
        logits = torch.stack(scores, dim=1)

        aggregate = torch.zeros_like(h)
        for dst in torch.unique(edges.target):
            mask = edges.target == dst
            weights = torch.softmax(logits[mask], dim=0)
            aggregate[dst] += torch.sum(weights.unsqueeze(-1) * message[mask], dim=0)

        return self.norm(self.out((h + aggregate).reshape(n, -1)))


def architecture_metadata() -> dict[str, object]:
    return {
        "name": "FinAI Temporal Graph Attention",
        "family": "TGAT-style continuous-time message passing",
        "status": "architecture_implemented",
        "training_status": "not_trained_in_repository",
        "inputs": ["node_features", "directed_temporal_edges", "time_delta"],
        "outputs": ["temporal_node_embeddings"],
    }
