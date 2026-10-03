import pytest

from causal_risk.constrained_gfnets import CausalConstrainedTailGenerator
from causal_risk.gfnets import GFlowConfig


def test_causal_constrained_generator_masks_infeasible_actions():
    nodes = ["rates", "credit", "portfolio"]
    edges = [
        {"source": "rates", "target": "credit", "weight": 0.8},
        {"source": "credit", "target": "portfolio", "weight": 0.9},
    ]
    bounds = {node: (-100.0, 100.0) for node in nodes}
    generator = CausalConstrainedTailGenerator(
        ["rates", "credit"],
        GFlowConfig(hidden_dim=16, epochs=2, seed=7, device="cpu"),
    )
    generator.train()
    result = generator.sample(
        {"rates": 10.0, "credit": 10.0},
        nodes=nodes,
        edges=edges,
        node_bounds=bounds,
        target_node="portfolio",
        target_interval=(-100.0, 100.0),
        draws=8,
        seed=7,
    )
    assert result["status"] == "CAUSALLY_CONSTRAINED_TRAJECTORIES_READY"
    assert len(result["trajectories"]) == 8
    assert result["screening"]["baseline_candidate_evaluations"] > 0


def test_causal_constrained_generator_rejects_no_feasible_action():
    nodes = ["rates", "portfolio"]
    edges = [{"source": "rates", "target": "portfolio", "weight": 1.0}]
    bounds = {"rates": (-10.0, 10.0), "portfolio": (-10.0, 10.0)}
    generator = CausalConstrainedTailGenerator(
        ["rates"],
        GFlowConfig(hidden_dim=16, epochs=1, seed=3, device="cpu"),
    )
    generator.train()
    with pytest.raises(ValueError, match="no feasible next action"):
        generator.sample(
            {"rates": 5.0},
            nodes=nodes,
            edges=edges,
            node_bounds=bounds,
            target_node="portfolio",
            target_interval=(90.0, 100.0),
            draws=1,
        )
