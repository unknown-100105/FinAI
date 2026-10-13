import pytest

from finance_engine.counterfactual_stability import (
    CounterfactualRun,
    assess_counterfactual_stability,
)


def run(run_id, low, high, **overrides):
    values = {
        "run_id": run_id,
        "intervention_key": "rates:+100bp",
        "metric": "portfolio_loss_delta",
        "model_version": "v1",
        "graph_digest": "graph-a",
        "evidence_digest": "evidence-a",
        "regime": "baseline",
        "delta_low": low,
        "delta_high": high,
    }
    values.update(overrides)
    return CounterfactualRun(**values)


def test_consistent_direction_is_stable_across_versions():
    result = assess_counterfactual_stability([
        run("a", 1.0, 2.0),
        run("b", 0.5, 1.5, model_version="v2", graph_digest="graph-b"),
        run("c", 2.0, 3.0, regime="stress", evidence_digest="evidence-b"),
    ])
    assert result["status"] == "DIRECTION_STABLE"
    assert result["direction"] == "positive"
    assert result["directional_agreement"] == 1.0
    assert result["production_validated"] is False
    assert len(result["replay_digest"]) == 64


def test_sign_disagreement_is_flagged_as_sensitive():
    result = assess_counterfactual_stability([
        run("a", 1.0, 2.0),
        run("b", -2.0, -1.0),
        run("c", 0.5, 1.5),
    ])
    assert result["status"] == "MODEL_OR_EVIDENCE_SENSITIVE"
    assert result["direction"] == "mixed"
    assert result["directional_agreement"] == pytest.approx(2 / 3)


def test_interval_crossing_zero_is_indeterminate_not_stable():
    result = assess_counterfactual_stability([
        run("a", 0.1, 2.0),
        run("b", -0.1, 1.0),
        run("c", 0.2, 1.0),
    ])
    assert result["status"] == "INDETERMINATE_INTERVALS"
    assert result["direction"] == "unknown"
    assert result["indeterminate_run_ids"] == ["b"]


def test_unapproved_runs_do_not_support_conclusion():
    result = assess_counterfactual_stability([
        run("a", 1.0, 2.0),
        run("b", 1.0, 2.0, approved=False),
        run("c", 1.0, 2.0, model_version="v2"),
    ])
    assert result["status"] == "INSUFFICIENT_APPROVED_RUNS"
    assert result["approved_run_count"] == 2
    assert result["excluded_run_ids"] == ["b"]


def test_requires_same_intervention_and_metric():
    with pytest.raises(ValueError, match="same intervention"):
        assess_counterfactual_stability([
            run("a", 1.0, 2.0),
            run("b", 1.0, 2.0, intervention_key="oil:+10%"),
        ])


def test_rejects_duplicate_run_ids_and_invalid_intervals():
    with pytest.raises(ValueError, match="unique"):
        assess_counterfactual_stability([run("a", 1, 2), run("a", 1, 2)])
    with pytest.raises(ValueError, match="delta_low"):
        run("bad", 3, 2)


def test_replay_digest_is_order_independent():
    a, b, c = run("a", 1, 2), run("b", 2, 3), run("c", 3, 4)
    assert assess_counterfactual_stability([a, b, c])["replay_digest"] == assess_counterfactual_stability([c, a, b])["replay_digest"]
