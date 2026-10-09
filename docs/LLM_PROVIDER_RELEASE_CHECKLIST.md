# FinAI LLM provider release checklist

A registry entry is not proof that a model can be invoked. Keep a provider disabled until its real model ID, adapter, configuration, error handling and financial-response evaluation pass.

## Per-provider checklist

- [ ] Confirm the model identifier from official provider documentation.
- [ ] Read credentials only from environment variables; never log secrets.
- [ ] Test missing/invalid credentials, timeout, rate limit, server error, malformed JSON, empty response and blocked response.
- [ ] Use bounded retries and distinguish retryable from non-retryable errors.
- [ ] Normalize responses to FinAI's adapter contract.
- [ ] Record provider/model, latency and fallback chain without leaking prompts or secrets.
- [ ] Explicit model selection must not silently switch providers.
- [ ] Offline and restricted-data policies must prevent prohibited cloud routing.
- [ ] Run the same numerical fidelity, evidence faithfulness, financial QA and multilingual test set across providers.
- [ ] Record model ID, test-set version, prompt version, date and parameters.

## Smoke-test expectations

| Scenario | Expected behaviour |
|---|---|
| Primary succeeds | Normalized response; fallback_used=false |
| Primary fails | Only eligible, policy-compatible fallbacks; record attempted chain |
| Explicit model fails | Surface error; no silent model switch |
| Offline mode | Eligible local models only |
| Restricted data | No cloud transmission |
| Missing key | Clear configuration error; no secret leakage |
| Financial result | Preserve deterministic engine values |
| Evidence-backed answer | Preserve evidence boundaries and run verifiers |

Mock tests do not establish live-provider validation. Credential-dependent tests should be opt-in and clearly skipped when credentials are absent. Reconfirm all registry IDs against official provider docs before enabling them.
