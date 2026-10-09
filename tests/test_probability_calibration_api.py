import pytest
from fastapi import HTTPException

from app.causal_risk_api import (
    ProbabilityCalibrationRequest,
    calibrate_probabilities,
)


def test_probability_calibration_api_uses_separate_test_split():
    request = ProbabilityCalibrationRequest(
        calibration_scores=[0.05, 0.15, 0.25, 0.35, 0.65, 0.75, 0.85, 0.95],
        calibration_labels=[0, 0, 0, 0, 1, 1, 1, 1],
        test_scores=[0.1, 0.4, 0.6, 0.9],
        test_labels=[0, 0, 1, 1],
        backend="sklearn_isotonic",
        n_bins=2,
    )
    result = calibrate_probabilities(request)
    assert result["status"] == "PROBABILITY_CALIBRATION_EVALUATED"
    assert result["backend"] == "sklearn_isotonic"
    assert result["metrics"]["n_samples"] == 4
    assert len(result["calibrated_probabilities"]) == 4
    assert "does not persist a calibrator" in result["semantics"]


def test_probability_calibration_api_rejects_length_mismatch():
    request = ProbabilityCalibrationRequest(
        calibration_scores=[0.1, 0.9],
        calibration_labels=[0, 1],
        test_scores=[0.2, 0.8],
        test_labels=[1],
        backend="sklearn_isotonic",
    )
    with pytest.raises(HTTPException) as exc:
        calibrate_probabilities(request)
    assert exc.value.status_code == 422
