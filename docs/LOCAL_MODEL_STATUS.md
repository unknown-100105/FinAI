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
| `ready_for_inference` | The model ID was listed by the server; a chat-completion test is still required |

Example PowerShell configuration:

```powershell
$env:FINAI_COLIBRI_BASE_URL = "http://127.0.0.1:8000/v1"
$env:FINAI_COLIBRI_MODEL = "olmoe-colibri" # must match /v1/models
$env:FINAI_COLIBRI_API_KEY = "local-finetoken" # only if required by the local server
```

Start FinAI on loopback and query the endpoint. Do not expose the development API or model server to the LAN or internet. Never commit secrets.

This endpoint does not load weights, start or manage the external runtime, test a generated response, or certify model quality. For an actual inference check, send a synthetic non-sensitive prompt through the normal FinAI response path and verify the returned provider/model metadata. A listed model is not proof that generation succeeds.
