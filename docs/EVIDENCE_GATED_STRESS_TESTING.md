# Evidence-Gated, Feasibility-Certified Counterfactual Stress Testing

## What is implemented in this branch

The research pipeline is available as Python API and an opt-in-by-request research endpoint:

- `causal_risk/evidence_gate.py` validates source attribution, evidence identifiers, timestamp freshness, confidence thresholds, and required intervention/causal-edge coverage.
- `causal_risk/evidence_gated_stress.py` refuses to run the scenario engine when the evidence gate fails, runs the existing deterministic SCM engine for accepted interventions, generates seeded tail scenarios, and records feasibility certificates/rejection reasons.
- `app/advanced_causal_api.py` exposes `POST /api/v1/causal-risk/stress-test/evidence-gated`.
- `scripts/benchmark_evidence_gated_stress.py` compares the gated pipeline with a deterministic stress suite and unconstrained tail-scenario generation.
- `tests/test_evidence_gated_stress.py` covers missing/stale/future/low-confidence evidence, fail-closed behavior, and deterministic replay.

The endpoint is a research tool, not a production investment decision or a forecast.

## Evidence record format

Every evidence item must provide:

- `evidence_id`: unique identifier;
- `source`: named source/provenance;
- `observed_at`: ISO-8601 timestamp;
- `confidence`: score from 0 to 1;
- `supports`: one or more exact claim keys such as `intervention:rates` or `edge:rates->credit`.

The gate requires evidence for each requested intervention and every default-graph edge on a directed path from an intervention to the portfolio outcome. The default policy is confidence >= 0.6 and evidence age <= 180 days; callers may tighten those limits. Invalid, future-dated, duplicate, stale, low-confidence, or missing evidence is not accepted.

This is a coverage/provenance gate. It does not independently verify source truthfulness, establish causal identification, or prove that a cited source supports a numeric shock magnitude. Evidence mappings must be reviewed and calibrated for the real data source before research conclusions are drawn.

## API example

Send a request to `POST /api/v1/causal-risk/stress-test/evidence-gated` with this shape (replace synthetic IDs and timestamps with real, licensed, timestamped evidence):

```json
{
  "shock": {"rates": 10, "usd": 5},
  "allocation": {"equity": 55, "debt": 30, "gold": 10, "cash": 5},
  "as_of": "2026-10-20T00:00:00+00:00",
  "minimum_confidence": 0.6,
  "max_age_days": 180,
  "include_tail_scenarios": true,
  "tail_draws": 64,
  "tail_seed": 42,
  "tail_distribution": "student_t_copula",
  "evidence": [
    {
      "evidence_id": "source-record-1",
      "source": "Named source / dataset",
      "observed_at": "2026-10-19T12:00:00+00:00",
      "confidence": 0.95,
      "supports": ["intervention:rates"]
    }
  ]
}
```

The example intentionally omits most required edge claims, so the gate should reject it. Generate the complete `supports` set from the returned `missing_claims` and map each claim to independently reviewed evidence; do not auto-approve claims just to make the endpoint pass.

## Run the smoke benchmark

From the repository root with project dependencies installed:

```powershell
python scripts/benchmark_evidence_gated_stress.py --draws 64 --seed 42
```

The script uses clearly labelled synthetic evidence fixtures to verify wiring and repeatability. Its output is not an empirical benchmark. It reports no realized tail coverage because no chronological realized-loss holdout is supplied.

## Required empirical evaluation before claims

1. Replace synthetic evidence with licensed, point-in-time source records and document the mapping from source data to every claim key.
2. Choose the causal graph, bounds, and primary tail-risk metrics using only training data.
3. Compare historical replay, conventional deterministic shocks, correlation-only/unconstrained generation, SCM without the gate, and the full gated pipeline on identical chronological rolling splits.
4. Report scenario constraint violations, rejection reasons, distributional plausibility, VaR/expected-shortfall coverage against realized outcomes, explanation trace fidelity, runtime, and cost.
5. Run ablations removing the evidence gate and feasibility gate separately; report uncertainty intervals and negative results.
6. Keep a final untouched test window and perform prior-art review before making publication or patent claims.

The default node bounds are broad engineering guards, not empirically calibrated market limits. The current tail sampler is seeded and reproducible but is not a trained GFlowNet. Passing tests or producing scenarios alone does not establish superiority, causal validity, novelty, or patentability.
