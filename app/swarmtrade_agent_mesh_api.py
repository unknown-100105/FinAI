"""API for provenance-aware multi-agent research runs; never submits orders."""
from typing import List, Literal

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from swarmtrade.agent_mesh import AgentEvidenceStore

router = APIRouter(prefix="/api/v1/swarmtrade/agent-mesh", tags=["swarmtrade-agent-mesh"])
store = AgentEvidenceStore()


class AgentRunRequest(BaseModel):
    symbol: str = Field(..., min_length=1, max_length=64)
    asset_class: Literal["equity", "option", "future", "crypto", "forex"]
    venue: str = Field(default="UNKNOWN", min_length=1, max_length=64)
    timeframe: str = Field(default="1d", min_length=1, max_length=32)


class AgentEvidenceRequest(BaseModel):
    evidence_id: str | None = Field(default=None, max_length=128)
    agent_id: str = Field(..., min_length=1, max_length=128)
    role: Literal[
        "data_quality", "news", "macro", "fundamentals", "technical", "liquidity",
        "volatility", "derivatives", "strategy", "adversarial", "portfolio", "risk",
        "execution_review",
    ]
    agent_version: str = Field(..., min_length=1, max_length=128)
    instrument: str = Field(..., min_length=1, max_length=128)
    claim: str = Field(..., min_length=1, max_length=4000)
    source_ids: List[str] = Field(..., min_length=1, max_length=20)
    source_timestamp: str = Field(..., min_length=1, max_length=64)
    observed_at: str = Field(..., min_length=1, max_length=64)
    confidence: float = Field(..., ge=0, le=1, allow_inf_nan=False)
    stance: Literal["bullish", "bearish", "neutral", "abstain"]
    invalidation: str = Field(default="", max_length=1000)
    missing_data: List[str] = Field(default_factory=list, max_length=30)


@router.get("/status")
def agent_mesh_status() -> dict:
    return {
        "service": "FinAI SwarmTrade Agent Mesh",
        "status": "available",
        "mode": "research_only",
        "max_evidence_per_run": 300,
        "roles": [
            "data_quality", "news", "macro", "fundamentals", "technical", "liquidity",
            "volatility", "derivatives", "strategy", "adversarial", "portfolio", "risk",
            "execution_review",
        ],
        "persistent_shared_evidence": True,
        "trade_signal_authority": False,
        "live_order_execution": False,
    }


@router.post("/runs")
def create_agent_run(request: AgentRunRequest) -> dict:
    try:
        return store.create_run(request.model_dump())
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.post("/runs/{run_id}/evidence")
def submit_agent_evidence(run_id: str, request: AgentEvidenceRequest) -> dict:
    try:
        return store.add_evidence(run_id, request.model_dump())
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc).strip("'")) from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except Exception as exc:
        # Avoid exposing SQL details or payloads in public API errors.
        if "UNIQUE constraint failed" in str(exc):
            raise HTTPException(status_code=409, detail="Duplicate evidence ID for this run") from exc
        raise


@router.get("/runs/{run_id}/summary")
def summarize_agent_run(run_id: str) -> dict:
    try:
        return store.summary(run_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc).strip("'")) from exc
