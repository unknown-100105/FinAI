"""Local-first payment intent journal and settlement adapter contract.

This is an integration seam, not a bank connector or production wallet. It never
stores account credentials, transfers funds, or contacts a ledger by itself.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from enum import Enum
import hashlib
import json
import re
import sqlite3
from threading import RLock
from typing import Any, Mapping, Protocol


class PaymentError(Exception):
    """Base class for local payment-intent errors."""


class IdempotencyConflict(PaymentError):
    """An idempotency key was reused with a different instruction."""


class InvalidPaymentTransition(PaymentError):
    """A payment intent attempted an unsupported state transition."""


class SettlementOutcomeUnknown(PaymentError):
    """An adapter failed after submission may have reached its destination."""


class PaymentState(str, Enum):
    PREPARED = "PREPARED"
    SUBMITTED = "SUBMITTED"
    SETTLED = "SETTLED"
    RECONCILIATION_REQUIRED = "RECONCILIATION_REQUIRED"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _hash(value: object) -> str:
    data = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(data.encode("utf-8")).hexdigest()


def _required_text(value: str, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must be a non-empty string")
    return value.strip()


@dataclass(frozen=True)
class PaymentIntent:
    payment_id: str
    idempotency_key: str
    payer_ref: str
    payee_ref: str
    amount_minor: int
    currency: str
    request_hash: str
    state: PaymentState
    external_reference: str | None
    settlement_mode: str | None
    created_at: str
    updated_at: str

    @classmethod
    def from_row(cls, row: sqlite3.Row) -> "PaymentIntent":
        return cls(
            payment_id=row["payment_id"], idempotency_key=row["idempotency_key"],
            payer_ref=row["payer_ref"], payee_ref=row["payee_ref"],
            amount_minor=row["amount_minor"], currency=row["currency"],
            request_hash=row["request_hash"], state=PaymentState(row["state"]),
            external_reference=row["external_reference"],
            settlement_mode=row["settlement_mode"], created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["state"] = self.state.value
        return data


@dataclass(frozen=True)
class SettlementReceipt:
    external_reference: str
    sandbox: bool


class SettlementAdapter(Protocol):
    """Configured adapter boundary; implementations must be idempotent."""

    def submit(self, intent: PaymentIntent) -> SettlementReceipt:
        """Submit once and return the destination's settlement reference."""


class LocalSimulationAdapter:
    """Deterministic simulator. It does not move funds or call a remote service."""

    def submit(self, intent: PaymentIntent) -> SettlementReceipt:
        suffix = _hash({
            "payment_id": intent.payment_id,
            "request_hash": intent.request_hash,
            "idempotency_key": intent.idempotency_key,
        })[:20].upper()
        return SettlementReceipt("SIM-" + suffix, sandbox=True)


