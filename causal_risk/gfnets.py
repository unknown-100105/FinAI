"""Compact GFlowNet-style tail trajectory research prototype."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Sequence

import numpy as np
import torch
from torch import nn

from causal_risk.stress_objectives import CausalStressReward


@dataclass(frozen=True)
class GFlowConfig:
    hidden_dim: int = 64
    levels: tuple[float, ...] = (-1.0, -0.5, 0.5, 1.0)
    learning_rate: float = 1e-3
    epochs: int = 150
    seed: int = 42
    device: str = "auto"


class TailFlowPolicy(nn.Module):
    def __init__(self, n_factors: int, hidden_dim: int, n_levels: int) -> None:
        super().__init__()
        self.n_factors = n_factors
        self.n_levels = n_levels
        self.net = nn.Sequential(
            nn.Linear(n_factors + n_factors + 1, hidden_dim),
            nn.Tanh(),
            nn.Linear(hidden_dim, hidden_dim),
            nn.Tanh(),
            nn.Linear(hidden_dim, n_levels),
        )

    def forward(self, state: torch.Tensor, step: int) -> torch.Tensor:
        step_vector = torch.zeros((state.shape[0], self.n_factors + 1), device=state.device)
        step_vector[:, step] = 1.0
        step_vector[:, -1] = float(step) / max(self.n_factors - 1, 1)
        return self.net(torch.cat([state, step_vector], dim=1))


class GFlowNetTailGenerator:
    """Research prototype using trajectory-balance-style training.

    It is a generative flow model prototype, not a claim of production-grade
    GFlowNet optimality.
    """

    def __init__(self, n_factors: int, config: GFlowConfig | None = None) -> None:
        if n_factors < 1:
            raise ValueError("n_factors must be positive")
        self.config = config or GFlowConfig()
        if self.config.epochs < 1:
            raise ValueError("epochs must be positive")
        self.n_factors = n_factors
        self.levels = torch.tensor(self.config.levels, dtype=torch.float32)
        self.policy = TailFlowPolicy(n_factors, self.config.hidden_dim, len(self.config.levels))
        self.log_z = nn.Parameter(torch.tensor(0.0))
        self.trained = False
        self.device = "cpu"

    def _reward(self, trajectory: torch.Tensor) -> torch.Tensor:
        magnitude = torch.linalg.vector_norm(trajectory, dim=1)
        diversity = torch.std(trajectory, dim=1)
        return torch.exp(1.5 * magnitude + 0.25 * diversity).clamp_min(1e-8)

    def train(
        self,
        *,
        seed: int | None = None,
        reward_fn: Any | None = None,
        objective_name: str = "synthetic_tail_reward",
    ) -> dict[str, Any]:
        seed = self.config.seed if seed is None else int(seed)
        torch.manual_seed(seed)
        requested_device = str(device or self.config.device).lower()
        if requested_device == "auto":
            resolved = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        elif requested_device in {"cpu", "cuda"}:
            resolved = torch.device(requested_device)
        else:
            raise ValueError("device must be 'auto', 'cpu', or 'cuda'")
        if resolved.type == "cuda" and not torch.cuda.is_available():
            raise ValueError("cuda device requested but CUDA is unavailable")
        self.device = str(resolved)
        self.policy.to(resolved)
        self.log_z.data = self.log_z.data.to(resolved)
        levels = self.levels.to(resolved)
        if resolved.type == "cuda":
            torch.cuda.manual_seed_all(seed)
        optimizer = torch.optim.Adam(
            list(self.policy.parameters()) + [self.log_z],
            lr=self.config.learning_rate,
        )
        losses = []
        for epoch in range(self.config.epochs):
            batch = torch.zeros((64, self.n_factors), dtype=torch.float32, device=resolved)
            log_pf = torch.zeros(64, device=resolved)
            for step in range(self.n_factors):
                logits = self.policy(batch, step)
                dist = torch.distributions.Categorical(logits=logits)
                action = dist.sample()
                log_pf += dist.log_prob(action)
                batch[:, step] = levels[action]
            reward = (
                self._reward(batch)
                if reward_fn is None
                else reward_fn(batch)
            )
            if reward.ndim != 1 or reward.shape[0] != batch.shape[0]:
                raise ValueError("reward_fn must return one finite reward per trajectory")
            if not torch.isfinite(reward).all() or torch.any(reward <= 0):
                raise ValueError("reward_fn must return finite strictly positive rewards")
            loss = torch.mean((self.log_z + log_pf - torch.log(reward)) ** 2)
            optimizer.zero_grad()
            loss.backward()
            torch.nn.utils.clip_grad_norm_(list(self.policy.parameters()) + [self.log_z], 5.0)
            optimizer.step()
            if epoch in {0, self.config.epochs - 1}:
                losses.append(float(loss.detach()))
        self.trained = True
        return {
            "status": "GFLOWNET_RESEARCH_TRAINED",
            "epochs": self.config.epochs,
            "final_loss": losses[-1] if losses else None,
            "seed": seed,
            "factors": self.n_factors,
            "levels": list(self.config.levels),
            "objective": objective_name,
            "reward_metadata": (
                reward_fn.metadata()
                if hasattr(reward_fn, "metadata")
                else {"objective": objective_name}
            ),
            "device": self.device,
        }

    def sample(
        self,
        center: Mapping[str, float],
        *,
        scale: float = 0.35,
        draws: int = 64,
        seed: int = 42,
    ) -> dict[str, Any]:
        if not self.trained:
            raise RuntimeError("GFlowNet prototype must be trained before sampling")
        if draws < 1 or draws > 5000:
            raise ValueError("draws must be between 1 and 5000")
        keys = tuple(sorted(center))
        if len(keys) != self.n_factors:
            raise ValueError("center factor count does not match trained generator")
        requested_device = str(self.device or "cpu")
        device = torch.device(requested_device)
        generator = torch.Generator(device=device).manual_seed(seed)
        state = torch.zeros((draws, self.n_factors), device=device)
        levels = self.levels.to(device)
        with torch.no_grad():
            for step in range(self.n_factors):
                logits = self.policy(state, step)
                # Deterministic sampling from an explicit seeded generator.
                probs = torch.softmax(logits, dim=-1)
                action = torch.multinomial(probs, 1, generator=generator).squeeze(1)
                state[:, step] = levels[action]
        result = []
        for row in state.detach().cpu().numpy():
            result.append({
                key: round(float(center[key]) + float(value) * max(abs(float(center[key])) * scale, 5.0), 3)
                for key, value in zip(keys, row)
            })
        return {
            "status": "GFLOWNET_SAMPLES_READY",
            "draws": draws,
            "seed": seed,
            "scenarios": result,
            "semantics": "Research GFlowNet-style trajectory sampler; generated scenarios require plausibility and risk validation.",
        }
