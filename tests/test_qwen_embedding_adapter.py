import numpy as np
import pytest

import llm.qwen_embedding_adapter as module
from llm.qwen_embedding_adapter import QwenEmbeddingAdapter


class FakeModel:

    def __init__(self):
        self.query_calls = []
        self.document_calls = []
        self.encode_calls = []

    def encode_query(self, texts, **kwargs):
        self.query_calls.append((texts, kwargs))
        return np.array(
            [
                [1.0, 0.0],
                [0.0, 1.0],
            ],
            dtype=np.float32,
        )

    def encode_document(self, texts, **kwargs):
        self.document_calls.append((texts, kwargs))
        return np.array(
            [
                [0.5, 0.5],
                [0.2, 0.8],
            ],
            dtype=np.float32,
        )

    def encode(self, texts, **kwargs):
        self.encode_calls.append((texts, kwargs))
        return np.array(
            [
                [0.3, 0.7],
                [0.6, 0.4],
            ],
            dtype=np.float32,
        )

    def get_sentence_embedding_dimension(self):
        return 2


def test_adapter_is_lazy(monkeypatch):

    created = []

    def fake_sentence_transformer(*args, **kwargs):
        created.append((args, kwargs))
        return FakeModel()

    monkeypatch.setattr(
        module,
        "SentenceTransformer",
        fake_sentence_transformer,
    )

    adapter = QwenEmbeddingAdapter(
        device="cpu"
    )

    assert adapter.model_id == "qwen3-embedding-0.6b"
    assert adapter.hf_model_id == "Qwen/Qwen3-Embedding-0.6B"
    assert adapter.loaded is False
    assert created == []


def test_query_embedding(monkeypatch):

    fake = FakeModel()

    monkeypatch.setattr(
        module,
        "SentenceTransformer",
        lambda *args, **kwargs: fake,
    )

    adapter = QwenEmbeddingAdapter(
        device="cpu"
    )

    result = adapter.embed(
        ["query one", "query two"]
    )

    assert result.shape == (2, 2)
    assert result.dtype == np.float32
    assert len(fake.query_calls) == 1
    assert len(fake.document_calls) == 0
    assert adapter.loaded is True


def test_document_embedding(monkeypatch):

    fake = FakeModel()

    monkeypatch.setattr(
        module,
        "SentenceTransformer",
        lambda *args, **kwargs: fake,
    )

    adapter = QwenEmbeddingAdapter(
        device="cpu"
    )

    result = adapter.embed(
        ["doc one", "doc two"],
        is_query=False,
    )

    assert result.shape == (2, 2)
    assert result.dtype == np.float32
    assert len(fake.document_calls) == 1


def test_embedding_dimension(monkeypatch):

    fake = FakeModel()

    monkeypatch.setattr(
        module,
        "SentenceTransformer",
        lambda *args, **kwargs: fake,
    )

    adapter = QwenEmbeddingAdapter(
        device="cpu"
    )

    assert adapter.embedding_dimension() == 2


def test_empty_texts_rejected():

    adapter = QwenEmbeddingAdapter(
        device="cpu"
    )

    with pytest.raises(ValueError):
        adapter.embed([])


def test_invalid_texts_rejected():

    adapter = QwenEmbeddingAdapter(
        device="cpu"
    )

    with pytest.raises(ValueError):
        adapter.embed(["valid", ""])


def test_non_list_texts_rejected():

    adapter = QwenEmbeddingAdapter(
        device="cpu"
    )

    with pytest.raises(TypeError):
        adapter.embed("single string")
