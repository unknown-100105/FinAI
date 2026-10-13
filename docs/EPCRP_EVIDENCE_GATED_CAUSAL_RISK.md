# EPCRP: Evidence-Gated Paired-World Causal Risk Propagation

**Status:** Experimental reference implementation. Not a filed patent, legal opinion, or validated financial-risk model.

## Purpose

EPCRP evaluates a controlled intervention against a baseline using the same caller-supplied structural graph and model configuration. Candidate edges are admitted only when they meet configured validation, evidence-ID, support-score, regime, and time-window conditions. The result includes node-level deltas, a portfolio-weighted delta, edge rejection reasons, evidence identifiers for affected outputs, and a machine-readable reproducibility manifest.

## Implementation

- **finance_engine/epcrp.py** is dependency-free and evaluates a static directed acyclic graph (DAG) using illustrative linear node equations.
- **tests/test_epcrp.py** covers paired-world propagation, rejection gates, cycle detection, intervention-aware lineage, uncertainty determinism, input validation, JSON serialization, and reproducibility.
- Time windows are evaluated at a single as_of timestamp. The code does not simulate lagged time steps, identify causal relationships from data, or estimate coefficients from market history.
- Uncertainty sampling perturbs supplied edge coefficients using caller-provided standard deviations. It is not calibrated unless a separate validation procedure establishes that calibration.
- Exposure weights are supplied by the caller and have no guaranteed financial unit.

## How to run

Run from the repository root:

    python -m pytest -q tests/test_epcrp.py

The code is also covered by the artifact-independent FinAI CI test list.

## Validation needed

Before using EPCRP for decisions, evaluate graph edges and assumptions against chronologically held-out financial data, compare against relevant stress-test and graph-propagation baselines, calibrate uncertainty intervals, test regime changes and missing evidence, and report repeated-run uncertainty and runtime/memory. The implementation is research code; its existence does not establish novelty, inventive step, patent eligibility, or freedom to operate.

## Relationship to intervention feasibility screening

The related **finance_engine/counterfactual_screening.py** component answers a different question: it computes conservative interval bounds for whether a bounded linear DAG can reach a target range under candidate interventions. It is a cheap feasibility screen, not a causal-discovery method. RETAIN means only “not proven impossible”; it must not be interpreted as a verified feasible outcome. Keep both components opt-in and experimental until their integration and empirical validity are reviewed.
