"""Operational diagnostics for FinAI's request pipeline and research layers.

These endpoints report local configuration and file presence only. They do not
prove live provider reachability, model inference quality, or financial validity.
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Request

router = APIRouter(prefix="/api/v1/system", tags=["system"])
ROOT = Path(__file__).resolve().parents[1]

RAG_ASSETS = (
    "data/rag/finai_rag.db",
    "data/rag/embeddings/finai_rag.faiss",
    "data/rag/embeddings/document_ids.npy",
)

PROVIDER_ENV = {
    "openai": ("OPENAI_API_KEY",),
    "openrouter": ("OPENROUTER_API_KEY",),
    "anthropic": ("ANTHROPIC_API_KEY",),
    "mistral": ("MISTRAL_API_KEY",),
    "gemini": ("GEMINI_API_KEY", "GOOGLE_API_KEY"),
    "sarvam": ("SARVAM_API_KEY",),
}


def _present(*relative_paths: str) -> bool:
    return all((ROOT / path).is_file() for path in relative_paths)


def _configured_providers() -> list[str]:
    return sorted(
        name
        for name, env_names in PROVIDER_ENV.items()
        if any(os.getenv(env_name, "").strip() for env_name in env_names)
    )


@router.get("/status")
def status(request: Request) -> dict[str, Any]:
    return {
        "status": "ok",
        "app_version": request.app.version,
        "api_prefixes": [
            "/api/v1/market",
            "/api/v1/market/analyst",
            "/api/v1/crypto",
            "/api/v1/investments",
            "/api/v1/compliance",
            "/api/v1/knowledge",
            "/api/v1/resources",
            "/api/v1/models",
            "/api/v1/system",
        ],
    }


@router.get("/brain-status")
def brain_status() -> dict[str, Any]:
    """Report safe local evidence about the Brain's layers without calling providers."""
    missing_rag_assets = [
        path for path in RAG_ASSETS if not (ROOT / path).is_file()
    ]
    router_model = ROOT / "router" / "models" / "finai_router_tfidf.joblib"
    provider_names = _configured_providers()
    research_enabled = os.getenv(
        "FINAI_ENABLE_RESEARCH_PATENT_ENDPOINTS", ""
    ).strip().casefold() in {"1", "true", "yes", "on"}
    network_mode = os.getenv("FINAI_NETWORK_MODE", "online").strip().lower()
    colibri_configured = bool(os.getenv("FINAI_COLIBRI_BASE_URL", "").strip())

    return {
        "schema_version": "1.0",
        "status": "diagnostic",
        "planner_role": "local_readiness_observation_not_authorization",
        "live_checks_performed": False,
        "layers": [
            {
                "id": "routing",
                "status": "code_present" if _present(
                    "router/router_gate.py", "router/domain_router.py"
                ) else "missing_code",
                "evidence": ["router/router_gate.py", "router/domain_router.py"],
                "trained_router_artifact_present": router_model.is_file(),
            },
            {
                "id": "policy_authority",
                "status": "code_present" if _present(
                    "policy/engine.py", "orchestrator/risk_controller.py"
                ) else "missing_code",
                "evidence": ["policy/engine.py", "orchestrator/risk_controller.py"],
                "enforcement_owner": "existing_policy_authority_and_risk_control",
            },
            {
                "id": "deterministic_finance",
                "status": "code_present" if _present(
                    "orchestrator/finance_dispatcher.py"
                ) else "missing_code",
                "evidence": ["orchestrator/finance_dispatcher.py"],
            },
            {
                "id": "retrieval",
                "status": "ready_local_assets" if not missing_rag_assets else "assets_missing",
                "required_assets": list(RAG_ASSETS),
                "missing_assets": missing_rag_assets,
                "evidence": ["rag/hybrid_retriever.py", "llm/qwen_embedding_adapter.py"],
            },
            {
                "id": "model_generation",
                "status": "provider_credentials_configured" if provider_names else "no_cloud_credentials_detected",
                "configured_provider_names": provider_names,
                "secret_values_exposed": False,
                "provider_reachability_verified": False,
                "model_inference_verified": False,
            },
            {
                "id": "verification_xai",
                "status": "code_present" if _present(
                    "xai/claim_verifier.py",
                    "rag/evidence_verifier.py",
                    "xai/trace.py",
                ) else "missing_code",
                "evidence": ["xai/claim_verifier.py", "rag/evidence_verifier.py", "xai/trace.py"],
            },
            {
                "id": "adaptive_orchestration",
                "status": "code_present" if _present(
                    "orchestrator/execution_plan.py",
                    "llm/resource_orchestrator.py",
                ) else "missing_code",
                "evidence": [
                    "orchestrator/execution_plan.py",
                    "llm/resource_orchestrator.py",
                ],
                "execution_plan_is_diagnostic": True,
            },
            {
                "id": "offline_inference",
                "status": (
                    "offline_mode_requested"
                    if network_mode == "offline"
                    else "local_adapters_present_runtime_unverified"
                ) if _present(
                    "llm/rllm_finqa_adapter.py",
                    "llm/colibri_adapter.py",
                ) else "missing_local_adapter_code",
                "network_mode": network_mode,
                "colibri_configured": colibri_configured,
                "local_runtime_verified": False,
                "model_weights_presence_verified": False,
                "colibri_server_reachability_verified": False,
            },
            {
                "id": "causal_risk_research",
                "status": "code_present_experimental" if _present(
                    "app/advanced_causal_api.py",
                    "finance_engine/counterfactual_screening.py",
                    "finance_engine/counterfactual_stability.py",
                ) else "incomplete_code",
                "experimental": True,
                "production_validated": False,
                "causal_validity_proven": False,
            },
            {
                "id": "research_endpoints",
                "status": "enabled_by_environment" if research_enabled else "disabled_by_default",
                "enabled": research_enabled,
                "requires_server_side_bearer_token": True,
            },
        ],
        "security": {
            "api_auth_mode": os.getenv("FINAI_API_AUTH_MODE", "development").strip().lower(),
            "production_mode": os.getenv("FINAI_ENV", "development").strip().lower() in {"production", "prod"},
            "shared_token_value_exposed": False,
        },
        "limitations": [
            "Local file presence is not proof of successful runtime loading.",
            "Configured credentials do not prove provider reachability or successful inference.",
            "Research modules and synthetic benchmarks do not establish real-market causal validity or patentability.",
        ],
    }
