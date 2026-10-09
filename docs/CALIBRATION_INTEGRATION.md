# Probability calibration and external Calibre integration

## Internal calibration is not the external package

`causal_risk/calibration.py` estimates empirical diagnostics for consensus graph edges. These are conditional associations, not calibrated probabilities or identified causal effects.

`causal_risk/probability_calibration.py` evaluates already-produced binary-event probabilities using Brier score, log loss, expected calibration error (ECE), reliability bins and a chronological split. It does not train a calibrator or infer probabilities from causal edge weights.

## External package gate

Before adding an external Calibre distribution to the primary runtime, verify its exact package/repository, supported Python versions, API and dependency constraints. The project has used Python 3.10.11; if a selected release requires a newer Python, isolate it or pin a compatible release. Do not conflate it with the internal calibration module.

## Safe integration sequence

1. Pin a verified release in an optional dependency group.
2. Wrap it behind an optional adapter so core FinAI works without the dependency.
3. Require a clearly defined event, probabilities in [0,1] and labelled outcomes.
4. Use chronological/walk-forward splits; never calibrate on the final test set.
5. Compare raw and calibrated predictions using Brier score, log loss, reliability diagrams and decision utility.
6. Assess regime stability, subgroup behaviour, sample counts and uncertainty.
7. Deploy only if held-out results support the change and monitoring for drift exists.

Calibration does not establish causality, truthfulness, profitability, investment suitability or patentability.
