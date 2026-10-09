import pytest

from orchestrator.execution_plan import (
    Capability, CapabilityStateGraph, ExecutionMode, StepKind, build_execution_plan,
)


def graph_for(*, model=True, retrieval=True):
    modes = tuple(ExecutionMode)
    return CapabilityStateGraph(
        capabilities=[
            Capability("policy", True, modes),
            Capability("deterministic_finance", True, modes),
            Capability("retrieval", retrieval, modes, "retrieval index unavailable"),
            Capability("model_generation", model, modes, "no model configured"),
            Capability("claim_verification", True, modes),
            Capability("response_verification", True, modes),
        ],
        prerequisites={"model_generation": ("policy",)},
    )


def test_plan_orders_stages_and_serializes():
    plan = build_execution_plan(
        request_id="req-1", intent="calculate loan interest",
        graph=graph_for(), mode=ExecutionMode.OFFLINE,
    )
    assert not plan.blocked
    assert [s.kind for s in plan.steps] == [
        StepKind.POLICY_CHECK, StepKind.DETERMINISTIC_TOOL, StepKind.RETRIEVAL,
        StepKind.MODEL_GENERATION, StepKind.CLAIM_VERIFICATION,
        StepKind.RESPONSE_VERIFICATION,
    ]
    assert plan.steps[1].depends_on == (plan.steps[0].step_id,)
    assert plan.to_dict()["mode"] == "offline"


def test_missing_required_model_blocks_plan():
    plan = build_execution_plan(
        request_id="req-2", intent="explain market risk",
        graph=graph_for(model=False),
    )
    assert plan.blocked
    assert any("no model configured" in reason for reason in plan.explanations)


def test_optional_retrieval_can_be_skipped_without_blocking():
    plan = build_execution_plan(
        request_id="req-3", intent="explain market risk",
        graph=graph_for(retrieval=False), require_retrieval=False,
    )
    assert not plan.blocked
    assert all(step.capability != "retrieval" for step in plan.steps)
    assert any("Optional stage skipped" in reason for reason in plan.explanations)


def test_unknown_capability_is_unavailable():
    graph = CapabilityStateGraph()
    assert not graph.is_available("missing", ExecutionMode.ONLINE)
    assert "not registered" in graph.explain_unavailable("missing", ExecutionMode.ONLINE)[0]


def test_prerequisite_cycle_is_rejected():
    with pytest.raises(ValueError, match="cycle"):
        CapabilityStateGraph(prerequisites={"a": ("b",), "b": ("a",)})


def test_empty_request_fields_are_rejected():
    graph = graph_for()
    for kwargs in ({"request_id": "", "intent": "chat"}, {"request_id": "id", "intent": ""}):
        with pytest.raises(ValueError):
            build_execution_plan(graph=graph, **kwargs)
