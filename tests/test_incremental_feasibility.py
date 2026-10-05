from causal_risk.incremental_feasibility import IncrementalIntervalState
from causal_risk.feasibility_pruning import propagate_interval_bounds


def test_incremental_preview_matches_full_interval_propagation():
    nodes = ["rates", "credit", "liquidity", "portfolio"]
    edges = [
        {"source": "rates", "target": "credit", "weight": 0.8},
        {"source": "credit", "target": "liquidity", "weight": 0.7},
        {"source": "liquidity", "target": "portfolio", "weight": 0.9},
    ]
    bounds = {node: (-100.0, 100.0) for node in nodes}
    state = IncrementalIntervalState.build(
        nodes, edges, bounds, {"rates": 50.0}
    )
    preview = state.preview_change("rates", 80.0)
    expected = propagate_interval_bounds(
        nodes, edges, {"rates": 80.0}, bounds
    )
    assert preview["intervals"] == expected
    assert preview["node_evaluations"] == 4


def test_incremental_preview_only_recomputes_descendant_cone():
    nodes = ["rates", "usd", "credit", "oil", "portfolio"]
    edges = [
        {"source": "rates", "target": "credit", "weight": 0.8},
        {"source": "usd", "target": "oil", "weight": 0.5},
        {"source": "credit", "target": "portfolio", "weight": 0.7},
    ]
    bounds = {node: (-100.0, 100.0) for node in nodes}
    state = IncrementalIntervalState.build(
        nodes, edges, bounds, {"rates": 40.0, "usd": 10.0}
    )
    preview = state.preview_change("rates", 60.0)
    assert "oil" not in preview["affected_nodes"]
    assert preview["node_evaluations"] == 3


def test_apply_change_persists_and_matches_full_interval_propagation():
    from causal_risk.feasibility_pruning import propagate_interval_bounds

    nodes = ["rates", "credit", "portfolio"]
    edges = [
        {"source": "rates", "target": "credit", "weight": 0.7},
        {"source": "credit", "target": "portfolio", "weight": 0.8},
    ]
    bounds = {node: (-100.0, 100.0) for node in nodes}
    state = IncrementalIntervalState.build(nodes, edges, bounds, {})
    state.apply_change("rates", 10.0)
    state.apply_change("credit", 20.0)
    expected = propagate_interval_bounds(
        nodes, edges, {"rates": 10.0, "credit": 20.0}, bounds
    )
    assert state.intervals == expected
    assert state.interval_node_evaluations > 0
