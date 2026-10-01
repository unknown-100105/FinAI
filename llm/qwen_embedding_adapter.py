from __future__ import annotations

from typing import List, Optional

import numpy as np
import torch
from sentence_transformers import SentenceTransformer


class QwenEmbeddingAdapter:

    FINAI_MODEL_ID = "qwen3-embedding-0.6b"
    HF_MODEL_ID = "Qwen/Qwen3-Embedding-0.6B"

    def __init__(
        self,
        device: Optional[str] = None,
        max_seq_length: Optional[int] = None,
    ):
        self.model_id = self.FINAI_MODEL_ID
        self.hf_model_id = self.HF_MODEL_ID

        self.device = (
            device
            or ("cuda" if torch.cuda.is_available() else "cpu")
        )

        self.max_seq_length = max_seq_length
        self._model = None

    def _load(self) -> SentenceTransformer:
        if self._model is None:
            self._model = SentenceTransformer(
                self.hf_model_id,
                device=self.device,
            )

            if self.max_seq_length is not None:
                if self.max_seq_length <= 0:
                    raise ValueError(
                        "max_seq_length must be positive."
                    )

                self._model.max_seq_length = (
                    self.max_seq_length
                )

        return self._model

    def embed(
        self,
        texts: List[str],
        *,
        is_query: bool = True,
        batch_size: int = 32,
        normalize_embeddings: bool = True,
    ) -> np.ndarray:

        if not isinstance(texts, list):
            raise TypeError(
                "texts must be a list of strings."
            )

        if not texts:
            raise ValueError(
                "texts cannot be empty."
            )

        if not all(
            isinstance(text, str) and text.strip()
            for text in texts
        ):
            raise ValueError(
                "texts must contain non-empty strings."
            )

        model = self._load()

        if is_query and hasattr(model, "encode_query"):
            embeddings = model.encode_query(
                texts,
                batch_size=batch_size,
                normalize_embeddings=normalize_embeddings,
                convert_to_numpy=True,
                show_progress_bar=False,
            )
        elif not is_query and hasattr(model, "encode_document"):
            embeddings = model.encode_document(
                texts,
                batch_size=batch_size,
                normalize_embeddings=normalize_embeddings,
                convert_to_numpy=True,
                show_progress_bar=False,
            )
        else:
            embeddings = model.encode(
                texts,
                batch_size=batch_size,
                normalize_embeddings=normalize_embeddings,
                convert_to_numpy=True,
                show_progress_bar=False,
            )

        embeddings = np.asarray(
            embeddings,
            dtype=np.float32,
        )

        if normalize_embeddings:
            norms = np.linalg.norm(
                embeddings,
                axis=1,
                keepdims=True,
            )

            embeddings = embeddings / np.clip(
                norms,
                1e-12,
                None,
            )

        return embeddings

    def embedding_dimension(self) -> int:
        model = self._load()

        if hasattr(model, "get_embedding_dimension"):
            dimension = model.get_embedding_dimension()
        else:
            dimension = (
                model.get_sentence_embedding_dimension()
            )

        if dimension is None:
            raise RuntimeError(
                "Embedding dimension is unavailable."
            )

        return int(dimension)

    @property
    def loaded(self) -> bool:
        return self._model is not None
