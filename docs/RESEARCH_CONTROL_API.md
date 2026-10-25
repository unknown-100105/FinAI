# Evidence-gated research control API

This API composes FinAI's existing evidence freshness/conflict evaluation, research capability envelope, short-lived evaluation lease and proof-digest mechanisms into a single observable request/response flow.

## Routes

- `GET /api/v1/causal-risk/research-control/status`
- `POST /api/v1/causal-risk/research-control/evaluate`

## Evaluation flow

1. Validate the request size, evidence IDs, confidence values, age windows and the research-operation allowlist.
2. Evaluate freshness and explicit conflict pairs using `causal_risk.research_control_plane.evaluate_evidence`.
3. Derive a capability mode from evidence freshness/conflicts, confidence, uncertainty and model disagreement.
4. Issue and immediately validate a short-lived evaluation lease bound to the input-state digest, model version, policy version and evidence digest.
5. Create a proof payload and deterministic SHA-256 digest for the experiment metadata/metrics.

Example request fields include `experiment_id`, `evidence`, `conflict_pairs`, `uncertainty`, `disagreement`, `operations`, `state`, `model_version`, `policy_version`, `ttl_seconds` and `metrics`. Only declared research operations are accepted. Actions such as `submit_order` are rejected.

## Trust boundary

This is **research diagnostics**, not a production trading authorization service. Evidence metadata and confidence values are supplied by the caller and are not independently authenticated by this API. The lease is an integrity/version/expiry binding; it is not a digital signature and does not establish that the input data are true. The response always reports `trade_authorized: false`, `order_submitted: false` and `fill_claimed: false`.

Do not describe capability mode `full` as a verified trade approval. It only means that this set of experimental research operations passed the configured research control rules.

## Verify locally

```powershell
python -m pytest -q tests/test_research_control_api.py
python -m pytest -q
```
