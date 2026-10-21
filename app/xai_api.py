from pathlib import Path
import json

from fastapi import Depends, FastAPI, HTTPException

from app.api_security import FinAIAPIAuthMiddleware
from app.trace_security import require_trace_api_enabled

app = FastAPI(
    title="FinAI XAI API",
    version="0.1.0",
    description="Read-only API for FinAI explainability traces.",
)
app.add_middleware(FinAIAPIAuthMiddleware)

TRACE_DIR = Path(__file__).resolve().parent.parent / "xai" / "traces"


@app.get("/health")
def health():
    return {
        "status": "ok",
        "service": "finai-xai-api",
        "version": "0.1.0",
    }


@app.get("/api/v1/xai/traces")
def list_traces(_: None = Depends(require_trace_api_enabled)):
    if not TRACE_DIR.exists():
        return {
            "count": 0,
            "traces": [],
        }

    traces = []

    for path in sorted(
        TRACE_DIR.glob("*.json"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    ):
        try:
            data = json.loads(
                path.read_text(encoding="utf-8")
            )

            traces.append(
                {
                    "trace_id": data.get("trace_id"),
                    "session_id": data.get("session_id"),
                    "started_at": data.get("started_at"),
                    "completed_at": data.get("completed_at"),
                    "intent": (
                        data.get("router", {})
                        .get("intent")
                    ),
                    "risk_level": (
                        data.get("policy", {})
                        .get("risk_level")
                    ),
                    "final_status": (
                        data.get("final", {})
                        .get("status")
                    ),
                }
            )

        except (OSError, json.JSONDecodeError):
            continue

    return {
        "count": len(traces),
        "traces": traces,
    }


@app.get("/api/v1/xai/traces/{trace_id}")
def get_trace(trace_id: str, _: None = Depends(require_trace_api_enabled)):
    if not trace_id.replace("-", "").isalnum():
        raise HTTPException(
            status_code=400,
            detail="Invalid trace ID.",
        )

    path = TRACE_DIR / f"{trace_id}.json"

    if not path.exists():
        raise HTTPException(
            status_code=404,
            detail="Trace not found.",
        )

    try:
        return json.loads(
            path.read_text(encoding="utf-8")
        )
    except json.JSONDecodeError:
        raise HTTPException(
            status_code=500,
            detail="Trace file contains invalid JSON.",
        )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.xai_api:app",
        host="127.0.0.1",
        port=8001,
        reload=False,
    )
