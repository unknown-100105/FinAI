from typing import Any, Dict, List, Optional


class SpecialistModelGateway:

    def __init__(
        self,
        default_embedding_model: str = "qwen3-embedding-0.6b",
        default_reranker_model: str = "qwen3-reranker-0.6b",
    ):
        self.default_embedding_model = default_embedding_model
        self.default_reranker_model = default_reranker_model

        self._embedding_adapters: Dict[str, Any] = {}
        self._reranker_adapters: Dict[str, Any] = {}

        self._capabilities: Dict[str, List[str]] = {}

    def register_embedding(
        self,
        model_id: str,
        adapter: Any,
        capabilities: Optional[List[str]] = None,
    ) -> None:

        model_id = str(model_id).strip().lower()

        if not model_id:
            raise ValueError(
                "model_id cannot be empty."
            )

        if adapter is None:
            raise ValueError(
                f"Adapter for '{model_id}' cannot be None."
            )

        if not hasattr(adapter, "embed"):
            raise TypeError(
                f"Embedding adapter '{model_id}' must provide "
                "'embed(...)'."
            )

        self._embedding_adapters[model_id] = adapter
        self._capabilities[model_id] = list(
            capabilities or ["semantic_retrieval"]
        )

    def register_reranker(
        self,
        model_id: str,
        adapter: Any,
        capabilities: Optional[List[str]] = None,
    ) -> None:

        model_id = str(model_id).strip().lower()

        if not model_id:
            raise ValueError(
                "model_id cannot be empty."
            )

        if adapter is None:
            raise ValueError(
                f"Adapter for '{model_id}' cannot be None."
            )

        if not hasattr(adapter, "rerank"):
            raise TypeError(
                f"Reranker adapter '{model_id}' must provide "
                "'rerank(...)'."
            )

        self._reranker_adapters[model_id] = adapter
        self._capabilities[model_id] = list(
            capabilities or ["reranking"]
        )

    def available_embedding_models(self) -> list:
        return sorted(
            self._embedding_adapters.keys()
        )

    def available_reranker_models(self) -> list:
        return sorted(
            self._reranker_adapters.keys()
        )

    def capabilities(self, model_id: str) -> list:

        model_id = str(model_id).strip().lower()

        if model_id not in self._capabilities:
            raise ValueError(
                f"Model '{model_id}' is not registered."
            )

        return list(
            self._capabilities[model_id]
        )

    def embed(
        self,
        texts: List[str],
        model_id: Optional[str] = None,
        **kwargs,
    ) -> Any:

        selected_model = (
            str(model_id).strip().lower()
            if model_id is not None
            else self.default_embedding_model
        )

        if selected_model not in self._embedding_adapters:
            available = ", ".join(
                self.available_embedding_models()
            )

            raise ValueError(
                f"Embedding model '{selected_model}' "
                f"is not registered. "
                f"Available: {available or 'none'}"
            )

        result = self._embedding_adapters[
            selected_model
        ].embed(
            texts=texts,
            **kwargs,
        )

        return result

    def rerank(
        self,
        query: str,
        documents: List[str],
        model_id: Optional[str] = None,
        **kwargs,
    ) -> Any:

        selected_model = (
            str(model_id).strip().lower()
            if model_id is not None
            else self.default_reranker_model
        )

        if selected_model not in self._reranker_adapters:
            available = ", ".join(
                self.available_reranker_models()
            )

            raise ValueError(
                f"Reranker model '{selected_model}' "
                f"is not registered. "
                f"Available: {available or 'none'}"
            )

        result = self._reranker_adapters[
            selected_model
        ].rerank(
            query=query,
            documents=documents,
            **kwargs,
        )

        return result
