"""Financial and causal reward functions for stress-trajectory generation."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

import numpy as np
import torch
from torch import Tensor


@dataclass(frozen=True)
class CausalStressReward:
    """Composite reward for empirical, causal-consistency-aware scenario search.

    The objective is deliberately explicit and inspectable. It combines tail
    severity, empirical support, directional agreement with a supplied causal
    graph, and portfolio relevance. It is a research objective, not a proven
    probability model.
    """

    empirical_center: tuple[float, ...]
    empirical_scale: tuple[float, ...]
    correlation_inverse: tuple[tuple[float, ...], ...] | None = None
    edge_matrix: tuple[tuple[float, ...], ...] | None = None
    portfolio_weights: tuple[float, ...] | None = None

    def __post_init__(self) -> None:
        d = len(self.empirical_center)
        if d < 1 or len(self.empirical_scale) != d:
            raise ValueError("empirical center and scale dimensions must match")
        if any(float(scale) <= 0 for scale in self.empirical_scale):
            raise ValueError("empirical scales must be positive")
        for matrix, name in (
            (self.correlation_inverse, "correlation_inverse"),
            (self.edge_matrix, "edge_matrix"),
        ):
            if matrix is not None:
                array = np.asarray(matrix, dtype=float)
                if array.shape != (d, d):
                    raise ValueError(f"{name} must be square with factor dimension")
                if not np.isfinite(array).all():
                    raise ValueError(f"{name} must be finite")
        if self.portfolio_weights is not None:
            if len(self.portfolio_weights) != d:
                raise ValueError("portfolio_weights must match factor dimension")

    def __call__(self, trajectory: Tensor) -> Tensor:
        if trajectory.ndim != 2 or trajectory.shape[1] != len(self.empirical_center):
            raise ValueError("trajectory has incompatible dimensions")
        z = trajectory.float()
        center = torch.tensor(self.empirical_center, dtype=z.dtype, device=z.device)
        scale = torch.tensor(self.empirical_scale, dtype=z.dtype, device=z.device)
        shock = center + z * scale

        severity = torch.linalg.vector_norm(z, dim=1)
        tail_severity = torch.sigmoid(severity - 1.0)

        standardized = (shock - center) / torch.clamp(scale, min=1e-8)
        if self.correlation_inverse is None:
            mahalanobis = torch.sum(standardized * standardized, dim=1)
        else:
            inv = torch.tensor(
                self.correlation_inverse,
                dtype=z.dtype,
                device=z.device,
            )
            mahalanobis = torch.einsum("bi,ij,bj->b", standardized, inv, standardized)
        empirical_support = torch.exp(-0.5 * torch.clamp(mahalanobis, max=50.0) / max(z.shape[1], 1))

        if self.edge_matrix is None:
            causal_alignment = torch.ones_like(tail_severity)
        else:
            edges = torch.tensor(self.edge_matrix, dtype=z.dtype, device=z.device)
            nz = edges != 0
            if torch.any(nz):
                relation = edges.unsqueeze(0) * z.unsqueeze(2) * z.unsqueeze(1)
                causal_alignment = torch.sigmoid(
                    3.0 * relation[:, nz]
                ).mean(dim=1)
            else:
                causal_alignment = torch.ones_like(tail_severity)

        if self.portfolio_weights is None:
            portfolio_relevance = severity / max(float(z.shape[1]) ** 0.5, 1.0)
        else:
            weights = torch.tensor(
                self.portfolio_weights,
                dtype=z.dtype,
                device=z.device,
            )
            portfolio_relevance = torch.abs(z) @ torch.abs(weights)
            portfolio_relevance = portfolio_relevance / torch.clamp(
                torch.sum(torch.abs(weights)),
                min=1e-8,
            )

        # Geometric means keep one extreme component from fully dominating.
        score = torch.clamp(
            tail_severity
            * torch.sqrt(torch.clamp(empirical_support, min=1e-8))
            * causal_alignment
            * (0.5 + 0.5 * torch.sigmoid(portfolio_relevance)),
            min=1e-8,
        )
        return score

    def metadata(self) -> dict[str, object]:
        return {
            "objective": "causal_empirical_tail_reward",
            "components": [
                "tail_severity",
                "empirical_support",
                "causal_direction_alignment",
                "portfolio_relevance",
            ],
            "semantics": (
                "Research reward for constrained stress-trajectory search. "
                "It is not a calibrated scenario probability."
            ),
        }
