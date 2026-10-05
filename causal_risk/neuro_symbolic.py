"""Deterministic financial constraint layer for neuro-symbolic safety."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Sequence

import math


@dataclass(frozen=True)
class RuleResult:
    rule_id: str
    passed: bool
    message: str
    severity: str


DEFAULT_RULES = (
    "allocation_sum_100",
    "allocation_nonnegative",
    "shock_bounds",
    "no_unknown_intervention",
    "research_gate_required",
)


class FinancialConstraintEngine:
    """Hard-rule validator that can reject model proposals deterministically."""

    def __init__(self, shock_limit: float = 150.0) -> None:
        if shock_limit <= 0:
            raise ValueError("shock_limit must be positive")
        self.shock_limit = float(shock_limit)

    def validate(
        self,
        allocation: Mapping[str, float],
        shock: Mapping[str, float],
        allowed_shocks: Sequence[str],
        *,
        research_graph_ready: bool,
    ) -> dict[str, Any]:
        rules: list[RuleResult] = []

        total = sum(float(value) for value in allocation.values())
        rules.append(RuleResult(
            "allocation_sum_100",
            math.isclose(total, 100.0, abs_tol=1e-6),
            f"allocation total={total:.6f}",
            "error",
        ))
        nonnegative = all(float(value) >= 0 for value in allocation.values())
        rules.append(RuleResult(
            "allocation_nonnegative",
            nonnegative,
            "allocation weights must be non-negative",
            "error",
        ))
        finite = all(math.isfinite(float(value)) for value in shock.values())
        within = finite and all(abs(float(value)) <= self.shock_limit for value in shock.values())
        rules.append(RuleResult(
            "shock_bounds",
            within,
            f"shock magnitudes must be finite and <= {self.shock_limit}",
            "error",
        ))
        unknown = sorted(set(shock) - set(allowed_shocks))
        rules.append(RuleResult(
            "no_unknown_intervention",
            not unknown,
            f"unknown interventions: {unknown}" if unknown else "all interventions are supported",
            "error",
        ))
        rules.append(RuleResult(
            "research_gate_required",
            bool(research_graph_ready),
            "research graph must be explicitly approved before research counterfactual use",
            "error",
        ))

        passed = all(rule.passed for rule in rules)
        return {
            "passed": passed,
            "rules": [rule.__dict__ for rule in rules],
            "failed_rule_ids": [rule.rule_id for rule in rules if not rule.passed],
            "semantics": "Hard symbolic rules are deterministic constraints; model-generated suggestions cannot override a failed rule.",
        }
