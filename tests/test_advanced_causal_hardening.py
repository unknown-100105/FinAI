"""Regression tests for advanced causal-risk research boundaries.

These tests validate deterministic software behavior on synthetic data; they do
not establish causal identification or real-market predictive performance.
"""
import numpy as np
import pytest


def test_notears_returns_finite_diagnostics_and_zero_diagonal():
    from causal_risk.discovery import notears_linear

    rng = np.random.default_rng(41)
    x = rng.normal(size=(80, 3))
    x[:, 1] += 0.7 * x[:, 0]
    result = notears_linear(x, max_outer_iter=4, max_inner_iter=30)
    adjacency = np.asarray(result["adjacency"], dtype=float)
    assert result["method"] == "NOTEARS-linear"
    assert result["status"] == "research_implemented"
    assert adjacency.shape == (3, 3)
    assert np.isfinite(adjacency).all()
    assert np.allclose(np.diag(adjacency), 0.0)
    assert np.isfinite(result["acyclicity"])
    assert "acyclicity_converged" in result["optimizer"]


@pytest.mark.parametrize(
    "samples",
    [
        [[1.0, 2.0]],
        [[1.0, 2.0], [np.nan, 1.0], [2.0, 3.0], [3.0, 4.0],
         [4.0, 5.0], [5.0, 6.0], [6.0, 7.0], [7.0, 8.0]],
    ],
)
def test_notears_rejects_insufficient_or_nonfinite_samples(samples):
    from causal_risk.discovery import notears_linear

    with pytest.raises(ValueError):
        notears_linear(samples)


def test_lagged_discovery_reports_baseline_not_full_dynotears():
    from causal_risk.dynamic_discovery import discover_lagged_graph

    rng = np.random.default_rng(9)
    x = rng.normal(size=(160, 2))
    for t in range(1, len(x)):
        x[t, 1] += 0.9 * x[t - 1, 0]
    result = discover_lagged_graph(x, lags=1, alpha=0.01, threshold=0.05)
    assert result["status"] == "research_baseline"
    assert "Ridge" in result["method"]
    assert all(edge["lag"] >= 1 for edge in result["edges"])
    assert all(np.isfinite(edge["weight"]) for edge in result["edges"])


def test_tail_sampler_rejects_invalid_correlation_and_is_seeded():
    from causal_risk.tail_scenarios import generate_tail_scenarios

    with pytest.raises(ValueError, match="symmetric"):
        generate_tail_scenarios(
            {"rates": 20, "oil": 10},
            draws=16,
            correlation=[[1.0, 0.2], [0.3, 1.0]],
        )
    kwargs = {
        "draws": 32,
        "seed": 123,
        "distribution": "student_t_copula",
        "degrees_of_freedom": 5,
        "correlation": [[1.0, 0.4], [0.4, 1.0]],
    }
    first = generate_tail_scenarios({"rates": 20, "oil": 10}, **kwargs)
    second = generate_tail_scenarios({"rates": 20, "oil": 10}, **kwargs)
    assert first == second
    assert first["scenario_count"] == len(first["scenarios"])
    assert first["gfnets_status"] == "interface_ready_not_trained"


def test_gflownet_rejects_invalid_reward_values():
    import torch
    from causal_risk.gfnets import GFlowConfig, GFlowNetTailGenerator

    generator = GFlowNetTailGenerator(
        2, GFlowConfig(hidden_dim=8, epochs=1, seed=4, device="cpu")
    )

    def invalid_reward(batch):
        return torch.zeros(batch.shape[0], dtype=batch.dtype, device=batch.device)

    with pytest.raises(ValueError, match="strictly positive"):
        generator.train(reward_fn=invalid_reward)


def test_temporal_gnn_rejects_edge_index_out_of_range():
    from causal_risk.temporal_gnn import build_temporal_edges, train_temporal_risk_model

    edges = build_temporal_edges([0], [9], [1.0])
    with pytest.raises((ValueError, IndexError, RuntimeError)):
        train_temporal_risk_model(
            [[0.1], [0.2]], [0.1, 0.2], edges,
            hidden_features=4, heads=1, epochs=1, device="cpu",
        )
