"""Capability-aware execution planning for FinAI.

This module is intentionally provider-agnostic and has no optional ML dependencies.
It creates an auditable plan; it does not execute tools, authorize transactions, or
claim that a model/provider is available. Callers must enforce policy and authority
again at execution time.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any, Iterable, Mapping, Optional


class ExecutionMode(str, Enum):
    ONLINE = "online"
    DEGRADED = "degraded"
    OFFLINE = "offline"


class StepKind(str, Enum):
    POLICY_CHECK = "policy_check"
    MARKET_DATA = "market_data"
    DETERMINISTIC_TOOL = "deterministic_tool"
    STRUCTURED_KNOWLEDGE = "structured_knowledge"
    RETRIEVAL = "retrieval"
    RESOURCE_PLANNING = "resource_planning"
    MODEL_GENERATION = "model_generation"
    CLAIM_VERIFICATION = "claim_verification"
    RESPONSE_VERIFICATION = "response_verification"


@dataclass(frozen=True)
class Capability:
    """A named capability and its current operational evidence."""

    name: str
    available: bool
    modes: tuple[ExecutionMode, ...] = (ExecutionMode.ONLINE,)
    reason: str = ""
    metadata: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class PlanStep:
    step_id: str
    kind: StepKind
    capability: str
    required: bool = True
    depends_on: tuple[str, ...] = ()
    parameters: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class FinAIExecutionPlan:
    request_id: str
    intent: str
    mode: ExecutionMode
    steps: tuple[PlanStep, ...]
    blocked: bool
    explanations: tuple[str, ...] = ()
    schema_version: str = "1.0"

    def to_dict(self) -> dict[str, Any]:
        """Return JSON-friendly data without leaking provider credentials."""
        data = asdict(self)
        data["mode"] = self.mode.value
        for step in data["steps"]:
            step["kind"] = step["kind"].value
        return data


class CapabilityStateGraph:
    """Small in-memory capability graph with explicit, inspectable transitions.

    Nodes represent capabilities; directed edges represent declared prerequisites.
    This is a runtime state object, not a durable graph database. Persistence is a
    caller responsibility and must use an application-approved storage backend.
    """

    def __init__(self, capabilities: Iterable[Capability] = (),
                 prerequisites: Optional[Mapping[str, Iterable[str]]] = None) -> None:
        self._capabilities: dict[str, Capability] = {}
        self._prerequisites: dict[str, tuple[str, ...]] = {}
        for capability in capabilities:
            self.set_capability(capability)
        for name, required in (prerequisites or {}).items():
            self._prerequisites[name] = tuple(dict.fromkeys(required))
        self._validate_acyclic()

    def set_capability(self, capability: Capability) -> None:
        if not capability.name.strip():
            raise ValueError("capability name must not be empty")
        self._capabilities[capability.name] = capability

    def set_prerequisites(self, name: str, required: Iterable[str]) -> None:
        previous = self._prerequisites.get(name)
        self._prerequisites[name] = tuple(dict.fromkeys(required))
        try:
            self._validate_acyclic()
        except Exception:
            if previous is None:
                self._prerequisites.pop(name, None)
            else:
                self._prerequisites[name] = previous
            raise

    def get(self, name: str) -> Optional[Capability]:
        return self._capabilities.get(name)

    def is_available(self, name: str, mode: ExecutionMode) -> bool:
        capability = self._capabilities.get(name)
        if capability is None or not capability.available or mode not in capability.modes:
            return False
        return all(self.is_available(dep, mode)
                   for dep in self._prerequisites.get(name, ()))

    def explain_unavailable(self, name: str, mode: ExecutionMode) -> tuple[str, ...]:
        capability = self._capabilities.get(name)
        if capability is None:
            return (f"Capability '{name}' is not registered.",)
        reasons: list[str] = []
        if not capability.available:
            reasons.append(capability.reason or f"Capability '{name}' is disabled.")
        if mode not in capability.modes:
            reasons.append(f"Capability '{name}' does not support {mode.value} mode.")
        for dep in self._prerequisites.get(name, ()):
            if not self.is_available(dep, mode):
                reasons.extend(self.explain_unavailable(dep, mode))
        return tuple(dict.fromkeys(reasons))

    def snapshot(self) -> dict[str, Any]:
        return {
            "capabilities": {
                name: {
                    "available": cap.available,
                    "modes": sorted(mode.value for mode in cap.modes),
                    "reason": cap.reason,
                    "metadata": dict(cap.metadata),
                    "prerequisites": list(self._prerequisites.get(name, ())),
                }
                for name, cap in sorted(self._capabilities.items())
            }
        }

    def _validate_acyclic(self) -> None:
        visiting: set[str] = set()
        visited: set[str] = set()

        def visit(node: str) -> None:
            if node in visiting:
                raise ValueError(f"capability prerequisite cycle detected at '{node}'")
            if node in visited:
                return
            visiting.add(node)
            for parent in self._prerequisites.get(node, ()):
                visit(parent)
            visiting.remove(node)
            visited.add(node)

        for node in self._prerequisites:
            visit(node)


def build_execution_plan(
    *,
    request_id: str,
    intent: str,
    graph: CapabilityStateGraph,
    mode: ExecutionMode = ExecutionMode.ONLINE,
    require_retrieval: bool = True,
    require_market_data: bool = False,
    require_structured_knowledge: bool = False,
    require_resource_planning: bool = False,
    require_model: bool = True,
    require_claim_verification: bool = True,
    require_response_verification: bool = True,
) -> FinAIExecutionPlan:
    """Build a conservative plan from current capability state.

    Policy check is always first. Deterministic finance execution is only included
    when its capability is registered and available. Missing required stages block
    the plan; optional unavailable stages are omitted with an explanation.
    """
    if not request_id.strip():
        raise ValueError("request_id must not be empty")
    if not intent.strip():
        raise ValueError("intent must not be empty")

    requested = [("policy", StepKind.POLICY_CHECK, True)]
    if require_market_data:
        requested.append(("market_data", StepKind.MARKET_DATA, True))
    requested.append(("deterministic_finance", StepKind.DETERMINISTIC_TOOL, False))
    if require_structured_knowledge:
        requested.append(("structured_knowledge", StepKind.STRUCTURED_KNOWLEDGE, True))
    requested.append(("retrieval", StepKind.RETRIEVAL, require_retrieval))
    if require_resource_planning:
        requested.append(("resource_planning", StepKind.RESOURCE_PLANNING, True))
    requested.extend([
        ("model_generation", StepKind.MODEL_GENERATION, require_model),
        ("claim_verification", StepKind.CLAIM_VERIFICATION, require_claim_verification),
        ("response_verification", StepKind.RESPONSE_VERIFICATION, require_response_verification),
    ])
    steps: list[PlanStep] = []
    explanations: list[str] = []
    blocked = False
    previous_id: Optional[str] = None

    for capability, kind, required in requested:
        # Deterministic finance is intent-dependent; do not force it on every request.
        if capability == "deterministic_finance" and not any(
            token in intent.lower()
            for token in (
                "calculate", "calculation", "emi", "loan", "budget",
                "portfolio", "payment", "interest", "tax", "sip",
                "compound", "fixed_deposit", "recurring_deposit",
                "finance_engine", "financial_calculation",
            )
        ):
            continue
        if not graph.is_available(capability, mode):
            why = graph.explain_unavailable(capability, mode)
            if required:
                blocked = True
                explanations.extend(why)
            elif why:
                explanations.extend(f"Optional stage skipped: {reason}" for reason in why)
            continue
        step_id = f"{len(steps) + 1:02d}_{capability}"
        steps.append(PlanStep(
            step_id=step_id,
            kind=kind,
            capability=capability,
            required=required,
            depends_on=(previous_id,) if previous_id else (),
        ))
        previous_id = step_id

    return FinAIExecutionPlan(
        request_id=request_id,
        intent=intent,
        mode=mode,
        steps=tuple(steps),
        blocked=blocked,
        explanations=tuple(dict.fromkeys(explanations)),
    )
