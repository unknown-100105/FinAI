import numpy as np
import pytest

from causal_risk.feasibility_pruning import (
    AdaptivePruningController,
    evaluate_prefix_feasibility,
    propagate_interval_bounds,
    screen_candidate_actions,
)


NODES = ["rates", "credit", "liquidity", "equity", "portfolio"]
EDGES = [
    {"source": "rates", "target": "credit", "weight": 0.7, "lag": 0},
    {"source": "credit", "target": "liquidity", "weight": 0.8, "lag": 0},
    {"source": "liquidity", "target": "equity", "weight": 0.9, "lag": 0},
    {"source": "equity", "target": "portfolio", "weight": 0.8, "lag": 0},
]
BOUNDS = {
    "rates": (-100, 100),
    "credit": (-100, 100),
    "liquidity": (-100, 100),
    "equity": (-100, 100),
    "portfolio": (-100, 100),
}


def test_interval_propagation_is_deterministic():
    result = propagate_interval_bounds(
        NODES,
        EDGES,
        {"rates": 80},
        BOUNDS,
    )
    assert result["rates"] == (80.0, 80.0)
    assert result["credit"] == (56.0, 56.0)
    assert result["liquidity"] == (44.800000000000004, 44.800000000000004)
    assert result["equity"] == (40.320000000000004, 40.320000000000004)


def test_infeasible_prefix_is_hard_pruned():
    certificate = evaluate_prefix_feasibility(
        NODES,
        EDGES,
        {"rates": -100},
        BOUNDS,
        target_node="portfolio",
        target_interval=(70, 100),
    )
    assert certificate.hard_infeasible is True
    assert certificate.reason.startswith("target interval")


def test_feasible_prefix_is_not_hard_pruned():
    certificate = evaluate_prefix_feasibility(
        NODES,
        EDGES,
        {"rates": 100},
        BOUNDS,
        target_node="portfolio",
        target_interval=(45, 70),
    )
    assert certificate.hard_infeasible is False
    assert certificate.reachable_interval[0] <= 64.0 <= certificate.reachable_interval[1]


def test_empirical_support_can_reject_extreme_action():
    certificate = evaluate_prefix_feasibility(
        NODES,
        EDGES,
        {"rates": 100},
        BOUNDS,
        target_node="portfolio",
        target_interval=(0, 100),
        empirical_center={"rates": 0},
        empirical_scale={"rates": 10},
        max_standardized_deviation=4.0,
    )
    assert certificate.hard_infeasible is True
    assert certificate.empirical_support_ok is False


def test_screening_separates_hard_and_adaptive_pruning():
    controller = AdaptivePruningController(
        target_full_eval_fraction=0.5,
        current_margin=10.0,
    )
    result = screen_candidate_actions(
        NODES,
        EDGES,
        {},
        {"rates": [-100, -50, 0, 50, 100]},
        BOUNDS,
        target_node="portfolio",
        target_interval=(40, 70),
        controller=controller,
    )
    assert result["total_candidates"] == 5
    assert result["hard_pruned_candidates"] >= 1
    assert result["hard_pruned_candidates"] + result["accepted_candidates"] + result["adaptive_pruned_candidates"] == 5


def test_controller_moves_toward_compute_budget():
    controller = AdaptivePruningController(
        target_full_eval_fraction=0.25,
        current_margin=0.0,
        margin_step=0.1,
    )
    assert controller.update(0.8) == pytest.approx(0.1)
    assert controller.update(0.1) == pytest.approx(0.0)
