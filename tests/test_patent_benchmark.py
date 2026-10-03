from causal_risk.patent_benchmark import benchmark_patent_mechanism_variants


def _case():
    nodes = ["rates", "credit", "portfolio"]
    edges = [
        {"source": "rates", "target": "portfolio", "weight": 0.8},
        {"source": "credit", "target": "portfolio", "weight": 0.1},
    ]
    bounds = {"rates": (-100.0, 100.0), "credit": (0.0, 20.0), "portfolio": (-100.0, 100.0)}
    return benchmark_patent_mechanism_variants(
        nodes,
        edges,
        ["rates", "credit"],
        {"rates": 10.0, "credit": 10.0},
        [-1.0, -0.5, 0.5, 1.0],
        bounds,
        target_node="portfolio",
        target_interval=(8.0, 12.0),
        prefix_depth=1,
        scale=0.35,
    )


def test_patent_benchmark_is_deterministic_and_reports_correctness():
    one = _case()
    two = _case()
    assert one["status"] == "PATENT_MECHANISM_VARIANT_BENCHMARK_READY"
    assert one["baseline"]["candidate_prefixes"] == 4
    assert one["baseline"]["exact_completion_evaluations"] == 16
    assert one["correctness"]["finite_action_space_high_risk_prefixes"] == 1
    assert one["forward_certificate"]["hard_pruned_prefixes"] == 1
    assert one["bidirectional_necessary_interval"]["necessary_interval_pruned_prefixes"] == 1
    assert one["correctness"]["forward_no_false_prune"] is True
    assert one["correctness"]["bidirectional_no_false_prune"] is True
    assert one["incremental_propagation"]["exact_match_rate"] == 1.0
    assert one["baseline"] == two["baseline"]
    assert one["forward_certificate"] == two["forward_certificate"]
    assert one["bidirectional_necessary_interval"] == two["bidirectional_necessary_interval"]
    assert one["correctness"] == two["correctness"]


def test_patent_benchmark_records_compute_effect_fields():
    result = _case()
    for variant in ("forward_certificate", "bidirectional_necessary_interval"):
        assert "estimated_expensive_evaluations_avoided" in result[variant]
        assert "estimated_evaluation_reduction_fraction" in result[variant]
        assert 0.0 <= result[variant]["high_risk_prefix_recall"] <= 1.0
