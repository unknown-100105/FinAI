import numpy as np


def test_synthetic_dataset_has_point_in_time_contract():
    from causal_risk.research_experiments import generate_synthetic_financial_system

    data = generate_synthetic_financial_system(n_rows=120, seed=7)
    assert data["status"] == "SYNTHETIC_POINT_IN_TIME_DATASET_READY"
    assert len(data["timestamps"]) == 120
    assert len(data["values"]) == 120
    assert len(data["known_edges"]) > 0


def test_discovery_experiment_is_chronologically_isolated():
    from causal_risk.research_experiments import (
        generate_synthetic_financial_system,
        run_discovery_holdout_experiment,
    )

    data = generate_synthetic_financial_system(n_rows=120, seed=8)
    result = run_discovery_holdout_experiment(data["values"])
    assert result["status"] == "DISCOVERY_FUTURE_HOLDOUT_READY"
    assert result["future_holdout_isolation"] is True
    assert result["split"]["test_start"] > result["split"]["train_end"]


def test_patent_mechanism_benchmark_has_technical_effect_fields():
    from causal_risk.research_experiments import run_patent_mechanism_benchmark

    result = run_patent_mechanism_benchmark()
    assert result["status"] == "PATENT_MECHANISM_BENCHMARK_READY"
    assert result["benchmark"]["false_prunes"] == 0
    assert result["benchmark"]["evaluation_reduction_fraction"] > 0
    assert "high_risk_trajectory_recall" in result["technical_effects_to_measure"]


def test_ood_suite_is_deterministic_and_changes_inputs():
    from causal_risk.research_experiments import build_ood_suite

    values = np.ones((4, 3))
    suite = build_ood_suite(values)
    assert suite["normal"] == values.tolist()
    assert suite["scaled"][0][0] == 1.5
    assert suite["missing_first_feature"][0][0] == 0.0
    assert suite["noisy"] != values.tolist()
