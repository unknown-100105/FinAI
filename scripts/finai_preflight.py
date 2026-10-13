"""Offline readiness audit for a FinAI checkout.

This script checks local file and Python-package presence only. It never prints
secret values, downloads models or data, contacts providers, or modifies files.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import os
import platform
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]

REQUIRED_PACKAGES = (
    "fastapi",
    "pydantic",
    "sklearn",
    "numpy",
    "joblib",
    "requests",
    "yfinance",
    "ccxt",
    "torch",
    "transformers",
    "peft",
    "bitsandbytes",
    "accelerate",
    "sentencepiece",
    "faiss",
    "sentence_transformers",
    "openai",
)
PROVIDER_KEY_NAMES = (
    "GEMINI_API_KEY",
    "OPENAI_API_KEY",
    "OPENROUTER_API_KEY",
    "ANTHROPIC_API_KEY",
    "MISTRAL_API_KEY",
)


def _file_check(root: Path, relative_path: str, *, required: bool) -> dict[str, Any]:
    path = root / relative_path
    present = path.is_file()
    return {
        "path": relative_path,
        "present": present,
        "required_for_full_readiness": required,
    }


def audit(root: Path = ROOT) -> dict[str, Any]:
    """Return a deterministic, local-only report for the given checkout."""
    root = Path(root).resolve()
    router_model = root / "router" / "models" / "finai_router_tfidf.joblib"
    router_metadata = router_model.with_suffix(".json")
    source_chunks = (
        "data/domain_chunks/finllm_india_clean_chunks.jsonl",
        "data/domain_chunks/indian_financial_news_clean_chunks.jsonl",
    )
    rag_assets = (
        "data/rag/finai_rag.db",
        "data/rag/embeddings/finai_rag.faiss",
        "data/rag/embeddings/document_ids.npy",
    )

    files = [
        _file_check(
            root,
            "requirements.txt",
            required=True,
        ),
        _file_check(
            root,
            "app/main.py",
            required=True,
        ),
        _file_check(
            root,
            "router/train_tfidf_router.py",
            required=True,
        ),
        _file_check(
            root,
            "scripts/build_rag_index.py",
            required=True,
        ),
        _file_check(
            root,
            "scripts/build_rag_faiss.py",
            required=True,
        ),
        _file_check(
            root,
            "frontend/package-lock.json",
            required=True,
        ),
        _file_check(
            root,
            "data/financial_intents.jsonl",
            required=False,
        ),
        _file_check(
            root,
            "router/models/finai_router_tfidf.joblib",
            required=False,
        ),
        _file_check(
            root,
            "router/models/finai_router_tfidf.json",
            required=False,
        ),
        *(_file_check(root, path, required=False) for path in source_chunks),
        *(_file_check(root, path, required=False) for path in rag_assets),
    ]

    package_status = {}
    for package in REQUIRED_PACKAGES:
        try:
            package_status[package] = importlib.util.find_spec(package) is not None
        except (ImportError, ValueError, ModuleNotFoundError):
            package_status[package] = False

    configured_providers = [
        key.removesuffix("_API_KEY").lower()
        for key in PROVIDER_KEY_NAMES
        if os.getenv(key, "").strip()
    ]

    missing_router_inputs = [
        path
        for path in (
            "data/sft_v3_work/finai_v3_router_train_v3.jsonl",
            "data/sft_v3_work/finai_v3_router_train.jsonl",
            "data/sft_v3_work/router_train.jsonl",
            "data/sft_v3_work/finai_v3_router_pool_train.jsonl",
        )
        if not (root / path).is_file()
    ]
    available_router_inputs = [
        path for path in (
            "data/sft_v3_work/finai_v3_router_train_v3.jsonl",
            "data/sft_v3_work/finai_v3_router_train.jsonl",
            "data/sft_v3_work/router_train.jsonl",
            "data/sft_v3_work/finai_v3_router_pool_train.jsonl",
        ) if (root / path).is_file()
    ]

    missing_source_chunks = [
        path for path in source_chunks if not (root / path).is_file()
    ]
    missing_rag_assets = [
        path for path in rag_assets if not (root / path).is_file()
    ]

    return {
        "schema_version": "1.0",
        "scope": "local_presence_check_only_no_network_calls",
        "checkout": {
            "root": str(root),
            "python_version": platform.python_version(),
            "platform": platform.platform(),
            "python_executable": sys.executable,
        },
        "files": files,
        "packages": package_status,
        "provider_credentials": {
            "configured_provider_names": configured_providers,
            "secret_values_exposed": False,
            "reachability_verified": False,
        },
        "artifacts": {
            "router_model_present": router_model.is_file(),
            "router_metadata_present": router_metadata.is_file(),
            "router_training_inputs_available": available_router_inputs,
            "router_training_inputs_checked": missing_router_inputs,
            "rag_source_chunks_missing": missing_source_chunks,
            "rag_assets_missing": missing_rag_assets,
            "rag_assets_ready": not missing_rag_assets,
        },
        "next_steps": _next_steps(
            root=root,
            package_status=package_status,
            router_model_present=router_model.is_file(),
            router_training_inputs_available=available_router_inputs,
            missing_source_chunks=missing_source_chunks,
            missing_rag_assets=missing_rag_assets,
        ),
    }


def _next_steps(
    *,
    root: Path,
    package_status: dict[str, bool],
    router_model_present: bool,
    router_training_inputs_available: list[str],
    missing_source_chunks: list[str],
    missing_rag_assets: list[str],
) -> list[str]:
    steps = []
    missing_packages = sorted(name for name, present in package_status.items() if not present)
    if missing_packages:
        steps.append(
            "Install project dependencies in the active interpreter; missing packages: "
            + ", ".join(missing_packages)
        )
    if not router_model_present:
        if router_training_inputs_available:
            steps.append(
                "Build the router artifact from the available approved training file with "
                "router/train_tfidf_router.py --train <path>."
            )
        else:
            steps.append(
                "Obtain or generate the approved router training JSONL; no known default "
                "training input was found, so the router model cannot be rebuilt from this clone alone."
            )
    if missing_source_chunks:
        steps.append(
            "Obtain approved/licensed RAG source chunks for: "
            + ", ".join(missing_source_chunks)
            + ". Record source, license, and retrieval date; no data is downloaded automatically."
        )
    if missing_rag_assets:
        steps.append(
            "After preparing source chunks, run scripts/build_rag_index.py and then "
            "scripts/build_rag_faiss.py; missing generated assets: "
            + ", ".join(missing_rag_assets)
        )
    if not steps:
        steps.append(
            "Required local files and checked package imports are present. Run the backend "
            "test suite, frontend build/lint, and explicit provider/runtime smoke tests next."
        )
    return steps


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT, help="FinAI checkout root")
    parser.add_argument("--json", action="store_true", help="emit machine-readable JSON")
    parser.add_argument(
        "--strict",
        action="store_true",
        help="exit nonzero when any full-readiness file, package, or generated artifact is missing",
    )
    args = parser.parse_args(argv)
    report = audit(args.root)

    missing_required_files = [
        item["path"] for item in report["files"]
        if item["required_for_full_readiness"] and not item["present"]
    ]
    missing_packages = [
        name for name, present in report["packages"].items() if not present
    ]
    missing_artifacts = list(report["artifacts"]["rag_assets_missing"])
    missing_artifacts.extend(
        path for path in report["artifacts"]["rag_source_chunks_missing"]
        if path not in missing_artifacts
    )
    if (
        not report["artifacts"]["router_model_present"]
        and "router/models/finai_router_tfidf.joblib" not in missing_artifacts
    ):
        missing_artifacts.append("router/models/finai_router_tfidf.joblib")
    if (
        not report["artifacts"]["router_training_inputs_available"]
        and not report["artifacts"]["router_model_present"]
    ):
        missing_artifacts.append("approved router training JSONL (one of the known paths)")

    if args.json:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        print("FinAI local preflight")
        print(f"Checkout: {report['checkout']['root']}")
        print(f"Python: {report['checkout']['python_version']}")
        print("\nPackages:")
        for name, present in report["packages"].items():
            print(f"  {'OK' if present else 'MISSING':7} {name}")
        print("\nArtifacts:")
        print(f"  Router model: {'present' if report['artifacts']['router_model_present'] else 'missing'}")
        print(f"  RAG ready:    {'yes' if report['artifacts']['rag_assets_ready'] else 'no'}")
        print(f"  RAG source chunks missing: {len(report['artifacts']['rag_source_chunks_missing'])}")
        print("\nConfigured provider names (keys are never shown): "
              + (", ".join(report["provider_credentials"]["configured_provider_names"]) or "none"))
        print("Provider reachability was not tested.")
        print("\nNext steps:")
        for index, item in enumerate(report["next_steps"], 1):
            print(f"  {index}. {item}")

    if args.strict and (missing_required_files or missing_packages or missing_artifacts):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
