"""Opt-in persistent paper-account endpoints for SwarmTrade; no live execution."""
from __future__ import annotations

import os
from typing import Literal, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field, field_validator

from app.swarmtrade_api import SwarmTradeRequest
from swarmtrade.engine import build_swarm_plan
from swarmtrade.paper_ledger import PaperLedger, payload_digest

router = APIRouter(prefix="/api/v1/swarmtrade/paper", tags=["swarmtrade-paper"])


def _enabled() -> bool:
    return os.getenv("FINAI_ENABLE_SWARMTRADE_PAPER_LEDGER", "").strip().lower() in {"1", "true", "yes", "on"}


def _ledger() -> PaperLedger:
    if not _enabled():
        raise HTTPException(
            status_code=503,
            detail="Paper ledger is disabled. Set FINAI_ENABLE_SWARMTRADE_PAPER_LEDGER=1 for a trusted local environment.",
        )
    return PaperLedger()


class CreatePaperAccountRequest(BaseModel):
    label: str = Field(default="FinAI paper account", min_length=1, max_length=100)
    currency: str = Field(default="INR", min_length=3, max_length=3)
    initial_capital: float = Field(default=100000, gt=0, allow_inf_nan=False)


class OpenPaperPositionRequest(BaseModel):
    idempotency_key: str = Field(..., min_length=1, max_length=160)
    acknowledge_simulation_only: bool = Field(...)
    plan: SwarmTradeRequest

    @field_validator("idempotency_key")
    @classmethod
    def validate_key(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("idempotency_key must not be blank")
        return value


class ClosePaperPositionRequest(BaseModel):
    idempotency_key: str = Field(..., min_length=1, max_length=160)
    exit_price: float = Field(..., gt=0, allow_inf_nan=False)
    reason: Literal["manual", "stop", "target", "risk_control"] = "manual"

    @field_validator("idempotency_key")
    @classmethod
    def validate_key(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("idempotency_key must not be blank")
        return value


@router.get("/status")
def paper_ledger_status() -> dict:
    return {
        "status": "available" if _enabled() else "disabled",
        "enabled": _enabled(),
        "mode": "persistent_paper_trading_only",
        "real_orders_supported": False,
        "live_fills_claimed": False,
        "unrealized_pnl_included_in_equity": False,
    }


@router.post("/accounts")
def create_paper_account(request: CreatePaperAccountRequest) -> dict:
    try:
        return _ledger().create_account(
            label=request.label,
            currency=request.currency,
            initial_capital=request.initial_capital,
        )
    except HTTPException:
        raise
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.get("/accounts/{account_id}")
def get_paper_account(account_id: str) -> dict:
    try:
        return _ledger().get_account(account_id)
    except HTTPException:
        raise
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/accounts/{account_id}/positions")
def list_paper_positions(
    account_id: str,
    status: Literal["open", "closed", "all"] = "all",
) -> dict:
    try:
        return _ledger().list_positions(account_id, status=status)
    except HTTPException:
        raise
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.post("/accounts/{account_id}/positions")
def open_paper_position(account_id: str, request: OpenPaperPositionRequest) -> dict:
    if not request.acknowledge_simulation_only:
        raise HTTPException(status_code=422, detail="Explicit acknowledgement of simulation-only mode is required")
    ledger = _ledger()
    try:
        # Idempotent retries must replay before recalculating against changed account state.
        request_payload = {
            "plan_request": request.plan.model_dump(),
            "acknowledge_simulation_only": request.acknowledge_simulation_only,
        }
        request_hash = payload_digest(request_payload)
        replay = ledger.replay_if_exists(
            account_id=account_id,
            idempotency_key=request.idempotency_key,
            event_type="open",
            request_digest=request_hash,
        )
        if replay is not None:
            return replay

        snapshot = ledger.get_account(account_id)
        plan_request = request.plan.model_dump()
        # Risk sizing uses current persisted account state, never caller-reported capital/open risk.
        plan_request["capital"] = snapshot["equity_excluding_unrealized_pnl"]
        plan_request["open_position_risk_pct"] = snapshot["open_position_risk_pct"]
        plan_request["current_daily_loss_pct"] = snapshot["daily_realized_loss_pct"]
        plan = build_swarm_plan(plan_request)
        if plan.get("status") != "APPROVED_FOR_SIMULATION":
            raise HTTPException(status_code=409, detail={"message": "Risk gate blocked paper position", "plan": plan})
        return ledger.open_position(
            account_id=account_id,
            idempotency_key=request.idempotency_key,
            plan=plan,
            request_digest=request_hash,
        )
    except HTTPException:
        raise
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.post("/accounts/{account_id}/positions/{position_id}/close")
def close_paper_position(account_id: str, position_id: str, request: ClosePaperPositionRequest) -> dict:
    ledger = _ledger()
    request_payload = {
        "position_id": position_id,
        "exit_price": request.exit_price,
        "reason": request.reason,
    }
    try:
        return ledger.close_position(
            account_id=account_id,
            position_id=position_id,
            exit_price=request.exit_price,
            idempotency_key=request.idempotency_key,
            close_reason=request.reason,
            request_digest=payload_digest(request_payload),
        )
    except HTTPException:
        raise
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
