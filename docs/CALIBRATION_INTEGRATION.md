# Internal probability-calibration metrics (separate from Calibre agent tooling)

## Internal calibration is not the external package

`causal_risk/calibration.py` estimates empirical diagnostics for consensus graph edges. These are conditional associations, not calibrated probabilities or identified causal effects.

`causal_risk/probability_calibration.py` evaluates already-produced binary-event probabilities using Brier score, log loss, expected calibration error (ECE), reliability bins and a chronological split. It does not train a calibrator or infer probabilities from causal edge weights.

## Safe use of the metrics

1. Require a clearly defined event, probabilities in [0,1] and labelled outcomes.
2. Use chronological/walk-forward splits; never calibrate on the final test set.
3. Compare raw and calibrated predictions using Brier score, log loss, reliability diagrams and decision utility.
4. Assess regime stability, subgroup behaviour, sample counts and uncertainty.
5. Deploy only if held-out results support the change and monitoring for drift exists.

Calibre agent-context tooling is documented separately in `docs/AI_AGENT_CONTEXT.md`; it is not this numerical calibration module.

Calibration does not establish causality, truthfulness, profitability, investment suitability or patentability.
