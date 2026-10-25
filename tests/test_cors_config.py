from __future__ import annotations

import pytest

from app.main import _cors_allowed_origins


def test_development_cors_defaults_are_localhost_only():
    origins = _cors_allowed_origins(environment="development", configured="")
    assert origins == [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
    ]


def test_production_cors_fails_closed_without_explicit_origins():
    assert _cors_allowed_origins(environment="production", configured="") == []


def test_production_cors_accepts_explicit_origins_and_deduplicates():
    origins = _cors_allowed_origins(
        environment="production",
        configured="https://finai.example, https://admin.example/, https://finai.example",
    )
    assert origins == ["https://finai.example", "https://admin.example"]


def test_credentialed_cors_rejects_wildcard():
    with pytest.raises(ValueError, match="must not contain"):
        _cors_allowed_origins(
            environment="production",
            configured="https://finai.example, *",
        )



def test_production_cors_rejects_plain_http_origins():
    with pytest.raises(ValueError, match="must use HTTPS"):
        _cors_allowed_origins(
            environment="production",
            configured="http://finai.example",
        )
