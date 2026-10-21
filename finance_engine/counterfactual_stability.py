"""Robustness gate for repeated counterfactual risk estimates.

Research-only: this module measures directional stability across independently
versioned runs. It does not establish causal identification or financial validity.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
import math
from typing import Any, Iterable


@dataclass(frozen=True)
class CounterfactualRun:
    run_id: str
    intervention_key: str
    metric: str
    model_version: str
    graph_digest: str
    evidence_digest: str
    regime: str
    delta_low: float
    delta_high: float
    approved: bool = True

    def __post_init__(self) -> None:
        for name in (
            "run_id", "intervention_key", "metric", "model_version",
            "graph_digest", "evidence_digest", "regime",
        ):
            if not getattr(self, name).strip():
                raise ValueError(f"{name} must be non-empty")
        if not math.isfinite(self.delta_low) or not math.isfinite(self.delta_high):
            raise ValueError("delta bounds must be finite")
        if self.delta_low > self.delta_high:
            raise ValueError("delta_low must not exceed delta_high")


def _sign(run: CounterfactualRun) -> int | None:
    """Return +1/-1 only when the whole interval excludes zero."""
    if run.delta_low > 0:
        return 1
    if run.delta_high < 0:
        return -1
    return None


def assess_counterfactual_stability(
    runs: Iterable[CounterfactualRun],
    *,
    min_approved_runs: int = 3,
    min_directional_agreement: float = 1.0,
) -> dict[str, Any]:
    """Assess whether an intervention's estimated direction survives model/evidence changes.

    The method is deliberately conservative: an interval touching or crossing zero
    is indeterminate, not positive or negative. Unapproved runs are recorded but
    never used to support a stable conclusion.
    """
    submitted = tuple(runs)
    if min_approved_runs < 2:
        raise ValueError("min_approved_runs must be at least 2")
    if not math.isfinite(min_directional_agreement) or not 0 < min_directional_agreement <= 1:
        raise ValueError("min_directional_agreement must be in (0, 1]")
    if not submitted:
        raise ValueError("at least one run is required")
    ids = [run.run_id for run in submitted]
    if len(ids) != len(set(ids)):
        raise ValueError("run_id values must be unique")
    keys = {(run.intervention_key, run.metric) for run in submitted}
    if len(keys) != 1:
        raise ValueError("all runs must evaluate the same intervention_key and metric")

    approved = tuple(run for run in submitted if run.approved)
    excluded_ids = sorted(run.run_id for run in submitted if not run.approved)
    signs = [_sign(run) for run in approved]
    decisive = [sign for sign in signs if sign is not None]
    positive = sum(sign == 1 for sign in decisive)
    negative = sum(sign == -1 for sign in decisive)
    agreement = max(positive, negative) / len(decisive) if decisive else 0.0
    has_indeterminate = any(sign is None for sign in signs)

    if len(approved) < min_approved_runs:
        status = "INSUFFICIENT_APPROVED_RUNS"
        direction = "unknown"
    elif has_indeterminate:
        status = "INDETERMINATE_INTERVALS"
        direction = "unknown"
    elif agreement < min_directional_agreement or (positive and negative):
        status = "MODEL_OR_EVIDENCE_SENSITIVE"
        direction = "mixed"
    elif positive == len(approved):
        status = "DIRECTION_STABLE"
        direction = "positive"
    elif negative == len(approved):
        status = "DIRECTION_STABLE"
        direction = "negative"
    else:
        status = "INDETERMINATE_INTERVALS"
        direction = "unknown"

    canonical_runs = [
        asdict(run) for run in sorted(submitted, key=lambda item: item.run_id)
    ]
    run_digest = hashlib.sha256(
        json.dumps(canonical_runs, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    approved_midpoints = [(run.delta_low + run.delta_high) / 2 for run in approved]
    return {
        "status": status,
        "experimental": True,
        "production_validated": False,
        "intervention_key": submitted[0].intervention_key,
        "metric": submitted[0].metric,
        "direction": direction,
        "approved_run_count": len(approved),
        "submitted_run_count": len(submitted),
        "excluded_run_ids": excluded_ids,
        "indeterminate_run_ids": sorted(
            run.run_id for run, sign in zip(approved, signs) if sign is None
        ),
        "directional_agreement": agreement,
        "directional_agreement_threshold": min_directional_agreement,
        "aggregate_delta_envelope": (
            [min(run.delta_low for run in approved), max(run.delta_high for run in approved)]
            if approved else None
        ),
        "mean_interval_midpoint": (
            sum(approved_midpoints) / len(approved_midpoints) if approved_midpoints else None
        ),
        "model_versions": sorted({run.model_version for run in approved}),
        "graph_digests": sorted({run.graph_digest for run in approved}),
        "evidence_digests": sorted({run.evidence_digest for run in approved}),
        "regimes": sorted({run.regime for run in approved}),
        "replay_digest": run_digest,
        "interpretation": (
            "Directional stability is a robustness diagnostic across supplied runs, "
            "not proof of causal identification, calibrated probability, or future returns."
        ),
    }
