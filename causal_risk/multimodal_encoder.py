"""Trainable multimodal financial state encoder with masked-modality learning."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Sequence

import numpy as np
import torch
from torch import Tensor, nn


DEFAULT_MODALITIES = (
    "market",
    "macro",
    "text",
    "event",
    "entity",
    "portfolio",
    "microstructure",
)


@dataclass(frozen=True)
class MultimodalEncoderConfig:
    hidden_dim: int = 64
    layers: int = 2
    heads: int = 4
    dropout: float = 0.1
    seed: int = 42


class MultimodalFinancialEncoder(nn.Module):
    """Cross-modal transformer over typed financial modalities.

    Each modality has its own input projection and a learned modality token.
    Missing modalities are represented by a learned missing embedding.
    """

    def __init__(
        self,
        modality_dimensions: Mapping[str, int],
        config: MultimodalEncoderConfig | None = None,
    ) -> None:
        super().__init__()
        self.config = config or MultimodalEncoderConfig()
        if self.config.hidden_dim < 8:
            raise ValueError("hidden_dim must be at least 8")
        if self.config.heads < 1 or self.config.hidden_dim % self.config.heads:
            raise ValueError("hidden_dim must be divisible by heads")
        clean = {str(k): int(v) for k, v in modality_dimensions.items()}
        if not clean:
            raise ValueError("at least one modality is required")
        if any(v < 1 for v in clean.values()):
            raise ValueError("modality dimensions must be positive")
        self.modalities = tuple(sorted(clean))
        self.projections = nn.ModuleDict({
            modality: nn.Linear(dim, self.config.hidden_dim)
            for modality, dim in clean.items()
        })
        self.modality_embeddings = nn.Parameter(
            torch.randn(len(self.modalities), self.config.hidden_dim) * 0.02
        )
        self.missing_embedding = nn.Parameter(
            torch.zeros(self.config.hidden_dim)
        )
        layer = nn.TransformerEncoderLayer(
            d_model=self.config.hidden_dim,
            nhead=self.config.heads,
            dropout=self.config.dropout,
            batch_first=True,
            norm_first=True,
            activation="gelu",
        )
        self.transformer = nn.TransformerEncoder(layer, num_layers=self.config.layers)
        self.norm = nn.LayerNorm(self.config.hidden_dim)
        self.reconstruction_heads = nn.ModuleDict({
            modality: nn.Linear(self.config.hidden_dim, self.config.hidden_dim)
            for modality in self.modalities
        })

    def _stack(
        self,
        inputs: Mapping[str, Tensor],
        *,
        device: torch.device,
        force_missing: str | None = None,
    ) -> tuple[Tensor, Tensor]:
        batch_size = None
        tokens = []
        present = []
        for index, modality in enumerate(self.modalities):
            value = inputs.get(modality)
            is_present = value is not None and modality != force_missing
            if is_present:
                tensor = value.to(device).float()
                if tensor.ndim != 2 or tensor.shape[1] != self.projections[modality].in_features:
                    raise ValueError(f"{modality} tensor has an incompatible shape")
                if batch_size is None:
                    batch_size = tensor.shape[0]
                if tensor.shape[0] != batch_size:
                    raise ValueError("all modality batches must have equal row counts")
                if not torch.isfinite(tensor).all():
                    raise ValueError(f"{modality} tensor contains non-finite values")
                token = self.projections[modality](tensor)
                present.append(torch.ones(batch_size, dtype=torch.bool, device=device))
            else:
                if batch_size is None:
                    provided = [value for value in inputs.values() if value is not None]
                    if not provided:
                        raise ValueError("at least one modality batch is required")
                    batch_size = int(provided[0].shape[0])
                token = self.missing_embedding.expand(batch_size, -1)
                present.append(torch.zeros(batch_size, dtype=torch.bool, device=device))
            token = token + self.modality_embeddings[index].to(device)
            tokens.append(token)

        return torch.stack(tokens, dim=1), torch.stack(present, dim=1)

    def forward(
        self,
        inputs: Mapping[str, Tensor],
        *,
        mask_modality: str | None = None,
    ) -> dict[str, Tensor]:
        device = next(self.parameters()).device
        tokens, present = self._stack(
            inputs,
            device=device,
            force_missing=mask_modality,
        )
        encoded = self.transformer(tokens)
        pooled_weights = present.float().unsqueeze(-1)
        pooled = (encoded * pooled_weights).sum(dim=1) / torch.clamp(
            pooled_weights.sum(dim=1),
            min=1.0,
        )
        fused = self.norm(pooled)
        reconstructions = {
            modality: self.reconstruction_heads[modality](fused)
            for modality in self.modalities
        }
        return {
            "embedding": fused,
            "tokens": encoded,
            "present_mask": present,
            "reconstructions": reconstructions,
        }


def train_multimodal_encoder(
    inputs: Mapping[str, Sequence[Sequence[float]]],
    *,
    config: MultimodalEncoderConfig | None = None,
    epochs: int = 100,
    learning_rate: float = 1e-3,
    mask_probability: float = 0.25,
    seed: int = 42,
) -> dict[str, Any]:
    """Self-supervised masked-modality training with a deterministic seed.

    The objective makes the fused state useful even when one modality is
    missing. It is a research pretraining objective, not a foundation-model
    scale training claim.
    """
    if epochs < 1 or epochs > 5000:
        raise ValueError("epochs must be between 1 and 5000")
    if not 0.0 <= mask_probability < 1.0:
        raise ValueError("mask_probability must be between 0 and 1")
    torch.manual_seed(seed)
    np.random.seed(seed)

    tensors = {
        str(modality): torch.tensor(np.asarray(values, dtype=np.float32))
        for modality, values in inputs.items()
    }
    dimensions = {key: int(value.shape[1]) for key, value in tensors.items()}
    if any(value.ndim != 2 for value in tensors.values()):
        raise ValueError("each modality must be a 2-D matrix")
    rows = {int(value.shape[0]) for value in tensors.values()}
    if len(rows) != 1 or not rows:
        raise ValueError("all modality matrices must have equal row counts")
    if not all(torch.isfinite(value).all() for value in tensors.values()):
        raise ValueError("modality matrices must be finite")

    model = MultimodalFinancialEncoder(dimensions, config=config)
    optimizer = torch.optim.AdamW(model.parameters(), lr=learning_rate)
    losses: list[float] = []

    for _ in range(epochs):
        model.train()
        full = model(tensors)
        masked_losses = []
        for modality in model.modalities:
            if modality not in tensors:
                continue
            if np.random.random() > mask_probability:
                continue
            masked = model(tensors, mask_modality=modality)
            target = model.projections[modality](tensors[modality])
            masked_losses.append(
                torch.mean((masked["reconstructions"][modality] - target.detach()) ** 2)
            )
            # Preserve representation consistency between full and masked states.
            masked_losses.append(
                0.25 * torch.mean((masked["embedding"] - full["embedding"].detach()) ** 2)
            )
        loss = (
            torch.stack(masked_losses).mean()
            if masked_losses
            else torch.mean(full["embedding"] ** 2) * 0.0
        )
        optimizer.zero_grad()
        loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), 5.0)
        optimizer.step()
        losses.append(float(loss.detach()))

    model.eval()
    with torch.no_grad():
        encoded = model(tensors)
    return {
        "status": "MULTIMODAL_ENCODER_RESEARCH_TRAINED",
        "modalities": list(model.modalities),
        "rows": next(iter(rows)),
        "hidden_dim": model.config.hidden_dim,
        "epochs": epochs,
        "seed": seed,
        "mask_probability": mask_probability,
        "final_loss": round(float(losses[-1]), 8),
        "missing_modality_support": True,
        "embedding_dimension": model.config.hidden_dim,
        "semantics": (
            "Self-supervised masked-modality encoder for financial state "
            "representation; not a foundation-model scale pretraining claim."
        ),
        "model": model,
        "embedding": encoded["embedding"].detach().cpu().numpy(),
    }


def encode_multimodal_state(
    model: MultimodalFinancialEncoder,
    inputs: Mapping[str, Sequence[Sequence[float]]],
    *,
    mask_modality: str | None = None,
) -> dict[str, Any]:
    tensors = {
        str(key): torch.tensor(np.asarray(value, dtype=np.float32))
        for key, value in inputs.items()
    }
    with torch.no_grad():
        result = model(tensors, mask_modality=mask_modality)
    return {
        "status": "MULTIMODAL_ENCODER_INFERENCE_READY",
        "embedding": result["embedding"].detach().cpu().numpy().tolist(),
        "present_mask": result["present_mask"].detach().cpu().numpy().tolist(),
    }
