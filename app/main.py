import os
from pathlib import Path
from typing import Any, Dict, Optional
from uuid import uuid4

from dotenv import load_dotenv

# Load developer-local environment values before importing routers that gate
# optional providers or research features. Existing shell/CI values take priority.
ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env", override=False)

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from app.api_security import FinAIAPIAuthMiddleware
from pydantic import BaseModel, Field

from orchestrator.session_xai import XAISessionOrchestrator

from market_data.service import MarketDataService
from app.market_api import router as market_router
from app.market_analyst_api import router as market_analyst_router
from app.crypto_api import router as crypto_router
from app.investment_api import router as investment_router
from app.compliance_api import router as compliance_router
from app.knowledge_api import router as knowledge_router
from app.investment_routes_api import router as investment_routes_router
from app.resources_api import router as resources_router
from app.models_api import router as models_router
from app.system_api import router as system_router
from app.local_model_api import router as local_model_router
from app.xai_router import router as xai_router
from app.market_intelligence_api import router as market_intelligence_router
from app.investment_knowledge_api import router as investment_knowledge_router
from app.causal_risk_api import router as causal_risk_router
from app.advanced_causal_api import router as advanced_causal_router
from app.retrieval_lab_api import router as retrieval_lab_router
from app.research_control_api import router as research_control_router
from app.swarmtrade_api import router as swarmtrade_router
from app.swarmtrade_paper_api import router as swarmtrade_paper_router


APP_VERSION = "0.1.0"

app = FastAPI(
    title="FinAI API",
    version=APP_VERSION,
    description=(
        "End-to-end API for the FinAI financial assistant. "
        "Requests flow through routing, policy, execution, "
        "response handling, and XAI tracing."
    ),
)

def _cors_allowed_origins(
    environment: str | None = None,
    configured: str | None = None,
) -> list[str]:
    """Return an explicit CORS allowlist; production never inherits dev origins."""
    env_name = (environment if environment is not None else os.getenv("FINAI_ENV", "development")).strip().casefold()
    raw = configured if configured is not None else os.getenv("FINAI_CORS_ALLOW_ORIGINS", "")
    origins = list(dict.fromkeys(item.strip().rstrip("/") for item in raw.split(",") if item.strip()))
    if origins:
        if "*" in origins:
            raise ValueError("FINAI_CORS_ALLOW_ORIGINS must not contain '*' when credentials are enabled")
        return origins
    if env_name in {"production", "prod"}:
        return []
    return [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
    ]


# Localhost origins are defaults only in development. Production must provide
# an explicit comma-separated FINAI_CORS_ALLOW_ORIGINS allowlist.
app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_allowed_origins(),
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "Accept", "X-Request-ID"],
)

# Optional shared-token guard; production fails closed without a strong server token.
app.add_middleware(FinAIAPIAuthMiddleware)


app.include_router(market_router)
app.include_router(market_analyst_router)
app.include_router(crypto_router)
app.include_router(investment_router)
app.include_router(compliance_router)
app.include_router(knowledge_router)
app.include_router(investment_routes_router)
app.include_router(resources_router)
app.include_router(models_router)
app.include_router(system_router)
app.include_router(local_model_router)
app.include_router(xai_router)
app.include_router(market_intelligence_router)
app.include_router(investment_knowledge_router)
app.include_router(causal_risk_router)
app.include_router(advanced_causal_router)
app.include_router(retrieval_lab_router)
app.include_router(research_control_router)
app.include_router(swarmtrade_router)
app.include_router(swarmtrade_paper_router)

# Experimental patent-mechanism endpoints remain disabled unless explicitly opted in.
if os.getenv("FINAI_ENABLE_RESEARCH_PATENT_ENDPOINTS", "").strip().casefold() in {
    "1", "true", "yes", "on"
}:
    from app.patent_mechanism_api import router as patent_mechanism_router
    app.include_router(patent_mechanism_router)


_orchestrator: Optional[XAISessionOrchestrator] = None
_market_data_service: Optional[MarketDataService] = None


def get_market_data_service() -> MarketDataService:
    """
    Create the shared market-data service lazily.

    The provider itself is imported and registered only when market
    data is first requested, keeping normal API startup lightweight.
    """
    global _market_data_service

    if _market_data_service is None:
        from market_data.providers.yfinance_provider import YFinanceProvider

        providers = {
            "yfinance": YFinanceProvider(),
        }
        # Optional, read-only Longbridge support. Credentials are checked before
        # registering the provider; SDK initialization remains lazy until a quote
        # or history request explicitly selects it.
        longbridge_configured = all(
            os.getenv(name, "").strip()
            for name in (
                "LONGBRIDGE_APP_KEY",
                "LONGBRIDGE_APP_SECRET",
                "LONGBRIDGE_ACCESS_TOKEN",
            )
        )
        if longbridge_configured:
            from market_data.providers.longbridge_provider import LongbridgeMarketDataProvider
            providers["longbridge"] = LongbridgeMarketDataProvider()

        _market_data_service = MarketDataService(
            providers=providers,
            default_provider="yfinance",
        )

    return _market_data_service


