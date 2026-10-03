import os
from unittest.mock import patch

from llm.model_registry import enabled_models


def test_openai_model_is_enabled_when_api_key_exists():
    with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}, clear=False):
        model_ids = {spec.model_id for spec in enabled_models()}

    assert "openai-luna" in model_ids


def test_openai_model_is_optional_without_api_key():
    with patch.dict(os.environ, {}, clear=True):
        model_ids = {spec.model_id for spec in enabled_models()}

    assert "openai-luna" not in model_ids
