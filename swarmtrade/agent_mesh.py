"""Persistent, provenance-aware evidence exchange for the SwarmTrade agent hierarchy.

This module coordinates research outputs only. It does not create trade orders or
convert agent opinions into execution authorization.
"""
from __future__ import annotations

import json
import os
import sqlite3
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DB = ROOT / "data" / "swarmtrade" / "agent_evidence.sqlite3"
AGENT_ROLES = frozenset({
    "data_quality", "news", "macro", "fundamentals", "technical",
    "liquidity", "volatility", "derivatives", "strategy", "adversarial",
    "portfolio", "risk", "execution_review",
})
ASSET_CLASSES = frozenset({"equity", "option", "future", "crypto", "forex"})
MAX_EVIDENCE_PER_RUN = 300
MAX_TEXT_LENGTH = 4000


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _text(value: Any, name: str, limit: int = 256, *, required: bool = True) -> str:
    if not isinstance(value, str):
        raise ValueError(f"{name} must be a string")
    value = value.strip()
    if required and not value:
        raise ValueError(f"{name} must not be empty")
    if len(value) > limit:
        raise ValueError(f"{name} exceeds {limit} characters")
    return value


def _timestamp(value: Any, name: str) -> str:
    if not isinstance(value, str):
        raise ValueError(f"{name} must be an ISO-8601 timestamp")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError(f"{name} must be an ISO-8601 timestamp") from exc
    if parsed.tzinfo is None:
        raise ValueError(f"{name} must include a timezone")
    if parsed.timestamp() > datetime.now(timezone.utc).timestamp() + 60:
        raise ValueError(f"{name} cannot be more than 60 seconds in the future")
    return parsed.astimezone(timezone.utc).isoformat()


