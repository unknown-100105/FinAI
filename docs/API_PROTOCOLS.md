# FinAI Communication Protocols and API Boundaries

## Overview

FinAI uses a layered communication model. The primary frontend/backend contract is a JSON REST API served by FastAPI over HTTP during local development and HTTPS when deployed behind a correctly configured TLS terminator. REST is an architectural style; HTTP(S) is the transport.

## Protocol and interface map

| Boundary | Protocol or interface | Data / purpose |
|---|---|---|
| React/Vite frontend → FinAI backend | HTTP(S), REST-style routes | JSON requests and responses for market, assistant, retrieval, research, and simulation features |
| API validation | JSON + Pydantic models | Typed request validation, bounds, and structured error responses |
| Backend → market-data providers | Provider-specific HTTP APIs and SDKs | Read-only quotes, historical bars, and supported financial data |
| Backend → optional local model runtime | Local HTTP API where the selected adapter supports it | Model discovery, readiness checks, and inference requests |
| Backend → relational persistence | SQLite through a Python database interface | Local paper-trading accounts, positions, idempotency records, and ledger state |
| Retrieval | In-process Python calls, SQLite FTS5/BM25, and FAISS where configured | Lexical/semantic retrieval and evidence provenance |
| Backend modules | Python function/module interfaces | Routing, deterministic finance calculations, policy checks, orchestration, verification, and XAI traces |

The exact capabilities at a provider boundary depend on that provider's adapter, credentials, package version, and configuration. The table does not imply every optional service is configured in every installation.

## REST API conventions

- API routes are versioned under `/api/v1` where defined by the application.
- JSON is the normal request/response format.
- FastAPI exposes the OpenAPI schema and interactive documentation at `/openapi.json` and `/docs` when enabled by the application configuration.
- Local development normally binds the API to `127.0.0.1:8000`.
- The Vite frontend defaults to `http://localhost:8000`; set `VITE_API_BASE_URL` when the backend is hosted elsewhere.
- The application has an optional shared-token authentication middleware. Deployment configuration must use a strong secret and HTTPS; never place backend secrets in frontend environment variables or commit them to Git.
- The local CORS allowlist is intended for development origins. Review it before deployment.

## Relevant endpoint groups

| Capability | Example route |
|---|---|
| API index | `GET /api/v1` |
| Model registry | `GET /api/v1/models` |
| System/brain diagnostics | `GET /api/v1/system/brain-status` |
| Retrieval Lab | `POST /api/v1/retrieval-lab/search` |
| SwarmTrade planning | `POST /api/v1/swarmtrade/plan` |
| Paper ledger status | `GET /api/v1/swarmtrade/paper/status` |
| Evidence-gated research control | `POST /api/v1/causal-risk/research-control/evaluate` |

Consult `GET /api/v1` and the generated OpenAPI schema from the running revision for the current route inventory and exact request models.

## Trading and safety boundary

SwarmTrade planning and the paper ledger are simulation-only. A plan must not be interpreted as a broker order, a confirmed fill, or financial advice. The current integration explicitly reports that no live order was submitted and no fill was claimed. The research-control API is not a trade authorization system. No production broker execution should be added without a separate design, explicit authorization, broker sandbox testing, operational controls, and a security review.

## What is not implied

- REST does not mean every internal module communicates over HTTP; many calls are in-process Python calls.
- SQLite is a database interface, not a network protocol.
- FTS5 and FAISS are retrieval/indexing technologies, not frontend communication protocols.
- A configured adapter or endpoint does not prove its external provider, model weights, credentials, or network access are available.
- WebSocket, gRPC, and message-queue protocols should not be claimed as part of the runtime unless a concrete implementation is added and verified.

## Local verification

From the repository root on Windows, run:

```powershell
uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Then open `http://127.0.0.1:8000/docs` and inspect `http://127.0.0.1:8000/openapi.json`. Run the repository's verification script as documented in the README. API documentation being reachable confirms route/schema exposure only; it does not by itself verify external providers or model inference.