class PaymentLedger:
    """SQLite-backed state machine and append-only, hash-chained event journal.

    amount_minor is an integer in minor currency units (INR paise, for example).
    No balance accounting or cross-device offline double-spend prevention is done.
    """

    def __init__(self, database_path: str = ":memory:") -> None:
        self._lock = RLock()
        self._conn = sqlite3.connect(
            database_path, isolation_level=None, timeout=5.0, check_same_thread=False
        )
        self._conn.row_factory = sqlite3.Row
        self._conn.execute("PRAGMA foreign_keys = ON")
        self._conn.execute("PRAGMA busy_timeout = 5000")
        self._conn.executescript("""
            CREATE TABLE IF NOT EXISTS payment_intents (
                payment_id TEXT PRIMARY KEY,
                idempotency_key TEXT NOT NULL UNIQUE,
                payer_ref TEXT NOT NULL,
                payee_ref TEXT NOT NULL,
                amount_minor INTEGER NOT NULL CHECK(amount_minor > 0),
                currency TEXT NOT NULL,
                request_hash TEXT NOT NULL,
                state TEXT NOT NULL,
                external_reference TEXT,
                settlement_mode TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS payment_journal (
                sequence INTEGER PRIMARY KEY AUTOINCREMENT,
                payment_id TEXT NOT NULL REFERENCES payment_intents(payment_id),
                event_type TEXT NOT NULL,
                payload_json TEXT NOT NULL,
                created_at TEXT NOT NULL,
                previous_hash TEXT NOT NULL,
                event_hash TEXT NOT NULL UNIQUE
            );
        """)

    def close(self) -> None:
        with self._lock:
            self._conn.close()

    def __enter__(self) -> "PaymentLedger":
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

    def _payment(self, payment_id: str) -> PaymentIntent:
        row = self._conn.execute(
            "SELECT * FROM payment_intents WHERE payment_id = ?", (payment_id,)
        ).fetchone()
        if row is None:
            raise KeyError(f"unknown payment_id: {payment_id}")
        return PaymentIntent.from_row(row)

    def get_payment(self, payment_id: str) -> PaymentIntent:
        with self._lock:
            return self._payment(_required_text(payment_id, "payment_id"))

    def get_by_idempotency_key(self, idempotency_key: str) -> PaymentIntent | None:
        key = _required_text(idempotency_key, "idempotency_key")
        with self._lock:
            row = self._conn.execute(
                "SELECT * FROM payment_intents WHERE idempotency_key = ?", (key,)
            ).fetchone()
            return PaymentIntent.from_row(row) if row else None

    def _append_event(self, payment_id: str, event_type: str,
                      payload: Mapping[str, Any]) -> None:
        row = self._conn.execute(
            "SELECT event_hash FROM payment_journal ORDER BY sequence DESC LIMIT 1"
        ).fetchone()
        previous_hash = row["event_hash"] if row else ""
        created_at = _now()
        payload_json = json.dumps(
            dict(payload), sort_keys=True, separators=(",", ":"), ensure_ascii=True
        )
        material = {
            "payment_id": payment_id, "event_type": event_type,
            "payload_json": payload_json, "created_at": created_at,
            "previous_hash": previous_hash,
        }
        self._conn.execute(
            """INSERT INTO payment_journal
               (payment_id,event_type,payload_json,created_at,previous_hash,event_hash)
               VALUES (?,?,?,?,?,?)""",
            (payment_id, event_type, payload_json, created_at,
             previous_hash, _hash(material)),
        )

    def prepare_payment(self, *, idempotency_key: str, payer_ref: str,
                        payee_ref: str, amount_minor: int,
                        currency: str = "INR") -> tuple[PaymentIntent, bool]:
        key = _required_text(idempotency_key, "idempotency_key")
        payer = _required_text(payer_ref, "payer_ref")
        payee = _required_text(payee_ref, "payee_ref")
        if payer == payee:
            raise ValueError("payer_ref and payee_ref must be different")
        if isinstance(amount_minor, bool) or not isinstance(amount_minor, int) or amount_minor <= 0:
            raise ValueError("amount_minor must be a positive integer")
        curr = _required_text(currency, "currency").upper()
        if not re.fullmatch(r"[A-Z]{3}", curr):
            raise ValueError("currency must be a three-letter ISO-style code")
        payload = {
            "payer_ref": payer, "payee_ref": payee,
            "amount_minor": amount_minor, "currency": curr,
        }
        request_hash = _hash(payload)
        with self._lock:
            self._conn.execute("BEGIN IMMEDIATE")
            try:
                existing = self._conn.execute(
                    "SELECT * FROM payment_intents WHERE idempotency_key = ?", (key,)
                ).fetchone()
                if existing:
                    record = PaymentIntent.from_row(existing)
                    if record.request_hash != request_hash:
                        raise IdempotencyConflict(
                            "idempotency_key was already used for a different instruction"
                        )
                    self._conn.execute("COMMIT")
                    return record, False

                payment_id = "pay_" + _hash({
                    "idempotency_key": key, "request_hash": request_hash
                })[:32]
                now = _now()
                self._conn.execute(
                    """INSERT INTO payment_intents
                       (payment_id,idempotency_key,payer_ref,payee_ref,amount_minor,
                        currency,request_hash,state,external_reference,settlement_mode,
                        created_at,updated_at)
                       VALUES (?,?,?,?,?,?,?, ?,NULL,NULL,?,?)""",
                    (payment_id,key,payer,payee,amount_minor,curr,request_hash,
                     PaymentState.PREPARED.value,now,now),
                )
                self._append_event(payment_id, "PAYMENT_PREPARED", {
                    **payload, "request_hash": request_hash,
                })
                record = self._payment(payment_id)
                self._conn.execute("COMMIT")
                return record, True
            except Exception:
                self._conn.execute("ROLLBACK")
                raise

    def mark_submitted(self, payment_id: str, *, external_reference: str,
                       sandbox: bool) -> PaymentIntent:
        reference = _required_text(external_reference, "external_reference")
        with self._lock:
            self._conn.execute("BEGIN IMMEDIATE")
            try:
                current = self._payment(_required_text(payment_id, "payment_id"))
                mode = "sandbox" if sandbox else "external"
                if current.state in {PaymentState.SUBMITTED, PaymentState.SETTLED}:
                    if current.external_reference == reference and current.settlement_mode == mode:
                        self._conn.execute("COMMIT")
                        return current
                    raise InvalidPaymentTransition("payment already has another submission reference")
                if current.state != PaymentState.PREPARED:
                    raise InvalidPaymentTransition(
                        f"cannot submit payment from state {current.state.value}"
                    )
                now = _now()
                self._conn.execute(
                    """UPDATE payment_intents SET state=?,external_reference=?,
                       settlement_mode=?,updated_at=? WHERE payment_id=?""",
                    (PaymentState.SUBMITTED.value,reference,mode,now,current.payment_id),
                )
                self._append_event(current.payment_id, "PAYMENT_SUBMITTED", {
                    "external_reference": reference, "settlement_mode": mode,
                })
                result = self._payment(current.payment_id)
                self._conn.execute("COMMIT")
                return result
            except Exception:
                self._conn.execute("ROLLBACK")
                raise

    def mark_settled(self, payment_id: str, *, external_reference: str) -> PaymentIntent:
        reference = _required_text(external_reference, "external_reference")
        with self._lock:
            self._conn.execute("BEGIN IMMEDIATE")
            try:
                current = self._payment(_required_text(payment_id, "payment_id"))
                if current.state == PaymentState.SETTLED:
                    if current.external_reference == reference:
                        self._conn.execute("COMMIT")
                        return current
                    raise InvalidPaymentTransition("settlement reference does not match")
                if current.state != PaymentState.SUBMITTED:
                    raise InvalidPaymentTransition(
                        f"cannot settle payment from state {current.state.value}"
                    )
                if current.external_reference != reference:
                    raise InvalidPaymentTransition("settlement reference does not match submission")
                now = _now()
                self._conn.execute(
                    "UPDATE payment_intents SET state=?,updated_at=? WHERE payment_id=?",
                    (PaymentState.SETTLED.value,now,current.payment_id),
                )
                self._append_event(current.payment_id, "PAYMENT_SETTLED", {
                    "external_reference": reference,
                    "settlement_mode": current.settlement_mode,
                })
                result = self._payment(current.payment_id)
                self._conn.execute("COMMIT")
                return result
            except Exception:
                self._conn.execute("ROLLBACK")
                raise

    def mark_reconciliation_required(self, payment_id: str, *, reason: str) -> PaymentIntent:
        why = _required_text(reason, "reason")
        with self._lock:
            self._conn.execute("BEGIN IMMEDIATE")
            try:
                current = self._payment(_required_text(payment_id, "payment_id"))
                if current.state == PaymentState.SETTLED:
                    raise InvalidPaymentTransition("settled payments cannot be silently downgraded")
                if current.state == PaymentState.RECONCILIATION_REQUIRED:
                    self._conn.execute("COMMIT")
                    return current
                now = _now()
                self._conn.execute(
                    "UPDATE payment_intents SET state=?,updated_at=? WHERE payment_id=?",
                    (PaymentState.RECONCILIATION_REQUIRED.value,now,current.payment_id),
                )
                self._append_event(current.payment_id, "RECONCILIATION_REQUIRED", {
                    "reason": why,
                })
                result = self._payment(current.payment_id)
                self._conn.execute("COMMIT")
                return result
            except Exception:
                self._conn.execute("ROLLBACK")
                raise

    def journal_events(self, payment_id: str | None = None) -> list[dict[str, Any]]:
        with self._lock:
            if payment_id is None:
                rows = self._conn.execute(
                    "SELECT * FROM payment_journal ORDER BY sequence"
                ).fetchall()
            else:
                rows = self._conn.execute(
                    "SELECT * FROM payment_journal WHERE payment_id=? ORDER BY sequence",
                    (_required_text(payment_id, "payment_id"),),
                ).fetchall()
            return [{
                "sequence": row["sequence"], "payment_id": row["payment_id"],
                "event_type": row["event_type"], "payload": json.loads(row["payload_json"]),
                "created_at": row["created_at"], "previous_hash": row["previous_hash"],
                "event_hash": row["event_hash"],
            } for row in rows]

    def verify_journal(self) -> tuple[bool, int | None]:
        """Verify the whole event hash chain; return (valid, failing sequence)."""
        with self._lock:
            rows = self._conn.execute(
                "SELECT * FROM payment_journal ORDER BY sequence"
            ).fetchall()
            expected_previous = ""
            for row in rows:
                if row["previous_hash"] != expected_previous:
                    return False, int(row["sequence"])
                material = {
                    "payment_id": row["payment_id"], "event_type": row["event_type"],
                    "payload_json": row["payload_json"], "created_at": row["created_at"],
                    "previous_hash": row["previous_hash"],
                }
                if _hash(material) != row["event_hash"]:
                    return False, int(row["sequence"])
                expected_previous = row["event_hash"]
            return True, None


