import numpy as np
import pytest

from causal_risk.probability_calibration import (
    ProbabilityCalibrator,
    evaluate_probability_calibration,
)


def test_sklearn_probability_calibrator_is_bounded_and_monotone():
    scores = np.linspace(0.05, 0.95, 40)
    labels = np.array([0] * 10 + [1] * 20 + [0] * 10)
    calibrator = ProbabilityCalibrator("sklearn_isotonic").fit(scores, labels)
    output = calibrator.transform(np.linspace(0.0, 1.0, 51))
    assert calibrator.backend == "sklearn_isotonic"
    assert np.isfinite(output).all()
    assert np.all((output >= 0.0) & (output <= 1.0))
    assert np.all(np.diff(output) >= -1e-12)


def test_auto_backend_returns_supported_backend():
    scores = np.linspace(0.05, 0.95, 30)
    labels = np.array([0, 1] * 15)
    calibrator = ProbabilityCalibrator("auto").fit(scores, labels)
    result = calibrator.transform(np.array([0.2, 0.5, 0.8]))
    assert calibrator.backend in {
        "calibre_centered_isotonic",
        "sklearn_isotonic",
    }
    assert result.shape == (3,)
    assert np.isfinite(result).all()


def test_probability_calibration_rejects_invalid_inputs():
    with pytest.raises(ValueError, match="probabilities"):
        ProbabilityCalibrator().fit([0.2, 1.2], [0, 1])
    with pytest.raises(ValueError, match="both classes"):
        ProbabilityCalibrator().fit([0.2, 0.8], [1, 1])


def test_evaluation_report_contains_proper_score_and_calibration_metrics():
    report = evaluate_probability_calibration(
        [0, 0, 1, 1],
        [0.1, 0.4, 0.6, 0.9],
        n_bins=2,
    )
    assert report.n_samples == 4
    assert report.brier_score == pytest.approx(0.085)
    assert 0.0 <= report.expected_calibration_error <= 1.0
    assert report.distinct_probability_count == 4


def test_evaluation_rejects_probabilities_outside_unit_interval():
    with pytest.raises(ValueError):
        evaluate_probability_calibration([0, 1], [-0.1, 1.1])
