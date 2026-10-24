"""Safe simulation API for deterministic SwarmTrade planning."""
from typing import Dict, Literal, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field, field_validator

from swarmtrade.engine import MAX_LOGICAL_AGENTS, SIGNAL_NAMES, build_swarm_plan

router = APIRouter(prefix="/api/v1/swarmtrade", tags=["swarmtrade"])


class SwarmTradeRequest(BaseModel):
    symbol: str = Field(..., min_length=1, max_length=40)
    asset_class: Literal["equity", "option", "future", "crypto", "forex"] = "equity"
    side: Literal["auto", "long", "short"] = "auto"
    entry_price: float = Field(..., gt=0, allow_inf_nan=False)
    stop_price: Optional[float] = Field(default=None, gt=0, allow_inf_nan=False)
    target_price: Optional[float] = Field(default=None, gt=0, allow_inf_nan=False)
    capital: float = Field(default=100000, gt=0, allow_inf_nan=False)
    risk_pct: float = Field(default=0.5, gt=0, le=5, allow_inf_nan=False)
    open_position_risk_pct: float = Field(default=0, ge=0, le=3, allow_inf_nan=False)
    current_daily_loss_pct: float = Field(default=0, ge=0, le=20, allow_inf_nan=False)
    max_daily_loss_pct: float = Field(default=2.0, ge=0.1, le=5, allow_inf_nan=False)
    max_leverage: float = Field(default=1.0, ge=1, le=30, allow_inf_nan=False)
    margin_rate: float = Field(default=1.0, ge=0.01, le=1, allow_inf_nan=False)
    multiplier: float = Field(default=1.0, gt=0, allow_inf_nan=False)
    unit_step: float = Field(default=1.0, gt=0, allow_inf_nan=False)
    fee_bps: float = Field(default=5.0, ge=0, le=1000, allow_inf_nan=False)
    slippage_bps: float = Field(default=5.0, ge=0, le=1000, allow_inf_nan=False)
    max_loss_per_unit: Optional[float] = Field(default=None, gt=0, allow_inf_nan=False)
    tick_size: Optional[float] = Field(default=None, gt=0, allow_inf_nan=False)
    tick_value: Optional[float] = Field(default=None, gt=0, allow_inf_nan=False)
    pip_size: Optional[float] = Field(default=None, gt=0, allow_inf_nan=False)
    pip_value_per_unit: Optional[float] = Field(default=None, gt=0, allow_inf_nan=False)
    margin_per_unit: Optional[float] = Field(default=None, gt=0, allow_inf_nan=False)
    min_reward_risk: float = Field(default=1.0, ge=0.5, le=5.0, allow_inf_nan=False)
    agent_count: int = Field(default=MAX_LOGICAL_AGENTS, ge=5, le=MAX_LOGICAL_AGENTS)
    signals: Dict[str, float] = Field(default_factory=dict)

    @field_validator("symbol")
    @classmethod
    def normalize_symbol(cls, value: str) -> str:
        normalized = value.strip().upper()
        if not normalized:
            raise ValueError("symbol must not be blank")
        return normalized

    @field_validator("agent_count")
    @classmethod
    def validate_agent_count(cls, value: int) -> int:
        if value % 5 != 0:
            raise ValueError("agent_count must be a multiple of 5 to balance strategy roles")
        return value

    @field_validator("signals")
    @classmethod
    def validate_signals(cls, value: Dict[str, float]) -> Dict[str, float]:
        unknown = set(value) - SIGNAL_NAMES
        if unknown:
            raise ValueError(f"Unsupported signal(s): {', '.join(sorted(unknown))}")
        for name, score in value.items():
            if not -1 <= score <= 1:
                raise ValueError(f"Signal {name} must be between -1 and 1")
        return value


@router.get("/status")
def swarmtrade_status() -> dict:
    return {
        "service": "FinAI SwarmTrade",
        "status": "available",
        "mode": "deterministic_simulation_only",
        "max_logical_agents": MAX_LOGICAL_AGENTS,
        "min_logical_agents": 5,
        "agent_count_multiple": 5,
        "agent_roles": ["momentum", "trend", "mean_reversion", "breakout", "sentiment"],
        "risk_controls": ["max 1% single-trade risk", "max 3% aggregate open-position risk",
                          "daily-loss cutoff", "protective stop and target", "cost-aware reward/risk",
                          "margin and leverage caps"],
        "live_order_execution": False,
    }


@router.post("/plan")
def create_swarm_plan(request: SwarmTradeRequest) -> dict:
    try:
        return build_swarm_plan(request.model_dump())
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