class PaymentService:
    """Preparation and guarded adapter dispatch; real funds are not handled here."""

    def __init__(self, ledger: PaymentLedger) -> None:
        self.ledger = ledger

    def prepare(self, **kwargs: Any) -> tuple[PaymentIntent, bool]:
        return self.ledger.prepare_payment(**kwargs)

    def submit_prepared(self, payment_id: str, *, adapter: SettlementAdapter,
                        authenticated: bool, confirmed: bool) -> PaymentIntent:
        if not authenticated:
            raise PermissionError("authenticated user context is required before submission")
        if not confirmed:
            raise PermissionError("explicit payment confirmation is required before submission")
        intent = self.ledger.get_payment(payment_id)
        if intent.state in {PaymentState.SUBMITTED, PaymentState.SETTLED}:
            return intent
        if intent.state != PaymentState.PREPARED:
            raise InvalidPaymentTransition(
                f"cannot submit payment from state {intent.state.value}"
            )
        try:
            receipt = adapter.submit(intent)
            if not isinstance(receipt, SettlementReceipt):
                raise TypeError("settlement adapter returned an invalid receipt")
            reference = _required_text(receipt.external_reference, "external_reference")
        except Exception as exc:
            self.ledger.mark_reconciliation_required(
                payment_id, reason="submission result unknown; manual reconciliation required"
            )
            raise SettlementOutcomeUnknown(
                "adapter failed; intent moved to reconciliation and must not be retried blindly"
            ) from exc
        try:
            return self.ledger.mark_submitted(
                payment_id, external_reference=reference, sandbox=receipt.sandbox
            )
        except Exception as exc:
            # The destination may have accepted the intent even if local persistence
            # failed. Do not leave it apparently safe for an automatic retry.
            try:
                self.ledger.mark_reconciliation_required(
                    payment_id,
                    reason="adapter receipt obtained but local journal update failed",
                )
            except Exception:
                # Preserve the original persistence exception; operators must inspect
                # the journal and destination before retrying.
                pass
            raise SettlementOutcomeUnknown(
                "adapter returned a reference but local persistence failed; reconcile before retry"
            ) from exc
