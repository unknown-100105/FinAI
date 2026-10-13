"""Experimental EPCRP engine: evidence-gated paired-world risk propagation.

Static, caller-supplied DAG reference implementation. This module does not discover
causal relationships, simulate lagged time-series transitions, or validate finance.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, replace
from datetime import datetime, timezone
import hashlib
import json
import math
import random
from typing import Mapping, Optional, Sequence

METHOD_VERSION = "EPCRP-0.2"


def _parse_timestamp(value: str) -> datetime:
    if not isinstance(value, str) or not value.strip():
        raise ValueError("timestamp must be a non-empty ISO-8601 string")
    try:
        parsed = datetime.fromisoformat(value.strip().replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError(f"invalid ISO-8601 timestamp: {value!r}") from exc
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _finite(value: float, field_name: str) -> float:
    number = float(value)
    if not math.isfinite(number):
        raise ValueError(f"{field_name} must be finite")
    return number


def _digest(payload: object) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"),
                         ensure_ascii=True).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


@dataclass(frozen=True)
class RiskNode:
    name: str
    intercept: float = 0.0

    def __post_init__(self) -> None:
        if not isinstance(self.name, str) or not self.name.strip():
            raise ValueError("node name must be a non-empty string")
        _finite(self.intercept, f"intercept for node {self.name}")


@dataclass(frozen=True)
class EvidenceEdge:
    source: str
    target: str
    coefficient: float
    evidence_id: str
    support_score: float = 1.0
    regime: str = "all"
    valid_from: Optional[str] = None
    valid_to: Optional[str] = None
    validated: bool = True
    coefficient_std: float = 0.0

    def __post_init__(self) -> None:
        if not isinstance(self.source, str) or not self.source.strip():
            raise ValueError("edge source must be a non-empty string")
        if not isinstance(self.target, str) or not self.target.strip():
            raise ValueError("edge target must be a non-empty string")
        if not isinstance(self.evidence_id, str):
            raise ValueError("evidence_id must be a string")
        _finite(self.coefficient, "edge coefficient")
        support = _finite(self.support_score, "support_score")
        if not 0.0 <= support <= 1.0:
            raise ValueError("support_score must be between 0 and 1")
        spread = _finite(self.coefficient_std, "coefficient_std")
        if spread < 0:
            raise ValueError("coefficient_std must be non-negative")
        if self.valid_from:
            _parse_timestamp(self.valid_from)
        if self.valid_to:
            _parse_timestamp(self.valid_to)
        if self.valid_from and self.valid_to:
            if _parse_timestamp(self.valid_from) > _parse_timestamp(self.valid_to):
                raise ValueError("valid_from must not be after valid_to")

    @property
    def key(self) -> str:
        evidence = self.evidence_id.strip() or "NO_EVIDENCE"
        return f"{self.source}->{self.target}[{evidence}]"

    def rejection_reason(self, *, regime: str, as_of: datetime,
                         min_support: float) -> Optional[str]:
        if not self.validated:
            return "edge_not_validated"
        if not self.evidence_id.strip():
            return "missing_evidence_id"
        if self.support_score < min_support:
            return "support_below_threshold"
        requested_regime = (regime or "").strip().casefold()
        edge_regime = (self.regime or "").strip().casefold()
        if edge_regime not in {"", "all", requested_regime}:
            return "regime_mismatch"
        if self.valid_from and as_of < _parse_timestamp(self.valid_from):
            return "before_validity_window"
        if self.valid_to and as_of > _parse_timestamp(self.valid_to):
            return "after_validity_window"
        return None


@dataclass(frozen=True)
class EPCRPResult:
    baseline: Mapping[str, float]
    counterfactual: Mapping[str, float]
    node_delta: Mapping[str, float]
    portfolio_delta: float
    accepted_edge_keys: tuple[str, ...]
    rejected_edges: Mapping[str, str]
    evidence_by_output: Mapping[str, tuple[str, ...]]
    uncertainty_interval: Optional[tuple[float, float]]
    uncertainty_samples: int
    manifest: Mapping[str, object]

    def to_dict(self) -> dict[str, object]:
        """Return JSON-friendly result data for API and XAI consumers."""
        return {
            "baseline": dict(self.baseline),
            "counterfactual": dict(self.counterfactual),
            "node_delta": dict(self.node_delta),
            "portfolio_delta": self.portfolio_delta,
            "accepted_edge_keys": list(self.accepted_edge_keys),
            "rejected_edges": dict(self.rejected_edges),
            "evidence_by_output": {
                name: list(ids) for name, ids in self.evidence_by_output.items()
            },
            "uncertainty_interval": (
                list(self.uncertainty_interval) if self.uncertainty_interval else None
            ),
            "uncertainty_samples": self.uncertainty_samples,
            "manifest": dict(self.manifest),
        }


class EvidenceGatedRiskGraph:
    """Paired-world evaluator for a caller-supplied directed acyclic graph.

    Non-overridden node equation:
        x_v = intercept_v + sum(coef_uv * x_u for accepted edges u -> v)

    Source values are held fixed in both worlds. Intervention values override only
    the counterfactual world. Portfolio exposure weights must be calibrated by caller.
    """

    def __init__(self, nodes: Sequence[RiskNode], edges: Sequence[EvidenceEdge],
                 *, min_support: float = 0.60,
                 model_version: str = "unspecified") -> None:
        if not math.isfinite(float(min_support)) or not 0.0 <= min_support <= 1.0:
            raise ValueError("min_support must be finite and between 0 and 1")
        if not isinstance(model_version, str) or not model_version.strip():
            raise ValueError("model_version must not be empty")
        self.nodes = {node.name: node for node in nodes}
        if len(self.nodes) != len(nodes):
            raise ValueError("node names must be unique")
        if not self.nodes:
            raise ValueError("at least one node is required")
        self.edges = list(edges)
        self.min_support = float(min_support)
        self.model_version = model_version
        self._validate_endpoints()

    def _validate_endpoints(self) -> None:
        for edge in self.edges:
            if edge.source not in self.nodes or edge.target not in self.nodes:
                raise ValueError(
                    f"edge {edge.key} refers to an unknown source or target node"
                )

    def _accepted_edges(self, *, regime: str, as_of: datetime
                        ) -> tuple[list[EvidenceEdge], dict[str, str]]:
        accepted: list[EvidenceEdge] = []
        rejected: dict[str, str] = {}
        for edge in self.edges:
            reason = edge.rejection_reason(
                regime=regime, as_of=as_of, min_support=self.min_support
            )
            if reason is None:
                accepted.append(edge)
            else:
                rejected[edge.key] = reason
        return accepted, rejected

    def _topological_order(self, edges: Sequence[EvidenceEdge]) -> list[str]:
        incoming = {name: 0 for name in self.nodes}
        outgoing: dict[str, list[str]] = {name: [] for name in self.nodes}
        for edge in edges:
            incoming[edge.target] += 1
            outgoing[edge.source].append(edge.target)
        ready = sorted(name for name, degree in incoming.items() if degree == 0)
        order: list[str] = []
        while ready:
            current = ready.pop(0)
            order.append(current)
            for child in sorted(outgoing[current]):
                incoming[child] -= 1
                if incoming[child] == 0:
                    ready.append(child)
                    ready.sort()
        if len(order) != len(self.nodes):
            raise ValueError("accepted causal edges must form an acyclic graph (DAG)")
        return order

    def _evaluate(self, *, overrides: Mapping[str, float],
                  edges: Sequence[EvidenceEdge],
                  order: Sequence[str]) -> dict[str, float]:
        incoming: dict[str, list[EvidenceEdge]] = {name: [] for name in self.nodes}
        for edge in edges:
            incoming[edge.target].append(edge)
        values: dict[str, float] = {}
        for name in order:
            if name in overrides:
                values[name] = _finite(overrides[name], f"value for node {name}")
                continue
            value = float(self.nodes[name].intercept)
            for edge in incoming[name]:
                value += edge.coefficient * values[edge.source]
            values[name] = _finite(value, f"evaluated value for node {name}")
        return values

    @staticmethod
    def _evidence_lineage(*, edges: Sequence[EvidenceEdge],
                          interventions: Mapping[str, float],
                          node_delta: Mapping[str, float],
                          portfolio_exposures: Mapping[str, float]
                          ) -> dict[str, tuple[str, ...]]:
        outgoing: dict[str, list[EvidenceEdge]] = {}
        incoming: dict[str, list[EvidenceEdge]] = {}
        for edge in edges:
            outgoing.setdefault(edge.source, []).append(edge)
            incoming.setdefault(edge.target, []).append(edge)

        impacted: set[str] = set(interventions)
        stack = list(interventions)
        while stack:
            parent = stack.pop()
            for edge in outgoing.get(parent, []):
                if edge.target not in impacted:
                    impacted.add(edge.target)
                    stack.append(edge.target)

        by_output: dict[str, tuple[str, ...]] = {}
        for output, weight in portfolio_exposures.items():
            if float(weight) == 0.0 or abs(node_delta[output]) <= 1e-12:
                by_output[output] = ()
                continue
            ancestors = {output}
            stack = [output]
            while stack:
                target = stack.pop()
                for edge in incoming.get(target, []):
                    if edge.source not in ancestors:
                        ancestors.add(edge.source)
                        stack.append(edge.source)
            evidence_ids = {
                edge.evidence_id for edge in edges
                if edge.source in impacted and edge.target in ancestors
                and edge.evidence_id.strip()
            }
            by_output[output] = tuple(sorted(evidence_ids))
        return by_output

    def run_counterfactual(self, *, source_values: Mapping[str, float],
                           interventions: Mapping[str, float],
                           portfolio_exposures: Mapping[str, float],
                           as_of: str, regime: str = "baseline",
                           uncertainty_samples: int = 0,
                           seed: int = 17) -> EPCRPResult:
        timestamp = _parse_timestamp(as_of)
        if not interventions:
            raise ValueError("at least one intervention is required")
        if not isinstance(regime, str) or not regime.strip():
            raise ValueError("regime must not be empty")
        if not isinstance(uncertainty_samples, int) or uncertainty_samples < 0:
            raise ValueError("uncertainty_samples must be a non-negative integer")
        if uncertainty_samples > 100_000:
            raise ValueError("uncertainty_samples must not exceed 100000")
        for label, mapping in (
            ("source_values", source_values),
            ("interventions", interventions),
            ("portfolio_exposures", portfolio_exposures),
        ):
            unknown = set(mapping) - set(self.nodes)
            if unknown:
                raise ValueError(f"unknown node(s) in {label}: {sorted(unknown)}")
            for name, value in mapping.items():
                _finite(value, f"{label}[{name}]")
        if not portfolio_exposures:
            raise ValueError("at least one portfolio exposure is required")

        accepted, rejected = self._accepted_edges(regime=regime, as_of=timestamp)
        order = self._topological_order(accepted)
        baseline = self._evaluate(overrides=source_values, edges=accepted, order=order)
        cf_overrides = dict(source_values)
        cf_overrides.update(interventions)
        counterfactual = self._evaluate(overrides=cf_overrides, edges=accepted, order=order)
        delta = {name: counterfactual[name] - baseline[name] for name in self.nodes}
        portfolio_delta = _finite(
            sum(float(weight) * delta[name] for name, weight in portfolio_exposures.items()),
            "portfolio_delta",
        )
        lineage = self._evidence_lineage(
            edges=accepted, interventions=interventions, node_delta=delta,
            portfolio_exposures=portfolio_exposures,
        )

        interval: Optional[tuple[float, float]] = None
        if uncertainty_samples:
            rng = random.Random(seed)
            samples: list[float] = []
            for _ in range(uncertainty_samples):
                sampled_edges = [
                    replace(edge, coefficient=(
                        rng.gauss(edge.coefficient, edge.coefficient_std)
                        if edge.coefficient_std > 0 else edge.coefficient
                    ))
                    for edge in accepted
                ]
                baseline_sample = self._evaluate(
                    overrides=source_values, edges=sampled_edges, order=order
                )
                counterfactual_sample = self._evaluate(
                    overrides=cf_overrides, edges=sampled_edges, order=order
                )
                samples.append(sum(
                    float(weight) * (
                        counterfactual_sample[name] - baseline_sample[name]
                    )
                    for name, weight in portfolio_exposures.items()
                ))
            samples.sort()
            lo, hi = int(0.05 * (len(samples) - 1)), int(0.95 * (len(samples) - 1))
            interval = (_finite(samples[lo], "uncertainty lower bound"),
                        _finite(samples[hi], "uncertainty upper bound"))

        graph_payload = {
            "nodes": [asdict(node) for node in sorted(
                self.nodes.values(), key=lambda item: item.name
            )],
            "edges": [asdict(edge) for edge in sorted(
                self.edges, key=lambda item: (item.source, item.target, item.evidence_id)
            )],
        }
        input_payload = {
            "source_values": dict(sorted(source_values.items())),
            "interventions": dict(sorted(interventions.items())),
            "portfolio_exposures": dict(sorted(portfolio_exposures.items())),
            "as_of": timestamp.isoformat(), "regime": regime,
            "min_support": self.min_support,
            "uncertainty_samples": uncertainty_samples,
            "seed": seed if uncertainty_samples else None,
        }
        manifest = {
            "method_version": METHOD_VERSION,
            "model_version": self.model_version,
            "as_of": timestamp.isoformat().replace("+00:00", "Z"),
            "regime": regime,
            "min_support": self.min_support,
            "graph_sha256": _digest(graph_payload),
            "inputs_sha256": _digest(input_payload),
            "accepted_edge_keys": sorted(edge.key for edge in accepted),
            "rejected_edges": dict(sorted(rejected.items())),
            "uncertainty_samples": uncertainty_samples,
            "seed": seed if uncertainty_samples else None,
            "warning": (
                "Research prototype only: causal identification, coefficient calibration, "
                "and portfolio exposure units are caller responsibilities."
            ),
        }
        return EPCRPResult(
            baseline=baseline, counterfactual=counterfactual, node_delta=delta,
            portfolio_delta=portfolio_delta,
            accepted_edge_keys=tuple(sorted(edge.key for edge in accepted)),
            rejected_edges=dict(sorted(rejected.items())),
            evidence_by_output=lineage, uncertainty_interval=interval,
            uncertainty_samples=uncertainty_samples, manifest=manifest,
        )
