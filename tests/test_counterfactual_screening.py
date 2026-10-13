import random

import pytest

from finance_engine.counterfactual_screening import (
    BoundedLinearDAG,
    CounterfactualAction,
    Interval,
    LinearNode,
    benchmark_screening,
)


def build_model():
    return BoundedLinearDAG([
        LinearNode("rate_shock", Interval(-5, 5)),
        LinearNode("funding_spread", Interval(-10, 10),
                   parents={"rate_shock": 1.5}, intercept=1.0,
                   noise=Interval(-0.5, 0.5)),
        LinearNode("default_rate", Interval(-25, 25),
                   parents={"funding_spread": 2.0},
                   noise=Interval(-1.0, 1.0)),
        LinearNode("portfolio_loss", Interval(-20, 20),
                   parents={"default_rate": 0.8}, intercept=2.0,
                   noise=Interval(-0.5, 0.5)),
    ])


def actions():
    bands = [(-5, -4), (-3, -2), (-1, 0), (0.5, 1),
             (1.5, 2), (2, 2.5), (3, 3.5), (4, 5)]
    return [
        CounterfactualAction(f"shock_{i}", {"rate_shock": Interval(low, high)})
        for i, (low, high) in enumerate(bands)
    ]


def sampled_reference_evaluator(model, target, target_interval, trials=3000):
    def evaluate(action):
        rng = random.Random(20261013 + sum(ord(c) for c in action.action_id))
        for _ in range(trials):
            values = {}
            valid = True
            for name in model.order:
                node = model.nodes[name]
                if name in action.interventions:
                    chosen = action.interventions[name].intersection(node.domain)
                    if chosen is None:
                        valid = False
                        break
                    value = rng.uniform(chosen.low, chosen.high)
                else:
                    value = node.intercept + rng.uniform(node.noise.low, node.noise.high)
                    value += sum(coef * values[parent] for parent, coef in node.parents.items())
                if not node.domain.low <= value <= node.domain.high:
                    valid = False
                    break
                values[name] = value
            if valid and target_interval.low <= values[target] <= target_interval.high:
                return True
        return False
    return evaluate


def test_interval_arithmetic_handles_negative_coefficients():
    assert Interval(2, 4).scale(-3) == Interval(-12, -6)
    assert Interval(1, 3) - Interval(4, 7) == Interval(-6, -1)


def test_rejects_cycles():
    with pytest.raises(ValueError, match="acyclic"):
        BoundedLinearDAG([
            LinearNode("a", Interval(-10, 10), parents={"b": 1}),
            LinearNode("b", Interval(-10, 10), parents={"a": 1}),
        ])


def test_masks_actions_outside_backward_necessary_interval():
    result = build_model().screen_actions("portfolio_loss", Interval(10, 15), actions())
    by_id = {item.action_id: item for item in result}
    assert by_id["shock_0"].status == "MASK"
    assert by_id["shock_0"].reason.startswith("BACKWARD_CERTIFICATE_DISJOINT")
    assert by_id["shock_7"].status == "RETAIN"


def test_screening_retains_every_feasible_sampled_action():
    model, band = build_model(), Interval(10, 15)
    result = benchmark_screening(
        model, "portfolio_loss", band, actions(),
        sampled_reference_evaluator(model, "portfolio_loss", band),
    )
    assert result["all_reference_feasible_actions_retained"] is True
    assert result["reference_recall"] == 1.0
    assert result["candidate_evaluations_avoided"] > 0
    assert result["screened_reference_evaluation_calls"] < result["exhaustive_reference_evaluation_calls"]


def test_only_intervention_descendant_cone_is_recomputed():
    result = build_model().screen_actions(
        "portfolio_loss", Interval(10, 15),
        [CounterfactualAction("candidate", {"rate_shock": Interval(4, 4.5)})],
    )[0]
    assert result.recomputed_nodes == (
        "rate_shock", "funding_spread", "default_rate", "portfolio_loss"
    )
    assert result.interval_equations_evaluated == 3


def test_bad_intervention_domain_is_masked_with_reason():
    result = build_model().screen_actions(
        "portfolio_loss", Interval(10, 15),
        [CounterfactualAction("outside", {"rate_shock": Interval(9, 10)})],
    )[0]
    assert result.status == "MASK"
    assert result.reason == "INTERVENTION_OUTSIDE_DOMAIN:rate_shock"


def test_unknown_node_is_rejected():
    with pytest.raises(ValueError, match="unknown nodes"):
        build_model().screen_actions(
            "portfolio_loss", Interval(10, 15),
            [CounterfactualAction("bad", {"unknown": Interval(0, 1)})],
        )


def test_target_interval_outside_domain_masks_candidates():
    result = build_model().screen_actions(
        "portfolio_loss", Interval(30, 40),
        [CounterfactualAction("candidate", {"rate_shock": Interval(4, 5)})],
    )[0]
    assert result.status == "MASK"
    assert result.reason == "TARGET_INTERVAL_UNREACHABLE_BY_BOUNDED_MODEL"


def test_seeded_multibranch_graphs_never_mask_a_known_feasible_world():
    rng = random.Random(20261013)
    for case_index in range(80):
        count = rng.randint(3, 7)
        names = [f"v{i}" for i in range(count)]
        nodes = []
        for index, name in enumerate(names):
            parents = {
                names[parent_index]: rng.choice([-2.0, -1.0, 1.0, 2.0])
                for parent_index in range(index)
                if rng.random() < 0.35
            }
            nodes.append(LinearNode(
                name=name, domain=Interval(-1000, 1000), parents=parents,
                intercept=rng.choice([-2.0, -1.0, 0.0, 1.0, 2.0]),
                noise=Interval(-2, 2) if not parents else Interval(-1, 1),
            ))
        model = BoundedLinearDAG(nodes)
        action_node = rng.choice(names[:-1])
        intervention_value = rng.uniform(-5, 5)
        action = CounterfactualAction(
            f"random_{case_index}",
            {action_node: Interval(intervention_value, intervention_value)},
        )
        world_rng, values = random.Random(8000 + case_index), {}
        for name in model.order:
            node = model.nodes[name]
            if name == action_node:
                value = intervention_value
            else:
                value = node.intercept + world_rng.uniform(node.noise.low, node.noise.high)
                value += sum(coef * values[parent] for parent, coef in node.parents.items())
            assert node.domain.low <= value <= node.domain.high
            values[name] = value
        target_value = values[names[-1]]
        band = Interval(target_value - 0.01, target_value + 0.01)
        certificate = model.screen_actions(names[-1], band, [action])[0]
        assert certificate.status == "RETAIN", (
            f"False prune on seeded case {case_index}: {certificate.as_dict()}"
        )
