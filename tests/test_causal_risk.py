import numpy as np
from causal_risk.discovery import notears_linear
from causal_risk.dynamic_discovery import discover_lagged_graph
from causal_risk.engine import graph_snapshot, run_counterfactual
from causal_risk.tail_scenarios import generate_tail_scenarios


def test_causal_graph_has_directed_edges():
    graph = graph_snapshot()
    assert len(graph["nodes"]) >= 8
    assert len(graph["edges"]) >= 9
    assert graph["edges"][0]["source"] != graph["edges"][0]["target"]
    assert graph["graph_validation"] == []


def test_counterfactual_is_deterministic_and_explains_paths():
    shock = {"rates": 75, "supply": 60, "oil": 35, "credit": 40, "usd": 15}
    allocation = {"equity": 55, "debt": 30, "gold": 10, "cash": 5}
    first = run_counterfactual(shock, allocation, include_tail_scenarios=True)
    second = run_counterfactual(shock, allocation, include_tail_scenarios=True)
    assert first == second
    assert 0 <= first["systemic_stress"] <= 100
    assert first["explanation"]["primary_path"][-1] == "portfolio"
    assert first["validation"]["allocation"]["passed"]


def test_invalid_allocation_is_rejected():
    try:
        run_counterfactual({"rates": 10}, {"equity": 60, "debt": 30})
    except ValueError as exc:
        assert "sum to 100" in str(exc)
    else:
        raise AssertionError("expected invalid allocation to fail")


def test_notears_learns_dag_and_acyclicity():
    rng = np.random.default_rng(42)
    x1 = rng.normal(size=80)
    x2 = 0.8 * x1 + rng.normal(scale=0.2, size=80)
    x3 = 0.6 * x2 + rng.normal(scale=0.2, size=80)
    learned = notears_linear(np.column_stack([x1, x2, x3]), threshold=0.12, max_outer_iter=5)
    assert learned["method"] == "NOTEARS-linear"
    assert learned["status"] == "research_implemented"
    assert learned["acyclicity"] < 0.05


def test_dynamic_discovery_returns_lagged_edges():
    rng = np.random.default_rng(7)
    x = rng.normal(size=(90, 3))
    x[1:, 1] += 0.7 * x[:-1, 0]
    result = discover_lagged_graph(x, lags=1, threshold=0.02)
    assert result["method"].startswith("DYNOTEARS-style")
    assert result["n_samples"] == 90
    assert result["edges"]


def test_tail_sampler_is_reproducible_and_gfn_ready():
    first = generate_tail_scenarios({"rates": 75, "supply": 60}, draws=32, seed=11)
    second = generate_tail_scenarios({"rates": 75, "supply": 60}, draws=32, seed=11)
    assert first == second
    assert first["gfnets_status"] == "interface_ready_not_trained"