def get_orchestrator() -> XAISessionOrchestrator:
    """
    Create the session-aware XAI orchestrator lazily.

    This keeps API import lightweight and preserves the existing
    lazy RAG/model-loading behavior.
    """
    global _orchestrator

    if _orchestrator is None:
        _orchestrator = XAISessionOrchestrator()

    return _orchestrator


class SessionRequest(BaseModel):
    session_id: str = Field(..., min_length=1, max_length=128)


class ChatRequest(BaseModel):
    message: str = Field(
        ...,
        min_length=1,
        max_length=4000,
        description="User's financial request.",
    )

    session_id: Optional[str] = Field(
        default=None,
        max_length=128,
        description=(
            "Conversation session ID. "
            "A new one is generated when omitted."
        ),
    )

    language: str = Field(
        default="English",
        max_length=32,
    )

    persona: str = Field(
        default="neutral",
        max_length=32,
    )

    generate_response: bool = Field(
        default=False,
        description=(
            "Enable model-generated user-facing responses. "
            "Disabled by default to keep API smoke tests lightweight."
        ),
    )

    max_new_tokens: int = Field(
        default=256,
        ge=32,
        le=1024,
    )

    model_id: Optional[str] = Field(
        default=None,
        max_length=128,
        description="Optional enabled reasoning model override.",
    )


@app.get("/health")
def health() -> Dict[str, Any]:
    market_data = get_market_data_service()

    return {
        "status": "ok",
        "service": "finai-api",
        "version": APP_VERSION,
        "market_data": {
            "status": "configured",
            "default_provider": market_data.default_provider,
            "providers": sorted(market_data.providers.keys()),
        },
    }


@app.get("/api/v1")
def api_info() -> Dict[str, Any]:
    return {
        "service": "FinAI",
        "version": APP_VERSION,
        "endpoints": {
            "health": "/health",
            "chat": "/api/v1/chat",
            "xai": "/api/v1/xai",
            "brain_status": "/api/v1/system/brain-status",
            "swarmtrade_status": "/api/v1/swarmtrade/status",
            "swarmtrade_plan": "/api/v1/swarmtrade/plan",
            "swarmtrade_paper_status": "/api/v1/swarmtrade/paper/status",
            "swarmtrade_paper_accounts": "/api/v1/swarmtrade/paper/accounts",
            "swarmtrade_paper_positions": "/api/v1/swarmtrade/paper/accounts/{account_id}/positions",
            "research_control_status": "/api/v1/causal-risk/research-control/status",
            "research_control": "/api/v1/causal-risk/research-control/evaluate",
        },
    }


@app.post("/api/v1/session/authenticate")
def authenticate_session(request: SessionRequest) -> Dict[str, Any]:
    session_id = request.session_id.strip()
    if not session_id:
        raise HTTPException(status_code=422, detail="session_id cannot be empty.")

    session = get_orchestrator().authenticate_session(session_id)

    return {
        "status": "AUTHENTICATED",
        "message": (
            "Demo session authenticated. This development flow does not verify "
            "real-world identity, OTP, or bank credentials."
        ),
        "session": session,
    }


@app.post("/api/v1/session/logout")
def logout_session(request: SessionRequest) -> Dict[str, Any]:
    session_id = request.session_id.strip()
    if not session_id:
        raise HTTPException(status_code=422, detail="session_id cannot be empty.")

    session = get_orchestrator().logout_session(session_id)

    return {
        "status": "LOGGED_OUT",
        "message": "Session authentication has been cleared.",
        "session": session,
    }


@app.post("/api/v1/chat")
def chat(request: ChatRequest) -> Dict[str, Any]:
    message = request.message.strip()

    if not message:
        raise HTTPException(
            status_code=422,
            detail="Message cannot be empty.",
        )

    session_id = (
        request.session_id.strip()
        if request.session_id
        else ""
    )

    if not session_id:
        session_id = f"session-{uuid4().hex}"

    try:
        result = get_orchestrator().handle_message(
            session_id=session_id,
            user_text=message,
            generate_response=request.generate_response,
            language=request.language,
            persona=request.persona,
            max_new_tokens=request.max_new_tokens,
            model_id=request.model_id,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail="FinAI request processing failed.",
        ) from exc

    return {
        "service": "FinAI",
        "session_id": session_id,
        **result,
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="127.0.0.1",
        port=8000,
        reload=False,
    )