class AgentEvidenceStore:
    """SQLite-backed run/evidence store with uniqueness and bounded payloads."""

    def __init__(self, db_path: str | Path | None = None) -> None:
        configured = os.getenv("FINAI_SWARMTRADE_EVIDENCE_DB", "").strip()
        self.db_path = Path(db_path or configured or DEFAULT_DB)

    def _connect(self) -> sqlite3.Connection:
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(str(self.db_path), timeout=10.0, isolation_level=None)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA busy_timeout = 10000")
        conn.execute("PRAGMA journal_mode = WAL")
        return conn

    def initialize(self) -> None:
        with closing(self._connect()) as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS agent_runs (
                    run_id TEXT PRIMARY KEY,
                    symbol TEXT NOT NULL,
                    asset_class TEXT NOT NULL,
                    venue TEXT NOT NULL,
                    timeframe TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS agent_evidence (
                    evidence_id TEXT PRIMARY KEY,
                    run_id TEXT NOT NULL REFERENCES agent_runs(run_id),
                    agent_id TEXT NOT NULL,
                    role TEXT NOT NULL,
                    agent_version TEXT NOT NULL,
                    instrument TEXT NOT NULL,
                    claim TEXT NOT NULL,
                    source_ids_json TEXT NOT NULL,
                    source_timestamp TEXT NOT NULL,
                    observed_at TEXT NOT NULL,
                    confidence REAL NOT NULL CHECK(confidence >= 0 AND confidence <= 1),
                    stance TEXT NOT NULL CHECK(stance IN ('bullish','bearish','neutral','abstain')),
                    invalidation TEXT NOT NULL,
                    missing_data_json TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    UNIQUE(run_id, evidence_id)
                );
                CREATE INDEX IF NOT EXISTS ix_agent_evidence_run_role
                    ON agent_evidence(run_id, role);
            """)

    def create_run(self, request: Mapping[str, Any]) -> dict[str, Any]:
        symbol = _text(request.get("symbol"), "symbol", 64).upper()
        asset_class = _text(request.get("asset_class"), "asset_class", 20).lower()
        if asset_class not in ASSET_CLASSES:
            raise ValueError("asset_class must be equity, option, future, crypto, or forex")
        venue = _text(request.get("venue", "UNKNOWN"), "venue", 64).upper()
        timeframe = _text(request.get("timeframe", "1d"), "timeframe", 32)
        run_id = str(uuid4())
        created_at = _now()
        self.initialize()
        with self._connect() as conn:
            conn.execute(
                "INSERT INTO agent_runs VALUES (?, ?, ?, ?, ?, ?)",
                (run_id, symbol, asset_class, venue, timeframe, created_at),
            )
        return {"run_id": run_id, "symbol": symbol, "asset_class": asset_class,
                "venue": venue, "timeframe": timeframe, "created_at": created_at,
                "mode": "research_only", "order_submission_enabled": False}

    def add_evidence(self, run_id: str, request: Mapping[str, Any]) -> dict[str, Any]:
        evidence_id = _text(request.get("evidence_id", str(uuid4())), "evidence_id", 128)
        agent_id = _text(request.get("agent_id"), "agent_id", 128)
        role = _text(request.get("role"), "role", 64)
        if role not in AGENT_ROLES:
            raise ValueError("role is not a supported agent role")
        agent_version = _text(request.get("agent_version"), "agent_version", 128)
        instrument = _text(request.get("instrument"), "instrument", 128).upper()
        claim = _text(request.get("claim"), "claim", MAX_TEXT_LENGTH)
        source_ids = request.get("source_ids")
        if not isinstance(source_ids, list) or not source_ids or len(source_ids) > 20:
            raise ValueError("source_ids must be a non-empty list of at most 20 source IDs")
        source_ids = [_text(item, "source_id", 256) for item in source_ids]
        source_timestamp = _timestamp(request.get("source_timestamp"), "source_timestamp")
        observed_at = _timestamp(request.get("observed_at"), "observed_at")
        confidence = request.get("confidence")
        if isinstance(confidence, bool) or not isinstance(confidence, (int, float)) or not 0 <= confidence <= 1:
            raise ValueError("confidence must be a number between 0 and 1")
        stance = _text(request.get("stance"), "stance", 16).lower()
        if stance not in {"bullish", "bearish", "neutral", "abstain"}:
            raise ValueError("stance must be bullish, bearish, neutral, or abstain")
        invalidation = _text(request.get("invalidation", ""), "invalidation", 1000, required=False)
        missing = request.get("missing_data", [])
        if not isinstance(missing, list) or len(missing) > 30:
            raise ValueError("missing_data must be a list of at most 30 items")
        missing = [_text(item, "missing_data item", 256) for item in missing]
        self.initialize()
        with self._connect() as conn:
            conn.execute("BEGIN IMMEDIATE")
            try:
                run = conn.execute("SELECT symbol FROM agent_runs WHERE run_id = ?", (run_id,)).fetchone()
                if run is None:
                    raise KeyError("Agent run not found")
                count = conn.execute("SELECT COUNT(*) AS n FROM agent_evidence WHERE run_id = ?", (run_id,)).fetchone()["n"]
                if count >= MAX_EVIDENCE_PER_RUN:
                    raise ValueError(f"Evidence limit of {MAX_EVIDENCE_PER_RUN} per run reached")
                conn.execute(
                    """INSERT INTO agent_evidence
                    (evidence_id, run_id, agent_id, role, agent_version, instrument, claim,
                     source_ids_json, source_timestamp, observed_at, confidence, stance,
                     invalidation, missing_data_json, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (evidence_id, run_id, agent_id, role, agent_version, instrument, claim,
                     json.dumps(source_ids), source_timestamp, observed_at, float(confidence),
                     stance, invalidation, json.dumps(missing), _now()),
                )
                conn.commit()
            except Exception:
                conn.rollback()
                raise
        return {"accepted": True, "evidence_id": evidence_id, "run_id": run_id,
                "role": role, "stance": stance, "confidence": float(confidence),
                "execution_authority": False}

    def summary(self, run_id: str) -> dict[str, Any]:
        self.initialize()
        with self._connect() as conn:
            run = conn.execute("SELECT * FROM agent_runs WHERE run_id = ?", (run_id,)).fetchone()
            if run is None:
                raise KeyError("Agent run not found")
            rows = conn.execute(
                "SELECT role, stance, confidence, source_timestamp, observed_at, claim, source_ids_json, missing_data_json "
                "FROM agent_evidence WHERE run_id = ? ORDER BY created_at, evidence_id", (run_id,)
            ).fetchall()
        stance_counts = {key: 0 for key in ("bullish", "bearish", "neutral", "abstain")}
        roles: set[str] = set()
        stale_count = 0
        now = datetime.now(timezone.utc).timestamp()
        evidence = []
        for row in rows:
            stance_counts[row["stance"]] += 1
            roles.add(row["role"])
            source_time = datetime.fromisoformat(row["source_timestamp"]).timestamp()
            age_seconds = max(0.0, now - source_time)
            stale = age_seconds > 900
            stale_count += int(stale)
            evidence.append({
                "role": row["role"], "stance": row["stance"], "confidence": row["confidence"],
                "claim": row["claim"], "source_ids": json.loads(row["source_ids_json"]),
                "source_timestamp": row["source_timestamp"], "age_seconds": round(age_seconds, 2),
                "stale": stale, "missing_data": json.loads(row["missing_data_json"]),
            })
        return {
            "run": dict(run), "evidence_count": len(evidence), "distinct_roles": sorted(roles),
            "stance_counts": stance_counts, "stale_evidence_count": stale_count,
            "evidence": evidence,
            "interpretation": "Research evidence only; counts are not calibrated probabilities or a trade signal.",
            "order_submission_enabled": False,
        }
