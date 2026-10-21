from __future__ import annotations

import os
from pathlib import Path
from typing import List, Optional

import numpy as np
import torch
from sentence_transformers import SentenceTransformer

from policy.network_mode import get_network_mode


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

    def _resolve_model_source(self) -> str:
        configured_path = os.getenv("FINAI_EMBEDDING_MODEL_PATH", "").strip()
        if configured_path:
            local_path = Path(configured_path).expanduser()
            if not local_path.is_absolute():
                local_path = Path(__file__).resolve().parents[1] / local_path
            local_path = local_path.resolve()
            if not local_path.is_dir():
                raise FileNotFoundError(
                    "FINAI_EMBEDDING_MODEL_PATH does not point to an existing "
                    f"model directory: {local_path}"
                )
            return str(local_path)

        if get_network_mode() == "offline":
            # Resolve the already-cached snapshot without making a network call;
            # passing its local path to SentenceTransformer prevents a hidden fetch.
            try:
                from huggingface_hub import snapshot_download

                return snapshot_download(
                    repo_id=self.hf_model_id,
                    local_files_only=True,
                )
            except Exception as exc:
                raise FileNotFoundError(
                    f"Embedding model '{self.hf_model_id}' is not available in the "
                    "local Hugging Face cache. Pre-download it while online or set "
                    "FINAI_EMBEDDING_MODEL_PATH to an existing local model directory."
                ) from exc

        return self.hf_model_id

    def _load(self) -> SentenceTransformer:
        if self._model is None:
            model_source = self._resolve_model_source()
            self._model = SentenceTransformer(
                model_source,
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
