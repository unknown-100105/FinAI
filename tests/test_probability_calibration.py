import pytest
from causal_risk.probability_calibration import calibration_metrics, chronological_split


def test_perfect_predictions_have_zero_brier_and_ece():
    result = calibration_metrics([0, 1, 0, 1], [0, 1, 0, 1], n_bins=4)
    assert result["status"] == "CALIBRATION_METRICS_READY"
    assert result["brier_score"] == 0
    assert result["expected_calibration_error"] == 0
    assert len(result["bins"]) == 4


@pytest.mark.parametrize("p,y", [([1.1],[1]), ([-0.1],[0]), ([float("nan")],[1]), ([0.5],[2]), ([0.2,0.3],[1]), ([],[])])
def test_invalid_inputs_are_rejected(p, y):
    with pytest.raises(ValueError):
        calibration_metrics(p, y)


def test_chronological_split_preserves_order():
    p_train, y_train, p_test, y_test = chronological_split([.1,.2,.3,.4,.5], [0,0,1,0,1], test_fraction=.4)
    assert p_train.tolist() == [.1,.2,.3]
    assert p_test.tolist() == [.4,.5]
    assert y_test.tolist() == [0,1]
