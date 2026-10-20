"""Evidence gate for counterfactual financial stress testing.

The gate fails closed: each intervention and each causal edge on a path from an
intervened node to the portfolio outcome must be supported by sufficiently
recent, source-attributed evidence. Evidence records are inputs; this module
does not pretend that lexical matches prove causal identification.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Iterable, Mapping, Sequence

from causal_risk.schema import DEFAULT_EDGES, DEFAULT_NODES


def _parse_timestamp(value: Any) -> datetime:
    raw = str(value or "").strip()
    if not raw:
        raise ValueError("observed_at is required")
    if raw.endswith("Z"):
        raw = raw[:-1] + "+00:00"
    parsed = datetime.fromisoformat(raw)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def required_evidence_claims(
    interventions: Mapping[str, float],
    edges: Sequence[Any] | None = None,
    target_node: str = "portfolio",
) -> list[str]:
    """Return intervention and edge claims required to explain target impact."""
    nodes = {node.node_id for node in DEFAULT_NODES}
    if target_node not in nodes:
        raise ValueError(f"unknown target_node: {target_node}")
    unknown = sorted(set(interventions) - nodes)
    if unknown:
        raise ValueError(f"interventions reference unknown nodes: {unknown}")
    raw_edges = list(DEFAULT_EDGES if edges is None else edges)
    normalized = []
    for edge in raw_edges:
        if isinstance(edge, Mapping):
            source, target = str(edge["source"]), str(edge["target"])
        else:
            source, target = str(edge.source), str(edge.target)
        if source not in nodes or target not in nodes or source == target:
            raise ValueError(f"invalid causal edge: {source}->{target}")
        normalized.append((source, target))

    adjacency: dict[str, set[str]] = {node: set() for node in nodes}
    reverse: dict[str, set[str]] = {node: set() for node in nodes}
    for source, target in normalized:
        adjacency[source].add(target)
        reverse[target].add(source)

    ancestors = {target_node}
    queue = [target_node]
    while queue:
        current = queue.pop()
        for parent in reverse[current]:
            if parent not in ancestors:
                ancestors.add(parent)
                queue.append(parent)

    claims = {f"intervention:{name}" for name in interventions}
    for intervention in interventions:
        reachable = {intervention}
        queue = [intervention]
        while queue:
            current = queue.pop()
            for child in adjacency[current]:
                if child not in reachable:
                    reachable.add(child)
                    queue.append(child)
        for source, target in normalized:
            if source in reachable and target in ancestors:
                claims.add(f"edge:{source}->{target}")
    return sorted(claims)


def evaluate_evidence_gate(
    interventions: Mapping[str, float],
    evidence: Iterable[Mapping[str, Any]],
    *,
    as_of: str | datetime | None = None,
    minimum_confidence: float = 0.6,
    max_age_days: int = 180,
    edges: Sequence[Any] | None = None,
    target_node: str = "portfolio",
) -> dict[str, Any]:
    """Evaluate provenance, confidence, freshness and coverage for evidence."""
    if not 0.0 <= float(minimum_confidence) <= 1.0:
        raise ValueError("minimum_confidence must be between 0 and 1")
    if int(max_age_days) < 0:
        raise ValueError("max_age_days must be non-negative")
    if as_of is None:
        cutoff = datetime.now(timezone.utc)
    elif isinstance(as_of, datetime):
        cutoff = as_of if as_of.tzinfo else as_of.replace(tzinfo=timezone.utc)
        cutoff = cutoff.astimezone(timezone.utc)
    else:
        cutoff = _parse_timestamp(as_of)

    required = required_evidence_claims(
        interventions, edges=edges, target_node=target_node
    )
    support: dict[str, list[str]] = {claim: [] for claim in required}
    rejected_records: list[dict[str, str]] = []
    seen_ids: set[str] = set()
    valid_record_count = 0

    for index, record in enumerate(evidence or []):
        evidence_id = str(record.get("evidence_id", "")).strip()
        source = str(record.get("source", "")).strip()
        if not evidence_id or not source:
            rejected_records.append({
                "record": str(index),
                "reason": "missing evidence_id or source",
            })
            continue
        if evidence_id in seen_ids:
            rejected_records.append({
                "record": evidence_id,
                "reason": "duplicate evidence_id",
            })
            continue
        seen_ids.add(evidence_id)
        try:
            observed_at = _parse_timestamp(record.get("observed_at"))
            confidence = float(record.get("confidence"))
        except (TypeError, ValueError, OverflowError):
            rejected_records.append({
                "record": evidence_id,
                "reason": "invalid timestamp or confidence",
            })
            continue
        if not 0.0 <= confidence <= 1.0:
            rejected_records.append({
                "record": evidence_id,
                "reason": "confidence outside [0, 1]",
            })
            continue
        age_days = (cutoff - observed_at).total_seconds() / 86400.0
        if age_days < 0:
            rejected_records.append({
                "record": evidence_id,
                "reason": "evidence timestamp is in the future",
            })
            continue
        if age_days > int(max_age_days):
            rejected_records.append({
                "record": evidence_id,
                "reason": "evidence is stale",
            })
            continue
        if confidence < float(minimum_confidence):
            rejected_records.append({
                "record": evidence_id,
                "reason": "confidence below threshold",
            })
            continue
        valid_record_count += 1
        for claim in set(str(item).strip() for item in (record.get("supports") or [])):
            if claim in support:
                support[claim].append(evidence_id)

    missing = [claim for claim, ids in support.items() if not ids]
    return {
        "status": "EVIDENCE_GATE_PASSED" if not missing else "EVIDENCE_GATE_REJECTED",
        "passed": not missing,
        "target_node": target_node,
        "required_claims": required,
        "supported_claims": {
            claim: sorted(ids) for claim, ids in support.items() if ids
        },
        "missing_claims": missing,
        "valid_evidence_record_count": valid_record_count,
        "rejected_records": rejected_records,
        "policy": {
            "minimum_confidence": float(minimum_confidence),
            "max_age_days": int(max_age_days),
            "as_of": cutoff.isoformat(),
        },
        "limitation": (
            "Evidence coverage and freshness are checked mechanically; causal "
            "identification and source truthfulness still require independent review."
        ),
    }
