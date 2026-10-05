import pytest

from causal_risk.research_control_plane import (
    EvaluationLease,
    EvidenceItem,
    ResearchMode,
    build_experiment_proof,
    derive_research_capability,
    derive_safe_mode,
    digest,
    evaluate_evidence,
)


def _evidence(now=1000.0):
    return evaluate_evidence(
        [
            EvidenceItem("balance", 999.0, 60.0, 0.99),
            EvidenceItem("identity", 998.0, 60.0, 0.98),
        ],
        now=now,
    )


def test_evidence_state_is_deterministic():
    assert _evidence().evidence_digest == _evidence().evidence_digest
    assert _evidence().is_fresh is True


def test_stale_evidence_is_explicit():
    state = evaluate_evidence(
        [EvidenceItem("old", 0.0, 10.0, 0.99)],
        now=100.0,
    )
    assert state.stale_count == 1
    assert state.is_fresh is False


def test_evidence_conflict_is_explicit():
    state = evaluate_evidence(
        [
            EvidenceItem("a", 999.0, 60.0, 0.99),
            EvidenceItem("b", 999.0, 60.0, 0.99),
        ],
        now=1000.0,
        conflict_pairs=(("a", "b"),),
    )
    assert state.conflict_count == 1
    assert state.is_conflicted is True


@pytest.mark.parametrize(
    ("uncertainty", "disagreement", "expected"),
    [
        (0.05, 0.05, ResearchMode.FULL),
        (0.20, 0.10, ResearchMode.RESTRICTED),
        (0.45, 0.40, ResearchMode.SAFE),
        (0.80, 0.70, ResearchMode.QUARANTINE),
    ],
)
def test_uncertainty_and_disagreement_change_research_capability(
    uncertainty, disagreement, expected
):
    envelope = derive_research_capability(
        uncertainty=uncertainty,
        disagreement=disagreement,
        evidence=_evidence(),
        operations=("evaluate", "stress", "report"),
    )
    assert envelope.mode == expected


def test_conflicted_evidence_limits_operations():
    evidence = evaluate_evidence(
        [
            EvidenceItem("a", 999.0, 60.0),
            EvidenceItem("b", 999.0, 60.0),
        ],
        now=1000.0,
        conflict_pairs=(("a", "b"),),
    )
    envelope = derive_research_capability(
        uncertainty=0.02,
        disagreement=0.02,
        evidence=evidence,
        operations=("evaluate", "stress"),
    )
    assert envelope.mode == ResearchMode.SAFE
    assert envelope.allowed_operations == ("evaluate",)


def test_evaluation_lease_invalidates_when_state_changes():
    evidence = _evidence()
    lease = EvaluationLease.issue(
        experiment_id="exp-1",
        state={"prefix": {"rates": 2.0}},
        model_version="m1",
        policy_version="p1",
        evidence_digest=evidence.evidence_digest,
        ttl_seconds=60,
        issued_at=1000.0,
    )
    valid = lease.validate(
        state={"prefix": {"rates": 2.0}},
        model_version="m1",
        policy_version="p1",
        evidence_digest=evidence.evidence_digest,
        now=1020.0,
    )
    changed = lease.validate(
        state={"prefix": {"rates": 3.0}},
        model_version="m1",
        policy_version="p1",
        evidence_digest=evidence.evidence_digest,
        now=1020.0,
    )
    assert valid["valid"] is True
    assert "state_changed" in changed["reasons"]


def test_evaluation_lease_expires():
    evidence = _evidence()
    lease = EvaluationLease.issue(
        experiment_id="exp-1",
        state={"x": 1},
        model_version="m1",
        policy_version="p1",
        evidence_digest=evidence.evidence_digest,
        ttl_seconds=10,
        issued_at=1000.0,
    )
    result = lease.validate(
        state={"x": 1},
        model_version="m1",
        policy_version="p1",
        evidence_digest=evidence.evidence_digest,
        now=1011.0,
    )
    assert result["valid"] is False
    assert "lease_expired" in result["reasons"]


def test_safe_mode_is_deterministic():
    assert derive_safe_mode(
        model_available=True,
        evidence_available=True,
        graph_valid=True,
        operations=("evaluate",),
    ) == ResearchMode.FULL
    assert derive_safe_mode(
        model_available=False,
        evidence_available=True,
        graph_valid=True,
        operations=("evaluate",),
    ) == ResearchMode.SAFE
    assert derive_safe_mode(
        model_available=True,
        evidence_available=True,
        graph_valid=False,
        operations=("evaluate",),
    ) == ResearchMode.QUARANTINE


def test_experiment_proof_is_reproducible():
    evidence = _evidence()
    capability = derive_research_capability(
        uncertainty=0.05,
        disagreement=0.05,
        evidence=evidence,
        operations=("evaluate", "stress"),
    )
    lease = EvaluationLease.issue(
        experiment_id="exp-1",
        state={"x": 1},
        model_version="m1",
        policy_version="p1",
        evidence_digest=evidence.evidence_digest,
        ttl_seconds=60,
        issued_at=1000.0,
    )
    one = build_experiment_proof(
        experiment_id="exp-1",
        input_digest=digest({"x": 1}),
        evidence=evidence,
        capability=capability,
        lease=lease,
        metrics={"evaluations_avoided": 12},
    )
    two = build_experiment_proof(
        experiment_id="exp-1",
        input_digest=digest({"x": 1}),
        evidence=evidence,
        capability=capability,
        lease=lease,
        metrics={"evaluations_avoided": 12},
    )
    assert one["proof_digest"] == two["proof_digest"]
