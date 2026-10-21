"""Tests for the local-only FinAI artifact readiness audit."""

import json

from scripts.finai_preflight import audit, main


def test_preflight_reports_missing_router_and_rag_assets_without_network_calls(tmp_path, monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "do-not-print-this-secret")
    monkeypatch.setenv(
        "FINAI_COLIBRI_BASE_URL",
        "http://127.0.0.1:8000/v1",
    )
    monkeypatch.setenv("FINAI_COLIBRI_API_KEY", "local-api-secret")
    report = audit(tmp_path)

    assert report["scope"] == "local_presence_check_only_no_network_calls"
    assert report["artifacts"]["router_model_present"] is False
    assert len(report["artifacts"]["rag_source_chunks_missing"]) == 2
    assert len(report["artifacts"]["rag_assets_missing"]) == 3
    assert report["provider_credentials"]["configured_provider_names"] == ["gemini"]
    assert report["provider_credentials"]["secret_values_exposed"] is False
    assert report["provider_credentials"]["reachability_verified"] is False
    assert report["local_inference"]["colibri_configured"] is True
    assert report["local_inference"]["colibri_model"] == "olmoe-colibri"
    assert report["local_inference"]["colibri_server_reachability_verified"] is False
    assert report["local_inference"]["api_key_values_exposed"] is False

    serialized = json.dumps(report)
    assert "do-not-print-this-secret" not in serialized
    assert "local-api-secret" not in serialized


def test_preflight_emits_machine_readable_json_and_strict_exit_code(tmp_path, capsys):
    assert main(["--root", str(tmp_path), "--json"]) == 0
    output = capsys.readouterr().out
    decoded = json.loads(output)
    assert decoded["schema_version"] == "1.0"

    assert main(["--root", str(tmp_path), "--strict", "--json"]) == 1
    strict_output = capsys.readouterr().out
    assert json.loads(strict_output)["artifacts"]["rag_assets_ready"] is False


def test_preflight_marks_rag_ready_only_when_all_assets_exist(tmp_path):
    required = (
        "data/rag/finai_rag.db",
        "data/rag/embeddings/finai_rag.faiss",
        "data/rag/embeddings/document_ids.npy",
    )
    for relative in required:
        path = tmp_path / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b"placeholder")

    report = audit(tmp_path)
    assert report["artifacts"]["rag_assets_ready"] is True
    assert report["artifacts"]["rag_assets_missing"] == []
