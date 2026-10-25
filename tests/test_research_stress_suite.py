from benchmarks.research_stress_suite import run_suite


def test_research_pruning_stress_suite_has_no_false_prunes_or_propagation_mismatch():
    report = run_suite()

    assert report["status"] == "passed"
    assert report["scenario_count"] == 8
    assert report["passed_scenarios"] == 8
    assert report["failure_count"] == 0
    assert all(item["forward_false_prunes"] == 0 for item in report["scenarios"])
    assert all(item["bidirectional_false_prunes"] == 0 for item in report["scenarios"])
    assert all(item["incremental_exact_match_rate"] == 1.0 for item in report["scenarios"])
