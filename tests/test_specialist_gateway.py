import pytest

from llm.specialist_gateway import SpecialistModelGateway


class FakeEmbeddingAdapter:

    def __init__(self):
        self.calls = []

    def embed(self, **kwargs):
        self.calls.append(kwargs)
        return [[0.1, 0.2], [0.3, 0.4]]


class FakeRerankerAdapter:

    def __init__(self):
        self.calls = []

    def rerank(self, **kwargs):
        self.calls.append(kwargs)
        return [
            {"index": 1, "score": 0.95},
            {"index": 0, "score": 0.61},
        ]


def test_register_and_embed():

    adapter = FakeEmbeddingAdapter()

    gateway = SpecialistModelGateway()

    gateway.register_embedding(
        "qwen3-embedding-0.6b",
        adapter,
        capabilities=["semantic_retrieval"],
    )

    result = gateway.embed(
        ["loan interest", "credit card"],
    )

    assert result == [
        [0.1, 0.2],
        [0.3, 0.4],
    ]

    assert len(adapter.calls) == 1


def test_register_and_rerank():

    adapter = FakeRerankerAdapter()

    gateway = SpecialistModelGateway()

    gateway.register_reranker(
        "qwen3-reranker-0.6b",
        adapter,
        capabilities=["reranking"],
    )

    result = gateway.rerank(
        query="home loan interest",
        documents=[
            "Document A",
            "Document B",
        ],
    )

    assert result[0]["score"] == 0.95
    assert result[1]["index"] == 0

    assert len(adapter.calls) == 1


def test_explicit_embedding_model_selection():

    adapter_a = FakeEmbeddingAdapter()
    adapter_b = FakeEmbeddingAdapter()

    gateway = SpecialistModelGateway()

    gateway.register_embedding(
        "model-a",
        adapter_a,
    )

    gateway.register_embedding(
        "model-b",
        adapter_b,
    )

    gateway.embed(
        ["test"],
        model_id="model-b",
    )

    assert len(adapter_a.calls) == 0
    assert len(adapter_b.calls) == 1


def test_unknown_embedding_model_fails_safely():

    gateway = SpecialistModelGateway()

    with pytest.raises(ValueError):
        gateway.embed(
            ["test"],
            model_id="missing-model",
        )


def test_unknown_reranker_model_fails_safely():

    gateway = SpecialistModelGateway()

    with pytest.raises(ValueError):
        gateway.rerank(
            query="test",
            documents=["document"],
            model_id="missing-model",
        )


def test_capabilities_are_preserved():

    gateway = SpecialistModelGateway()

    gateway.register_embedding(
        "embedding-a",
        FakeEmbeddingAdapter(),
        capabilities=[
            "semantic_retrieval",
            "multilingual_retrieval",
        ],
    )

    assert gateway.capabilities(
        "embedding-a"
    ) == [
        "semantic_retrieval",
        "multilingual_retrieval",
    ]


def test_available_models_are_sorted():

    gateway = SpecialistModelGateway()

    gateway.register_embedding(
        "z-embedding",
        FakeEmbeddingAdapter(),
    )

    gateway.register_embedding(
        "a-embedding",
        FakeEmbeddingAdapter(),
    )

    gateway.register_reranker(
        "z-reranker",
        FakeRerankerAdapter(),
    )

    gateway.register_reranker(
        "a-reranker",
        FakeRerankerAdapter(),
    )

    assert gateway.available_embedding_models() == [
        "a-embedding",
        "z-embedding",
    ]

    assert gateway.available_reranker_models() == [
        "a-reranker",
        "z-reranker",
    ]
