from causal_risk.pruning_benchmark import benchmark_prefix_certificate


def test_pruning_certificate_has_zero_false_prunes_on_exact_small_state():
    nodes = ["rates", "credit", "portfolio"]
    edges = [
        {"source": "rates", "target": "credit", "weight": 0.8},
        {"source": "credit", "target": "portfolio", "weight": 0.9},
    ]
    bounds = {node: (-100.0, 100.0) for node in nodes}
    result = benchmark_prefix_certificate(
        nodes,
        edges,
        ["rates", "credit"],
        {"rates": 10.0, "credit": 10.0},
        [-1.0, -0.5, 0.5, 1.0],
        bounds,
        target_node="portfolio",
        target_interval=(-20.0, 20.0),
        prefix_depth=1,
    )
    assert result["status"] == "PRUNING_BENCHMARK_READY"
    assert result["false_prunes"] == 0
    assert result["certificate_evaluations"] < result["exact_completion_evaluations"]
    assert result["evaluation_reduction_fraction"] > 0


def test_pruning_benchmark_records_infeasible_prefixes():
    nodes = ["rates", "portfolio"]
    edges = [{"source": "rates", "target": "portfolio", "weight": 1.0}]
    bounds = {node: (-100.0, 100.0) for node in nodes}
    result = benchmark_prefix_certificate(
        nodes,
        edges,
        ["rates"],
        {"rates": 20.0},
        [-1.0, 1.0],
        bounds,
        target_node="portfolio",
        target_interval=(80.0, 100.0),
        prefix_depth=1,
    )
    assert result["hard_pruned"] == 2
    assert result["exact_feasible_prefixes"] == 0
