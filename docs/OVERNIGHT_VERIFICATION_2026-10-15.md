# FinAI overnight verification handoff — 15 October 2026

Target branch: `ai/finai-completion`

This document is a practical verification plan for the next local session. It distinguishes checked-in code from deployment-dependent capabilities; it does not certify production readiness.

## What the current branch contains

- FinAI routing, policy/authority, deterministic finance tools, RAG, model/provider routing, response verification, and XAI tracing.
- Multi-provider adapters and a Model Intelligence workspace; cloud provider credentials and live availability remain environment-dependent.
- Causal-risk research endpoints, dynamic/temporal and multimodal research prototypes, counterfactual simulation, feasibility screening, and deterministic synthetic benchmark artifacts.
- Experimental EPCRP and bounded linear-DAG screening APIs, explicitly opt-in and token-guarded.
- ResilientPay local intent journal with idempotency/state transitions and simulation-only settlement adapter. No live bank or Hyperledger Fabric settlement is included.
- Offline/network policy guards for named integrations. These are not an OS-level network sandbox.
- Colibrì loopback API adapter only. The third-party runtime/weights and VRAM/RAM/NVMe expert streaming are not implemented or bundled by FinAI.
- Finite-value validation for causal constraints, graph edges, research graph input, and selected research API request models.

## New API authentication boundary

The API now supports `FINAI_API_AUTH_MODE=development|bearer` and `FINAI_ENV=production`.

- Development mode preserves the current local workflow.
- Bearer mode requires `FINAI_API_BEARER_TOKEN` with at least 32 characters.
- Production environment always requires a configured strong token, even if the mode is mistakenly left as development.
- `/health` remains public for health probes; HTTP OPTIONS passes through for CORS preflight.
- This is a single shared bearer token, not user identity, roles, tenant isolation, session ownership, MFA, or a production identity system.
- Do not embed the shared token in a public browser bundle. For a browser deployment, put an identity-aware reverse proxy/OIDC gateway in front of the API. Keep API access private until this is configured.

## Tomorrow: run in PowerShell

From the repository root:

```powershell
Set-Location "C:\Users\roghe\FinAI"
git status -sb
git switch ai/finai-completion
git pull --ff-only origin ai/finai-completion
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe scripts\finai_preflight.py
```

Then verify frontend and lint:

```powershell
Set-Location "C:\Users\roghe\FinAI\frontend"
npm ci
npm run build
npm run lint
```

If `scripts/finai_preflight.py` has required arguments in this checkout, use its `--help` output first.

## Auth smoke checks

Local development should work without a token:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/health
Invoke-RestMethod http://127.0.0.1:8000/api/v1
```

For a private server-to-server deployment, generate a random secret of at least 32 characters and set it only in the server environment:

```powershell
$env:FINAI_ENV = "production"
$env:FINAI_API_AUTH_MODE = "bearer"
$env:FINAI_API_BEARER_TOKEN = "<inject-a-random-secret-from-your-secret-manager>"
```

Restart the API. `/health` should remain accessible; `/api/v1` should return 401 without a bearer token and 200 with the configured token. Do not commit the token or place it in frontend environment variables prefixed for browser exposure.

## Acceptance checklist

- [ ] Full Python suite passes on the exact pulled commit.
- [ ] Frontend `npm ci`, build and lint complete; review warnings.
- [ ] GitHub Actions backend, frontend, and benchmark jobs pass on the exact commit.
- [ ] API smoke tests pass for health, chat, models, market, XAI, causal-risk and research status.
- [ ] Test offline mode with network physically unavailable; confirm no unexpected outbound requests.
- [ ] Verify provider health and fallback with server-side credentials; report missing credentials as blocked.
- [ ] Regenerate/review router and RAG artifacts from approved, licensed source data in a clean checkout.
- [ ] Inspect causal-risk benchmark output, false-prune behavior, baselines, chronological holdout and repeatability.
- [ ] Verify the actual frontend in desktop and narrow viewports.
- [ ] Do not enable experimental patent routes or production API access before security review.

## Explicitly not certified

Patent novelty/inventive step; real-market causal accuracy; complete Colibrì model streaming; universal offline operation; live bank/Fabric settlement; production financial authorization; or deployment security. These require separate evidence and integration work.
