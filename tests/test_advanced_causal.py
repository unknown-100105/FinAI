import numpy as np


def test_versioned_risk_calibration_is_loadable():
    from causal_risk.risk_calibration import load_risk_calibration

    config = load_risk_calibration()
    assert config["version"]
    assert config["coefficients"]["systemic_liquidity"] == 0.34
    assert config["validation"]["causal_identification"] is False


def test_risk_target_calibration_uses_chronological_holdout():
    from causal_risk.risk_calibration import calibrate_risk_target

    rng = np.random.default_rng(9)
    x = rng.normal(size=(100, 3))
    y = 0.5 * x[:, 0] - 0.2 * x[:, 1] + rng.normal(scale=0.2, size=100)
    result = calibrate_risk_target(
        x,
        y,
        ["rates", "credit", "oil"],
        alpha=1.0,
    )
    assert result["status"] == "EMPIRICAL_RISK_CALIBRATION_READY"
    assert result["chronological_split"] is True
    assert result["train_samples"] == 80
    assert result["test_samples"] == 20


def test_student_t_copula_tail_sampler_is_reproducible():
    from causal_risk.tail_scenarios import generate_tail_scenarios

    correlation = [[1.0, 0.65], [0.65, 1.0]]
    first = generate_tail_scenarios(
        {"rates": 75, "oil": 50},
        draws=128,
        seed=12,
        correlation=correlation,
        distribution="student_t_copula",
        degrees_of_freedom=5,
    )
    second = generate_tail_scenarios(
        {"rates": 75, "oil": 50},
        draws=128,
        seed=12,
        correlation=correlation,
        distribution="student_t_copula",
        degrees_of_freedom=5,
    )
    assert first == second
    assert first["dependence_model"] == "student_t_copula"
    assert first["distribution"] == "student_t_copula"


def test_neuro_symbolic_rules_reject_invalid_allocation():
    from causal_risk.neuro_symbolic import FinancialConstraintEngine

    result = FinancialConstraintEngine().validate(
        {"equity": 60, "debt": 30},
        {"rates": 10},
        ["rates", "oil"],
        research_graph_ready=True,
    )
    assert result["passed"] is False
    assert "allocation_sum_100" in result["failed_rule_ids"]


def test_neuro_symbolic_rules_require_research_gate():
    from causal_risk.neuro_symbolic import FinancialConstraintEngine

    result = FinancialConstraintEngine().validate(
        {"equity": 60, "debt": 30, "gold": 10},
        {"rates": 10},
        ["rates", "oil"],
        research_graph_ready=False,
    )
    assert result["passed"] is False
    assert "research_gate_required" in result["failed_rule_ids"]


def test_multimodal_graph_fuses_available_modalities():
    from causal_risk.multimodal_graph import GraphEdge, GraphNode, MultimodalGraph

    graph = MultimodalGraph(
        nodes=[
            GraphNode("rates", "macro_factor", "macro", (1.0, 0.2), "synthetic"),
            GraphNode("credit", "asset", "market", (0.4, 0.6), "synthetic"),
        ],
        edges=[
            GraphEdge("rates", "credit", "affects", 0.8, "causal", "synthetic"),
        ],
    )
    vector = graph.fuse_node(
        "credit",
        {"market": [0.4, 0.6], "text": [0.1, 0.2]},
        output_dim=8,
    )
    assert vector.shape == (8,)
    assert np.isfinite(vector).all()


def test_gflownet_research_prototype_trains_and_samples():
    from causal_risk.gfnets import GFlowConfig, GFlowNetTailGenerator

    generator = GFlowNetTailGenerator(
        2,
        GFlowConfig(hidden_dim=16, epochs=3, seed=5),
    )
    result = generator.train()
    assert result["status"] == "GFLOWNET_RESEARCH_TRAINED"
    samples = generator.sample(
        {"rates": 75, "oil": 50},
        draws=8,
        seed=6,
    )
    assert samples["status"] == "GFLOWNET_SAMPLES_READY"
    assert len(samples["scenarios"]) == 8


def test_temporal_risk_gnn_training_routine_runs():
    from causal_risk.temporal_gnn import build_temporal_edges, train_temporal_risk_model

    node_features = [
        [0.1, 0.2],
        [0.2, 0.1],
        [0.4, 0.3],
    ]
    target = [0.1, 0.2, 0.5]
    edges = build_temporal_edges(
        [0, 1, 0],
        [1, 2, 2],
        [1.0, 1.0, 2.0],
    )
    result = train_temporal_risk_model(
        node_features,
        target,
        edges,
        hidden_features=8,
        heads=2,
        epochs=3,
        seed=3,
    )
    assert result["status"] == "TGAT_RESEARCH_TRAINED"
    assert result["model"] is not None
    assert np.isfinite(result["train_mae"])


def test_regime_benchmark_returns_metrics_by_regime():
    from causal_risk.regime_benchmark import assign_regimes, evaluate_predictions

    rng = np.random.default_rng(17)
    samples = rng.normal(size=(80, 3))
    regimes = assign_regimes(samples, volatility_window=5, high_vol_quantile=0.8)
    result = evaluate_predictions(
        rng.normal(size=80),
        rng.normal(size=80),
        regimes,
    )
    assert result["status"] == "REGIME_BENCHMARK_READY"
    assert result["regimes"]


def test_research_status_endpoint_is_exposed():
    from app.main import app
    from fastapi.testclient import TestClient

    response = TestClient(app).get("/api/v1/causal-risk/research-status")
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "FINAI_RESEARCH_STACK"
    assert payload["components"]["gflownet"] == "trajectory_balance_research_prototype"
