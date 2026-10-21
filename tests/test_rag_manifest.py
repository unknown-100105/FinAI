import hashlib
import json

from scripts.verify_rag_manifest import verify_manifest


def _hash(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _valid_manifest(root):
    source = root / "data" / "source.txt"
    artifact = root / "indexes" / "index.bin"
    source.parent.mkdir(parents=True)
    artifact.parent.mkdir(parents=True)
    source.write_text("licensed point-in-time sample", encoding="utf-8")
    artifact.write_bytes(b"index bytes")
    return {
        "schema_version": 1,
        "corpus_id": "sample-v1",
        "created_at_utc": "2026-10-21T00:00:00Z",
        "chunking": {
            "implementation": "test-chunker-v1",
            "max_tokens": 512,
            "overlap_tokens": 64,
        },
        "embedding": {
            "model_id": "test-embedding-v1",
            "dimension": 3,
        },
        "sources": [{
            "name": "sample",
            "uri": "https://example.invalid/source",
            "license": "TEST-LICENSE",
            "retrieved_at_utc": "2026-10-20T00:00:00Z",
            "source_file": "data/source.txt",
            "sha256": _hash(source),
        }],
        "artifacts": [{
            "role": "test-index",
            "path": "indexes/index.bin",
            "sha256": _hash(artifact),
        }],
    }


def test_manifest_verifies_provenance_and_artifact_hashes(tmp_path):
    manifest = _valid_manifest(tmp_path)
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    result = verify_manifest(manifest_path, tmp_path)

    assert result["status"] == "READY"
    assert result["errors"] == []


def test_manifest_detects_artifact_hash_mismatch(tmp_path):
    manifest = _valid_manifest(tmp_path)
    (tmp_path / "indexes" / "index.bin").write_bytes(b"changed")
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    result = verify_manifest(manifest_path, tmp_path)

    assert result["status"] == "INCOMPLETE"
    assert any("sha256 does not match the artifact" in error for error in result["errors"])


def test_manifest_rejects_paths_outside_root(tmp_path):
    manifest = _valid_manifest(tmp_path)
    manifest["artifacts"][0]["path"] = "../outside.bin"
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    result = verify_manifest(manifest_path, tmp_path)

    assert result["status"] == "INCOMPLETE"
    assert any("escapes the repository root" in error for error in result["errors"])
