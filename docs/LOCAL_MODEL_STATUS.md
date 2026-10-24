# Local model readiness endpoint

FinAI exposes a read-only diagnostic endpoint for the optional local Colibrì server:

- `GET /api/v1/system/local-model-status` returns configuration-only status and makes no outbound request.
- `GET /api/v1/system/local-model-status?probe=true` explicitly requests a short-timeout call to the local OpenAI-compatible `/v1/models` endpoint.

## Status meanings

| Status | Meaning |
|---|---|
| `unconfigured` | `FINAI_COLIBRI_BASE_URL` is empty |
| `invalid_configuration` | The configured URL is not accepted by the loopback-only adapter |
| `configured_not_probed` | Configuration exists; no request was made |
| `unreachable` | The explicitly requested local probe could not connect |
| `server_error` | The local endpoint returned a non-success HTTP status |
| `invalid_server_response` | The server did not return an OpenAI-compatible model list |
| `model_not_found` | Server is reachable, but the configured model ID was not listed |
| `model_listed_not_inference_verified` | The model ID was listed by the server; a chat-completion test is still required |

Example PowerShell configuration:

```powershell
$env:FINAI_COLIBRI_BASE_URL = "http://127.0.0.1:8010/v1"
$env:FINAI_COLIBRI_MODEL = "olmoe-colibri" # must match /v1/models
$env:FINAI_COLIBRI_API_KEY = "local-finetoken" # only if required by the local server
```

Start FinAI on loopback and query the endpoint. Do not expose the development API or model server to the LAN or internet. Never commit secrets.

This endpoint does not load weights, start or manage the external runtime, test a generated response, or certify model quality. For an actual inference check, send a synthetic non-sensitive prompt through the normal FinAI response path and verify the returned provider/model metadata. A listed model is not proof that generation succeeds.


## End-to-end inference smoke test

With the FinAI API and the local Colibrì server already running, configure the **backend process** with offline/restricted mode and the local endpoint. The API defaults to port 8000; keep Colibrì on another loopback port such as 8010 to avoid a port collision.

Run from the repository root:

```powershell
.\\.venv\\Scripts\\python.exe scripts\\smoke_local_model.py
```

The script checks `/health`, checks that Brain diagnostics report `FINAI_NETWORK_MODE=offline`, calls the opt-in local model-list probe, then submits a synthetic non-sensitive chat request with `model_id=colibri-local`. It succeeds only when the normal chat path reports generated text using the expected local model. If the API requires bearer mode, provide `FINAI_API_BEARER_TOKEN` in the script process environment as well.

The script uses a loopback-only base URL and never calls a cloud provider directly. Offline-mode configuration is an application-level policy; it is not a substitute for OS-level egress restrictions. The smoke result is a wiring check, not a measure of financial accuracy, safety, or model quality.
