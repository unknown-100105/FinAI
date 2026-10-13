"""Integrity checks for resumable FAISS construction."""

import pytest

from scripts.build_rag_faiss import MODEL_ID, validate_resume_state


def test_empty_index_starts_from_zero():
    assert validate_resume_state(
        vector_count=0,
        document_ids=[],
        checkpoint={"last_id": 0, "indexed_count": 0},
        checkpoint_exists=False,
    ) == (0, 0)


def test_valid_checkpoint_resumes_from_last_indexed_document():
    ids = [2, 5, 8]
    assert validate_resume_state(
        vector_count=3,
        document_ids=ids,
        checkpoint={
            "model_id": MODEL_ID,
            "last_id": 8,
            "indexed_count": 3,
        },
        checkpoint_exists=True,
    ) == (8, 3)


def test_stale_checkpoint_recovers_from_aligned_id_map():
    ids = [2, 5, 8]
    assert validate_resume_state(
        vector_count=3,
        document_ids=ids,
        checkpoint={
            "model_id": MODEL_ID,
            "last_id": 2,
            "indexed_count": 1,
        },
        checkpoint_exists=True,
    ) == (8, 3)


def test_vector_count_mismatch_fails_closed():
    with pytest.raises(ValueError, match="vector count does not match"):
        validate_resume_state(
            vector_count=3,
            document_ids=[2, 5],
            checkpoint={},
            checkpoint_exists=False,
        )


def test_duplicate_or_unsorted_document_ids_fail_closed():
    with pytest.raises(ValueError, match="strictly increasing"):
        validate_resume_state(
            vector_count=3,
            document_ids=[2, 2, 8],
            checkpoint={},
            checkpoint_exists=False,
        )


def test_mismatched_embedding_model_checkpoint_is_rejected():
    with pytest.raises(ValueError, match="does not match index builder model"):
        validate_resume_state(
            vector_count=1,
            document_ids=[3],
            checkpoint={
                "model_id": "some-other-model",
                "last_id": 3,
                "indexed_count": 1,
            },
            checkpoint_exists=True,
        )


def test_checkpoint_must_match_the_saved_id_map_prefix():
    with pytest.raises(ValueError, match="last_id does not match"):
        validate_resume_state(
            vector_count=2,
            document_ids=[2, 8],
            checkpoint={
                "model_id": MODEL_ID,
                "last_id": 7,
                "indexed_count": 1,
            },
            checkpoint_exists=True,
        )


def test_nonempty_index_without_checkpoint_fails_closed():
    with pytest.raises(ValueError, match="no checkpoint.json"):
        validate_resume_state(
            vector_count=1,
            document_ids=[3],
            checkpoint={},
            checkpoint_exists=False,
        )
