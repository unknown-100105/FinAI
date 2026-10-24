"""SQLite-backed paper ledger for explicit simulation-only SwarmTrade positions."""
from __future__ import annotations

import hashlib
import json
import math
import os
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping
from uuid import uuid4


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DB_PATH = ROOT / "data" / "swarmtrade" / "paper_ledger.sqlite3"


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def utc_timestamp() -> float:
    return utc_now().timestamp()


def utc_day_start_timestamp() -> float:
    now = utc_now()
    return datetime(now.year, now.month, now.day, tzinfo=timezone.utc).timestamp()


def payload_digest(payload: Mapping[str, Any]) -> str:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), allow_nan=False)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _finite_positive(value: Any, name: str) -> float:
    if isinstance(value, bool):
        raise ValueError(f"{name} must be a finite positive number")
    try:
        number = float(value)
    except (TypeError, ValueError, OverflowError) as exc:
        raise ValueError(f"{name} must be a finite positive number") from exc
    if not math.isfinite(number) or number <= 0:
        raise ValueError(f"{name} must be a finite positive number")
    return number


class PaperLedger:
    """File-backed ledger; every mutation uses a serialized SQLite transaction."""

    def __init__(self, db_path: str | Path | None = None) -> None:
        configured = os.getenv("FINAI_SWARMTRADE_PAPER_DB", "").strip()
        self.db_path = Path(db_path or configured or DEFAULT_DB_PATH)

    def _connect(self) -> sqlite3.Connection:
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        connection = sqlite3.connect(str(self.db_path), timeout=10.0, isolation_level=None)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute("PRAGMA busy_timeout = 10000")
        connection.execute("PRAGMA journal_mode = WAL")
        return connection

    @contextmanager
    def _connection(self):
        connection = self._connect()
        try:
            yield connection
        finally:
            connection.close()

    def initialize(self) -> None:
        with self._connection() as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS paper_accounts (
                    account_id TEXT PRIMARY KEY,
                    label TEXT NOT NULL,
                    currency TEXT NOT NULL,
                    initial_capital REAL NOT NULL CHECK(initial_capital > 0),
                    created_at REAL NOT NULL
                );
                CREATE TABLE IF NOT EXISTS paper_positions (
                    position_id TEXT PRIMARY KEY,
                    account_id TEXT NOT NULL REFERENCES paper_accounts(account_id),
                    symbol TEXT NOT NULL,
                    asset_class TEXT NOT NULL,
                    direction TEXT NOT NULL CHECK(direction IN ('long','short')),
                    quantity REAL NOT NULL CHECK(quantity > 0),
                    entry_price REAL NOT NULL CHECK(entry_price > 0),
                    stop_price REAL NOT NULL CHECK(stop_price > 0),
                    target_price REAL NOT NULL CHECK(target_price > 0),
                    multiplier REAL NOT NULL CHECK(multiplier > 0),
                    risk_per_unit REAL NOT NULL CHECK(risk_per_unit > 0),
                    estimated_risk REAL NOT NULL CHECK(estimated_risk > 0),
                    fee_bps REAL NOT NULL CHECK(fee_bps >= 0),
                    slippage_bps REAL NOT NULL CHECK(slippage_bps >= 0),
                    risk_metadata TEXT NOT NULL,
                    status TEXT NOT NULL CHECK(status IN ('OPEN','CLOSED')),
                    opened_at REAL NOT NULL,
                    closed_at REAL,
                    exit_price REAL,
                    gross_pnl REAL,
                    estimated_costs REAL,
                    net_pnl REAL,
                    close_reason TEXT
                );
                CREATE INDEX IF NOT EXISTS ix_paper_positions_account_status
                    ON paper_positions(account_id, status);
                CREATE INDEX IF NOT EXISTS ix_paper_positions_account_closed
                    ON paper_positions(account_id, closed_at);
                CREATE TABLE IF NOT EXISTS paper_events (
                    event_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    account_id TEXT NOT NULL REFERENCES paper_accounts(account_id),
                    idempotency_key TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    payload_digest TEXT NOT NULL,
                    response_json TEXT NOT NULL,
                    created_at REAL NOT NULL,
                    UNIQUE(account_id, idempotency_key)
                );
                """
            )

    def _require_account(self, connection: sqlite3.Connection, account_id: str) -> sqlite3.Row:
        row = connection.execute(
            "SELECT * FROM paper_accounts WHERE account_id = ?", (account_id,)
        ).fetchone()
        if row is None:
            raise KeyError("Paper account not found")
        return row

    def _account_snapshot(self, connection: sqlite3.Connection, account_id: str) -> dict[str, Any]:
        account = self._require_account(connection, account_id)
        total_realized = connection.execute(
            "SELECT COALESCE(SUM(net_pnl), 0) AS pnl FROM paper_positions WHERE account_id = ? AND status = 'CLOSED'",
            (account_id,),
        ).fetchone()["pnl"]
        open_rows = connection.execute(
            "SELECT position_id, symbol, asset_class, direction, quantity, entry_price, stop_price, "
            "target_price, estimated_risk, opened_at FROM paper_positions "
            "WHERE account_id = ? AND status = 'OPEN' ORDER BY opened_at, position_id",
            (account_id,),
        ).fetchall()
        now = utc_timestamp()
        day_start = utc_day_start_timestamp()
        previous_realized = connection.execute(
            "SELECT COALESCE(SUM(net_pnl), 0) AS pnl FROM paper_positions "
            "WHERE account_id = ? AND status = 'CLOSED' AND closed_at < ?",
            (account_id, day_start),
        ).fetchone()["pnl"]
        today_realized = connection.execute(
            "SELECT COALESCE(SUM(net_pnl), 0) AS pnl FROM paper_positions "
            "WHERE account_id = ? AND status = 'CLOSED' AND closed_at >= ? AND closed_at <= ?",
            (account_id, day_start, now),
        ).fetchone()["pnl"]
        equity = float(account["initial_capital"]) + float(total_realized)
        daily_starting_equity = max(1e-9, float(account["initial_capital"]) + float(previous_realized))
        daily_loss_pct = max(0.0, -float(today_realized) / daily_starting_equity * 100.0)
        open_risk = sum(float(row["estimated_risk"]) for row in open_rows)
        open_risk_pct = open_risk / max(equity, 1e-9) * 100.0
        return {
            "account_id": account_id,
            "label": account["label"],
            "currency": account["currency"],
            "initial_capital": float(account["initial_capital"]),
            "realized_pnl": float(total_realized),
            "equity_excluding_unrealized_pnl": equity,
            "daily_realized_pnl": float(today_realized),
            "daily_realized_loss_pct": daily_loss_pct,
            "open_position_risk": open_risk,
            "open_position_risk_pct": open_risk_pct,
            "open_positions": [dict(row) for row in open_rows],
            "open_position_count": len(open_rows),
            "created_at": float(account["created_at"]),
            "paper_only": True,
            "unrealized_pnl_included": False,
        }

    def create_account(self, *, label: str, currency: str, initial_capital: float) -> dict[str, Any]:
        label = str(label).strip()
        currency = str(currency).strip().upper()
        if not label or len(label) > 100:
            raise ValueError("label must be between 1 and 100 characters")
        if len(currency) != 3 or not currency.isalpha():
            raise ValueError("currency must be a three-letter ISO currency code")
        capital = _finite_positive(initial_capital, "initial_capital")
        account_id = str(uuid4())
        created_at = utc_timestamp()
        self.initialize()
        with self._connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            connection.execute(
                "INSERT INTO paper_accounts(account_id, label, currency, initial_capital, created_at) "
                "VALUES(?,?,?,?,?)",
                (account_id, label, currency, capital, created_at),
            )
            connection.commit()
            return self._account_snapshot(connection, account_id)

    def get_account(self, account_id: str) -> dict[str, Any]:
        self.initialize()
        with self._connect() as connection:
            return self._account_snapshot(connection, account_id)

    @staticmethod
    def _event_replay(
        connection: sqlite3.Connection,
        account_id: str,
        idempotency_key: str,
        event_type: str,
        request_digest: str,
    ) -> dict[str, Any] | None:
        row = connection.execute(
            "SELECT event_type, payload_digest, response_json FROM paper_events "
            "WHERE account_id = ? AND idempotency_key = ?",
            (account_id, idempotency_key),
        ).fetchone()
        if row is None:
            return None
        if row["event_type"] != event_type or row["payload_digest"] != request_digest:
            raise ValueError("Idempotency key was already used with a different operation or payload")
        response = json.loads(row["response_json"])
        response["idempotent_replay"] = True
        return response

    def replay_if_exists(
        self, *, account_id: str, idempotency_key: str, event_type: str, request_digest: str
    ) -> dict[str, Any] | None:
        if not idempotency_key.strip() or len(idempotency_key) > 160:
            raise ValueError("idempotency_key must be between 1 and 160 characters")
        self.initialize()
        with self._connection() as connection:
            self._require_account(connection, account_id)
            return self._event_replay(connection, account_id, idempotency_key, event_type, request_digest)

    @staticmethod
    def _save_event(
        connection: sqlite3.Connection,
        account_id: str,
        idempotency_key: str,
        event_type: str,
        request_digest: str,
        response: Mapping[str, Any],
    ) -> None:
        connection.execute(
            "INSERT INTO paper_events(account_id, idempotency_key, event_type, payload_digest, response_json, created_at) "
            "VALUES(?,?,?,?,?,?)",
            (account_id, idempotency_key, event_type, request_digest,
             json.dumps(response, sort_keys=True, allow_nan=False), utc_timestamp()),
        )

    def open_position(
        self, *, account_id: str, idempotency_key: str, plan: Mapping[str, Any],
        request_digest: str,
    ) -> dict[str, Any]:
        if not idempotency_key.strip() or len(idempotency_key) > 160:
            raise ValueError("idempotency_key must be between 1 and 160 characters")
        if plan.get("status") != "APPROVED_FOR_SIMULATION":
            raise ValueError("only a risk-approved SwarmTrade simulation plan can be opened")
        sizing = plan["sizing"]
        risk = plan["risk"]
        symbol = str(plan["symbol"])
        asset_class = str(plan["asset_class"])
        direction = str(plan["direction"])
        if direction not in {"long", "short"}:
            raise ValueError("plan direction must be long or short")
        position_id = str(uuid4())
        risk_metadata = {
            "asset_class": asset_class,
            "multiplier": sizing["multiplier"],
            "risk_model": risk.get("risk_model", {}),
        }
        self.initialize()
        with self._connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            try:
                self._require_account(connection, account_id)
                replay = self._event_replay(connection, account_id, idempotency_key, "open", request_digest)
                if replay is not None:
                    connection.commit()
                    return replay
                snapshot = self._account_snapshot(connection, account_id)
                equity = max(float(snapshot["equity_excluding_unrealized_pnl"]), 1e-9)
                if snapshot["daily_realized_loss_pct"] >= float(risk["daily_loss_limit_pct"]):
                    raise ValueError("paper account daily realized-loss gate is active")
                if float(risk["estimated_total_risk"]) > equity * 0.01 + 1e-8:
                    raise ValueError("paper account single-position risk would exceed 1% of current equity")
                combined_risk = float(snapshot["open_position_risk"]) + float(risk["estimated_total_risk"])
                combined_pct = combined_risk / equity * 100.0
                if combined_pct > 3.0 + 1e-8:
                    raise ValueError("paper account aggregate open-position risk would exceed 3% of equity")
                connection.execute(
                    "INSERT INTO paper_positions(position_id,account_id,symbol,asset_class,direction,quantity,"
                    "entry_price,stop_price,target_price,multiplier,risk_per_unit,estimated_risk,fee_bps,slippage_bps,"
                    "risk_metadata,status,opened_at) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                    (
                        position_id, account_id, symbol, asset_class, direction,
                        float(sizing["quantity"]), float(sizing["entry_price"]),
                        float(sizing["stop_price"]), float(sizing["target_price"]),
                        float(sizing["multiplier"]),
                        float(risk["risk_per_unit_including_estimated_costs"]),
                        float(risk["estimated_total_risk"]),
                        float(risk["fee_bps_per_side_assumption"]),
                        float(risk["slippage_bps_per_side_assumption"]),
                        json.dumps(risk_metadata, sort_keys=True),
                        "OPEN", utc_timestamp(),
                    ),
                )
                response = {
                    "status": "PAPER_POSITION_OPEN",
                    "account_id": account_id,
                    "position_id": position_id,
                    "symbol": symbol,
                    "asset_class": asset_class,
                    "direction": direction,
                    "quantity": float(sizing["quantity"]),
                    "entry_price": float(sizing["entry_price"]),
                    "stop_price": float(sizing["stop_price"]),
                    "target_price": float(sizing["target_price"]),
                    "estimated_risk": float(risk["estimated_total_risk"]),
                    "execution": {
                        "mode": "paper_ledger",
                        "real_order_submitted": False,
                        "live_fill_claimed": False,
                        "simulated_entry_recorded": True,
                    },
                    "idempotent_replay": False,
                }
                self._save_event(connection, account_id, idempotency_key, "open", request_digest, response)
                connection.commit()
                return response
            except Exception:
                connection.rollback()
                raise

    def close_position(
        self, *, account_id: str, position_id: str, exit_price: float,
        idempotency_key: str, close_reason: str, request_digest: str,
    ) -> dict[str, Any]:
        exit_price = _finite_positive(exit_price, "exit_price")
        if not idempotency_key.strip() or len(idempotency_key) > 160:
            raise ValueError("idempotency_key must be between 1 and 160 characters")
        if close_reason not in {"manual", "stop", "target", "risk_control"}:
            raise ValueError("close_reason must be manual, stop, target, or risk_control")
        self.initialize()
        with self._connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            try:
                self._require_account(connection, account_id)
                replay = self._event_replay(connection, account_id, idempotency_key, "close", request_digest)
                if replay is not None:
                    connection.commit()
                    return replay
                row = connection.execute(
                    "SELECT * FROM paper_positions WHERE account_id=? AND position_id=?",
                    (account_id, position_id),
                ).fetchone()
                if row is None:
                    raise KeyError("Paper position not found")
                if row["status"] != "OPEN":
                    raise ValueError("paper position is already closed")
                metadata = json.loads(row["risk_metadata"])
                asset_class = str(row["asset_class"])
                direction_sign = 1.0 if row["direction"] == "long" else -1.0
                entry_price = float(row["entry_price"])
                quantity = float(row["quantity"])
                multiplier = float(row["multiplier"])
                risk_model = metadata.get("risk_model", {})
                if asset_class in {"future"}:
                    tick_size = _finite_positive(risk_model.get("tick_size"), "tick_size")
                    tick_value = _finite_positive(risk_model.get("tick_value"), "tick_value")
                    gross_pnl = direction_sign * ((exit_price - entry_price) / tick_size) * tick_value * quantity
                elif asset_class == "forex":
                    pip_size = _finite_positive(risk_model.get("pip_size"), "pip_size")
                    pip_value = _finite_positive(risk_model.get("pip_value_per_unit"), "pip_value_per_unit")
                    gross_pnl = direction_sign * ((exit_price - entry_price) / pip_size) * pip_value * quantity
                else:
                    gross_pnl = direction_sign * (exit_price - entry_price) * multiplier * quantity
                fee_bps = float(row["fee_bps"])
                slippage_bps = float(row["slippage_bps"])
                estimated_costs = (
                    entry_price * multiplier * quantity
                    + exit_price * multiplier * quantity
                ) * (fee_bps + slippage_bps) / 10_000.0
                net_pnl = gross_pnl - estimated_costs
                closed_at = utc_timestamp()
                connection.execute(
                    "UPDATE paper_positions SET status='CLOSED', closed_at=?, exit_price=?, gross_pnl=?, "
                    "estimated_costs=?, net_pnl=?, close_reason=? WHERE account_id=? AND position_id=? AND status='OPEN'",
                    (closed_at, exit_price, gross_pnl, estimated_costs, net_pnl,
                     close_reason, account_id, position_id),
                )
                response = {
                    "status": "PAPER_POSITION_CLOSED",
                    "account_id": account_id,
                    "position_id": position_id,
                    "symbol": row["symbol"],
                    "direction": row["direction"],
                    "quantity": quantity,
                    "entry_price": entry_price,
                    "exit_price": exit_price,
                    "gross_pnl": round(gross_pnl, 8),
                    "estimated_costs": round(estimated_costs, 8),
                    "net_pnl": round(net_pnl, 8),
                    "close_reason": close_reason,
                    "closed_at": closed_at,
                    "execution": {
                        "mode": "paper_ledger",
                        "real_order_submitted": False,
                        "live_fill_claimed": False,
                        "simulated_close_recorded": True,
                    },
                    "idempotent_replay": False,
                }
                self._save_event(connection, account_id, idempotency_key, "close", request_digest, response)
                connection.commit()
                return response
            except Exception:
                connection.rollback()
                raise
