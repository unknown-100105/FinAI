# FinAI Adaptive Intelligence & STAIR Integration

Status: implementation proposal and acceptance contract. This document does not claim that research components are production-enabled.

## Goal

Extend FinAI with risk-aware adaptive orchestration while preserving deterministic finance services, policy enforcement, evidence-grounded retrieval, provider fallbacks, and offline operation.

## Architecture placement

1. Input normalization and intent/language routing.
2. Risk and task-complexity assessment.
3. Capability planner selects only configured capabilities:
   - deterministic finance tools for arithmetic and financial formulas;
   - retrieval for evidence-seeking queries;
   - SLM/local provider for low-latency supported tasks;
   - LLM provider for general explanation;
   - LRM/reasoning provider only when configured and justified;
   - VLM provider for image/document input only when configured;
   - specialist provider/skill for supported finance domains.
4. Retrieval plan may combine lexical, vector, reranking, and structure-aware retrieval.
5. Policy and deterministic validation remain authoritative.
6. Claim/evidence verification and abstention run before final response.
7. Trace records route decision, capability status, evidence identifiers, checks, latency, and fallback reason—never secrets or unnecessary raw financial data.

## STAIR-style structure-aware retrieval

STAIR is treated as a retrieval strategy, not a foundation model. It must be evaluated against FinAI's current hybrid retriever before production activation.

### Indexing requirements

- Preserve document identity, source, version/date, page, section heading, parent heading, and stable chunk ID.
- Extract table-of-contents and heading hierarchy when present.
- Keep table/caption relationships and page references where extraction supports them.
- Fall back to ordinary chunk retrieval for documents without reliable structure.
- Do not infer missing headings or fabricate section relationships.

### Query-time requirements

- Retrieve candidate sections using query terms and existing retrievers.
- Expand to parent/child or adjacent context only under explicit bounded rules.
- Deduplicate by stable chunk ID.
- Preserve source/page/section provenance.
- Fuse structure-aware candidates with existing candidates using a configurable rank-fusion method.
- Allow feature flag and safe fallback to current retrieval.

## Adaptive routing policy

Routing must be deterministic and auditable where possible. Use explicit signals:
- intent/domain;
- input modality;
- configured provider availability;
- task risk class;
- retrieval requirement;
- estimated complexity;
- latency/compute budget;
- prior evaluation-calibrated thresholds.

Never interpret model self-reported confidence as a calibrated probability without validation. Do not route high-impact financial actions to an LLM alone. If a required capability is unavailable, use a safe fallback or explain the limitation.

## Model-family integration policy

| Family | FinAI role | Gate |
|---|---|---|
| LLM | language interface and explanation | provider contract, safety, regression tests |
| SLM | local/low-latency tasks and offline fallback | local benchmark, memory/latency limits |
| VLM | financial image/document interpretation | OCR/vision benchmark, provenance, uncertainty |
| LRM | difficult multi-step reasoning | quality uplift justifies latency/cost |
| MoE | specialist selection; initially software-level routing | measurable uplift; no custom MoE training assumed |
| SSM/Mamba | optional sequence/stream processing research | task-specific baseline and resource benchmark |
| World model / JEPA-like | scenario representation/prediction research | calibration, out-of-sample validation, no direct trading authority |
| Neuro-symbolic | policy/rules + learned interpretation | deterministic rule tests and conflict handling |

## Evaluation protocol

Run against a fixed, versioned dataset with no test-set leakage. Report:
- retrieval Recall@k, MRR/nDCG, evidence completeness;
- answer correctness and citation support;
- numeric exactness for deterministic finance tasks;
- abstention precision/recall on unanswerable questions;
- multilingual performance by language and intent;
- latency p50/p95, tokens, VRAM/RAM, provider cost;
- fallback success and failure rates;
- regression comparison against current main-branch baseline.

A capability is not promoted merely because it improves one metric. Set acceptance thresholds before evaluating and record failed as well as successful runs.

## Production gates

- Feature flags default research capabilities off unless explicitly configured.
- No secrets in logs, traces, or benchmark artifacts.
- Provider timeouts, retries, circuit breakers, and bounded fallback.
- Deterministic finance engine remains source of truth for calculations.
- Policy enforcement precedes external actions and follows model output.
- CI covers unit, integration, contract, security, and regression tests.
- Document model/license, data provenance, known limitations, and deployment requirements.
- No live financial execution without separate explicit authorization and controls.

## Delivery checklist

- [ ] Audit existing router, model gateway, hybrid retrieval, finance engine, policy, verifier, XAI trace, and configuration.
- [ ] Add capability registry and route-decision trace without breaking existing APIs.
- [ ] Implement structure metadata extraction and index migration with backward compatibility.
- [ ] Add STAIR-style retrieval behind a feature flag.
- [ ] Add offline/local model capability contract and resource preflight.
- [ ] Add optional VLM/LRM provider contracts only where supported by repository abstractions.
- [ ] Add benchmark datasets, baseline report, and promotion thresholds.
- [ ] Run full test suite and local acceptance; record exact command, environment, and result.
- [ ] Review security, privacy, licensing, and production deployment blockers.

## Non-goals

- Claiming a custom LRM, MoE, SSM, or world model has been trained.
- Claiming STAIR results transfer to FinAI without local evaluation.
- Allowing generative models to replace deterministic calculations or policy.
- Claiming production readiness while live providers, credentials, security review, or deployment checks are incomplete.
