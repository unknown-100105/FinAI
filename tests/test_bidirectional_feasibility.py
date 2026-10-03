from causal_risk.bidirectional_feasibility import (
    backward_required_parent_interval,
    backward_target_cone,
)


def test_backward_required_interval_is_a_necessary_condition():
    required = backward_required_parent_interval(
        [-100.0, 100.0],
        [70.0, 100.0],
        [[-80.0, 80.0]],
        0.9,
    )
    assert required[0] >= -100.0
    assert required[1] <= 100.0
    assert required[1] >= required[0]


def test_backward_target_cone_excludes_unrelated_factor():
    nodes = ["rates", "credit", "portfolio", "usd", "oil"]
    edges = [
        {"source": "rates", "target": "credit", "weight": 0.8},
        {"source": "credit", "target": "portfolio", "weight": 0.9},
        {"source": "usd", "target": "oil", "weight": 0.5},
    ]
    bounds = {node: (-100.0, 100.0) for node in nodes}
    result = backward_target_cone(
        nodes,
        edges,
        bounds,
        target_node="portfolio",
        target_interval=(50.0, 100.0),
    )
    assert set(result["ancestor_nodes"]) == {"rates", "credit", "portfolio"}
    assert "usd" not in result["ancestor_nodes"]
    assert "oil" not in result["ancestor_nodes"]
