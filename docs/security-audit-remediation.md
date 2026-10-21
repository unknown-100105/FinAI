# Security and audit remediation tracker

This tracker records code changes on `security/audit-remediation-2026-10`. A change is not considered verified until the relevant tests and CI run against the branch. This is not a production-security certification.

## Findings and status

| Audit finding | Remediation in this branch | Status / remaining evidence |
|---|---|---|
| 1. Caller-selected session IDs and phrase-only authentication | Demo authenticate/logout endpoints now require explicit `FINAI_ENABLE_DEMO_SESSION_AUTH=true` outside production; phrase-only authentication has the same gate; normal chat sessions are server-issued and require an opaque, expiring session capability token; session IDs use a safe character allowlist. | **Partial.** Real identity and principal-bound sessions are not implemented. Production auth-required operations fail closed, but a verified OIDC/identity provider and per-principal session ownership are still required before multi-user deployment. |
| 2. Session IDs used in trace filenames | Trace IDs are independently generated UUID-based IDs; writes validate containment and use exclusive creation. | Code changed; trace security tests added. Runtime verification pending. |
| 3. Trace APIs lack per-user access control | Standalone and mounted trace routes are disabled by default, require explicit opt-in and bearer mode, separate full-detail opt-in, and check path containment. | **Partial.** Shared bearer authentication is not per-user authorization. Do not expose traces to multiple users until an identity gateway and principal-level authorization are implemented. |
| 4. Prompts and tool results persist without lifecycle controls | Trace payloads omit prompts, tool payloads/messages, retrieved text, claim text, and final message by default; sensitive-key redaction, restrictive file creation mode, configurable trace directory, seven-day expiry, and a protected trace deletion endpoint were added. | Code and tests added; runtime verification pending. Encryption at rest and deployment-specific ACL review remain required where appropriate. |
| 5. Cloud generation can receive financial context under standard sensitivity | Default data sensitivity changed to `restricted`; local-only fallback is enforced by existing routing policy. `standard` must be explicitly configured. A regression test asserts the default route sensitivity. | Needs regression tests proving cloud providers are not called under the default and restricted settings. Provider privacy review remains deployment-specific. |
| 6. Rejected/incomplete provider output returned to API callers | Chat API removes `original_response` from public results; test added. | Runtime verification pending. Internal service objects may retain rejected text for internal fallback/diagnostics; they must not be logged or exposed through ordinary routes. |
| 7. Financial calculation assumptions and verification | EMI, compound-interest, and SIP outputs document assumptions; compound-interest numeric verification was added; non-finite and fractional-period validation was added. | Tests added; run the full finance suite and review overflow/edge cases. |
| 8. SIP service is not in active chat dispatcher | Scope is documented: SIP is a direct service/demo capability, not an active chat calculation. | Documentation fix complete; do not advertise SIP chat routing until taxonomy, parser, policy, dispatch and integration tests are added. |
| 9. RAG verification overstates what lexical overlap proves | Verifier documentation and result mode now identify `LEXICAL_OVERLAP_SUPPORT`, not factual verification. | Unit test updated; human-labelled semantic evaluation remains outstanding. |
| 10. RAG depends on separately prepared artifacts | Manifest template and SHA-256/path-containment verifier added; README documents the workflow. | Code/tests added. Actual source licenses, corpus hashes, generated index hashes and a populated manifest are blocked on owner-provided corpus/artifacts. |
| 11. Test gaps | Regression tests added for session-auth gating, trace privacy/path safety, rejected model output, finance edge cases, and RAG manifest integrity. | **Pending.** Tests have not yet been executed on this branch. Add/confirm negative tests for production auth, trace access, provider network calls, and trace expiry before release. |
| 12. Causal-risk research lacks real-market validation | Existing runbooks and limitations remain; no empirical claims added. | **Blocked on licensed point-in-time data** and owner approval. Requires rolling chronological evaluation, matched baselines, ablations, OOD/regime tests, repeated seeds, calibration, tail coverage, and false-pruning/high-risk recall. |
| 13. Patent materials do not prove novelty | Claims are explicitly treated as hypotheses; no new patentability claim is made. | **Partial.** A preliminary public sweep is documented in `docs/patent-and-research-strategy.md` and identifies substantial conceptual overlap in causal/graph-based financial stress testing and counterfactual scenario generation. Still requires a claim-element search across patent families and non-patent literature, jurisdiction/status checks, and qualified patent counsel. No novelty or patentability conclusion is made. |

## Required verification before merge

1. Run the new targeted tests, then the complete backend suite and frontend build/lint/audit.
2. Fix regressions caused by the changed security defaults; do not weaken defaults merely to preserve old demo tests.
3. Run GitHub Actions against this branch and record the exact commit SHA and results.
4. Confirm no secrets or sensitive trace payloads are present in generated artifacts or logs.
5. Keep the branch unmerged until the unresolved principal-identity, licensed-data, and legal-review dependencies are explicitly accepted by the project owner.

## Safe demo configuration

For an isolated local demo only, set `FINAI_ENABLE_DEMO_SESSION_AUTH=true` while `FINAI_ENV` is not production. The flow is a mock gate, not identity, OTP, or bank authentication.

Trace API access is disabled by default. To enable it for a controlled local review, set `FINAI_ENABLE_XAI_TRACE_API=true`, `FINAI_API_AUTH_MODE=bearer`, and a strong `FINAI_API_BEARER_TOKEN`. A shared bearer token is not sufficient for multi-user trace authorization.
