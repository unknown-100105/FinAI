"""Validate RAG corpus provenance and generated-artifact fingerprints.

This verifier is local-only: it reads the manifest and files, never downloads
sources or modifies the corpus. A valid manifest proves identity/provenance, not
factual correctness or retrieval quality.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _resolve_inside_root(root: Path, relative_path: str) -> Path:
    candidate = (root / relative_path).resolve()
    if not candidate.is_relative_to(root.resolve()):
        raise ValueError("Path escapes the repository root.")
    return candidate


def verify_manifest(manifest_path: Path, root: Path = ROOT) -> dict[str, Any]:
    root = Path(root).resolve()
    manifest_path = Path(manifest_path)
    if not manifest_path.is_absolute():
        manifest_path = root / manifest_path
    errors: list[str] = []

    try:
        manifest_path = manifest_path.resolve()
        if not manifest_path.is_relative_to(root):
            raise ValueError("Manifest path escapes the repository root.")
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        return {"status": "INCOMPLETE", "errors": [f"Cannot read manifest: {exc}"]}

    if not isinstance(manifest, dict):
        return {"status": "INCOMPLETE", "errors": ["Manifest root must be a JSON object."]}

    if not manifest.get("corpus_id") or str(manifest["corpus_id"]).startswith("REPLACE_"):
        errors.append("corpus_id must identify an approved, immutable corpus version.")
    if not manifest.get("created_at_utc"):
        errors.append("created_at_utc is required.")

    chunking = manifest.get("chunking") or {}
    max_tokens = chunking.get("max_tokens")
    overlap = chunking.get("overlap_tokens")
    if not isinstance(max_tokens, int) or max_tokens <= 0:
        errors.append("chunking.max_tokens must be a positive integer.")
    if not isinstance(overlap, int) or overlap < 0 or (isinstance(max_tokens, int) and overlap >= max_tokens):
        errors.append("chunking.overlap_tokens must be nonnegative and smaller than max_tokens.")

    embedding = manifest.get("embedding") or {}
    if not embedding.get("model_id") or str(embedding["model_id"]).startswith("REQUIRED_"):
        errors.append("embedding.model_id must be the exact model identifier.")
    if not isinstance(embedding.get("dimension"), int) or embedding["dimension"] <= 0:
        errors.append("embedding.dimension must be a positive integer.")

    sources = manifest.get("sources")
    if not isinstance(sources, list) or not sources:
        errors.append("At least one source with license and provenance metadata is required.")
    else:
        for index, source in enumerate(sources):
            prefix = f"sources[{index}]"
            for field in ("name", "uri", "license", "retrieved_at_utc", "source_file", "sha256"):
                if not source.get(field) or str(source.get(field)).startswith(("REPLACE_", "REQUIRED_")):
                    errors.append(f"{prefix}.{field} is missing or a placeholder.")
            if source.get("source_file") and source.get("sha256"):
                try:
                    source_path = _resolve_inside_root(root, source["source_file"])
                    if not source_path.is_file():
                        errors.append(f"{prefix}.source_file does not exist.")
                    elif _sha256(source_path) != str(source["sha256"]).lower():
                        errors.append(f"{prefix}.sha256 does not match source_file.")
                except (OSError, ValueError) as exc:
                    errors.append(f"{prefix}.source_file is invalid: {exc}")

    artifacts = manifest.get("artifacts")
    if not isinstance(artifacts, list) or not artifacts:
        errors.append("At least one generated artifact with a SHA-256 fingerprint is required.")
    else:
        for index, artifact in enumerate(artifacts):
            prefix = f"artifacts[{index}]"
            if not artifact.get("role"):
                errors.append(f"{prefix}.role is required.")
            path_value = artifact.get("path")
            expected_hash = artifact.get("sha256")
            if not path_value or str(path_value).startswith(("REPLACE_", "REQUIRED_")):
                errors.append(f"{prefix}.path is missing or a placeholder.")
                continue
            if not expected_hash or str(expected_hash).startswith(("REPLACE_", "REQUIRED_")):
                errors.append(f"{prefix}.sha256 is missing or a placeholder.")
                continue
            try:
                artifact_path = _resolve_inside_root(root, path_value)
                if not artifact_path.is_file():
                    errors.append(f"{prefix}.path does not exist.")
                elif _sha256(artifact_path) != str(expected_hash).lower():
                    errors.append(f"{prefix}.sha256 does not match the artifact.")
            except (OSError, ValueError) as exc:
                errors.append(f"{prefix}.path is invalid: {exc}")

    return {
        "status": "READY" if not errors else "INCOMPLETE",
        "manifest": str(manifest_path.relative_to(root)),
        "errors": errors,
        "note": "Manifest readiness does not prove factual correctness or retrieval quality.",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", default="configs/rag-artifact-manifest.json")
    parser.add_argument("--root", type=Path, default=ROOT)
    args = parser.parse_args()
    result = verify_manifest(Path(args.manifest), args.root)
    print(json.dumps(result, indent=2))
    return 0 if result["status"] == "READY" else 1


if __name__ == "__main__":
    raise SystemExit(main())
