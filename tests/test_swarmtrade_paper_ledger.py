import pytest
from fastapi.testclient import TestClient

from app.main import app
from swarmtrade.paper_ledger import PaperLedger

client = TestClient(app)


def approved_plan_request(**overrides):
    payload = {
        "symbol": "TEST",
        "asset_class": "equity",
        "side": "auto",
        "entry_price": 100,
        "stop_price": 95,
        "target_price": 112,
        "capital": 100000,
        "risk_pct": 0.5,
        "fee_bps": 2,
        "slippage_bps": 2,
        "agent_count": 500,
        "signals": {"trend": 0.9, "momentum": 0.8, "breakout": 0.8, "sentiment": 0.7},
    }
    payload.update(overrides)
    return payload


def test_paper_ledger_is_disabled_by_default(monkeypatch):
    monkeypatch.delenv("FINAI_ENABLE_SWARMTRADE_PAPER_LEDGER", raising=False)
    assert client.get("/api/v1/swarmtrade/paper/status").json()["enabled"] is False
    response = client.post("/api/v1/swarmtrade/paper/accounts", json={"currency": "USD", "initial_capital": 10000})
    assert response.status_code == 503


def test_paper_ledger_is_disabled_in_production_even_when_feature_flag_is_enabled(monkeypatch, tmp_path):
    monkeypatch.setenv("FINAI_ENV", "production")
    monkeypatch.setenv("FINAI_API_AUTH_MODE", "bearer")
    monkeypatch.setenv("FINAI_API_BEARER_TOKEN", "test-production-token-with-at-least-32-chars")
    monkeypatch.setenv("FINAI_ENABLE_SWARMTRADE_PAPER_LEDGER", "1")
    monkeypatch.setenv("FINAI_SWARMTRADE_PAPER_DB", str(tmp_path / "ledger.sqlite3"))
    headers = {"Authorization": "Bearer test-production-token-with-at-least-32-chars"}

    status = client.get("/api/v1/swarmtrade/paper/status", headers=headers)
    assert status.status_code == 200
    assert status.json()["enabled"] is False
    assert status.json()["status"] == "disabled"

    accounts = client.get("/api/v1/swarmtrade/paper/accounts", headers=headers)
    assert accounts.status_code == 503


def test_paper_ledger_open_close_and_idempotent_replay(monkeypatch, tmp_path):
    monkeypatch.setenv("FINAI_ENABLE_SWARMTRADE_PAPER_LEDGER", "1")
    monkeypatch.setenv("FINAI_SWARMTRADE_PAPER_DB", str(tmp_path / "ledger.sqlite3"))
    account = client.post("/api/v1/swarmtrade/paper/accounts", json={
        "label": "Test account", "currency": "USD", "initial_capital": 100000,
    })
    assert account.status_code == 200
    account_id = account.json()["account_id"]

    body = {
        "idempotency_key": "open-001",
        "acknowledge_simulation_only": True,
        "quote_currency": "USD",
        "plan": approved_plan_request(),
    }
    opened = client.post(f"/api/v1/swarmtrade/paper/accounts/{account_id}/positions", json=body)
    assert opened.status_code == 200, opened.text
    position = opened.json()
    assert position["execution"]["real_order_submitted"] is False
    assert position["execution"]["simulated_entry_recorded"] is True

    opened_again = client.post(f"/api/v1/swarmtrade/paper/accounts/{account_id}/positions", json=body)
    assert opened_again.status_code == 200
    assert opened_again.json()["position_id"] == position["position_id"]
    assert opened_again.json()["idempotent_replay"] is True

    closed_body = {"idempotency_key": "close-001", "exit_price": 115, "reason": "target"}
    closed = client.post(
        f"/api/v1/swarmtrade/paper/accounts/{account_id}/positions/{position['position_id']}/close",
        json=closed_body,
    )
    assert closed.status_code == 200
    assert closed.json()["execution"]["real_order_submitted"] is False
    assert closed.json()["net_pnl"] > 0

    closed_again = client.post(
        f"/api/v1/swarmtrade/paper/accounts/{account_id}/positions/{position['position_id']}/close",
        json=closed_body,
    )
    assert closed_again.status_code == 200
    assert closed_again.json()["idempotent_replay"] is True

    snapshot = client.get(f"/api/v1/swarmtrade/paper/accounts/{account_id}")
    assert snapshot.status_code == 200
    assert snapshot.json()["open_position_count"] == 0
    assert snapshot.json()["realized_pnl"] > 0

    history = client.get(f"/api/v1/swarmtrade/paper/accounts/{account_id}/positions?status=closed")
    assert history.status_code == 200
    assert history.json()["count"] == 1
    assert history.json()["positions"][0]["status"] == "CLOSED"


def test_paper_ledger_requires_explicit_confirmation(monkeypatch, tmp_path):
    monkeypatch.setenv("FINAI_ENABLE_SWARMTRADE_PAPER_LEDGER", "1")
    monkeypatch.setenv("FINAI_SWARMTRADE_PAPER_DB", str(tmp_path / "ledger.sqlite3"))
    account = client.post("/api/v1/swarmtrade/paper/accounts", json={"currency": "USD", "initial_capital": 10000}).json()
    response = client.post(
        f"/api/v1/swarmtrade/paper/accounts/{account['account_id']}/positions",
        json={"idempotency_key": "open", "acknowledge_simulation_only": False,
        "quote_currency": "USD", "plan": approved_plan_request()},
    )
    assert response.status_code == 422


def test_paper_ledger_blocks_aggregate_risk_after_three_one_percent_positions(monkeypatch, tmp_path):
    monkeypatch.setenv("FINAI_ENABLE_SWARMTRADE_PAPER_LEDGER", "1")
    monkeypatch.setenv("FINAI_SWARMTRADE_PAPER_DB", str(tmp_path / "ledger.sqlite3"))
    account = client.post("/api/v1/swarmtrade/paper/accounts", json={"currency": "USD", "initial_capital": 100000}).json()
    account_id = account["account_id"]
    for index in range(3):
        open_body = {
            "idempotency_key": f"open-{index}",
            "acknowledge_simulation_only": True,
            "quote_currency": "USD",
            "plan": approved_plan_request(risk_pct=1.0, fee_bps=0, slippage_bps=0),
        }
        opened = client.post(f"/api/v1/swarmtrade/paper/accounts/{account_id}/positions", json=open_body)
        assert opened.status_code == 200, opened.text

    too_many_risk = client.post(
        f"/api/v1/swarmtrade/paper/accounts/{account_id}/positions",
        json={
            "idempotency_key": "open-4",
            "acknowledge_simulation_only": True,
            "quote_currency": "USD",
            "plan": approved_plan_request(risk_pct=1.0, fee_bps=0, slippage_bps=0),
        },
    )
    assert too_many_risk.status_code == 409


def test_paper_ledger_blocks_position_after_realized_daily_loss_limit(monkeypatch, tmp_path):
    monkeypatch.setenv("FINAI_ENABLE_SWARMTRADE_PAPER_LEDGER", "1")
    monkeypatch.setenv("FINAI_SWARMTRADE_PAPER_DB", str(tmp_path / "ledger.sqlite3"))
    account = client.post("/api/v1/swarmtrade/paper/accounts", json={"currency": "USD", "initial_capital": 10000}).json()
    account_id = account["account_id"]

    opened = client.post(
        f"/api/v1/swarmtrade/paper/accounts/{account_id}/positions",
        json={
            "idempotency_key": "open-loss",
            "acknowledge_simulation_only": True,
            "quote_currency": "USD",
            "plan": approved_plan_request(risk_pct=1.0, fee_bps=0, slippage_bps=0),
        },
    )
    assert opened.status_code == 200, opened.text
    position_id = opened.json()["position_id"]
    closed = client.post(
        f"/api/v1/swarmtrade/paper/accounts/{account_id}/positions/{position_id}/close",
        json={"idempotency_key": "close-loss", "exit_price": 90, "reason": "stop"},
    )
    assert closed.status_code == 200
    assert closed.json()["net_pnl"] < 0

    blocked = client.post(
        f"/api/v1/swarmtrade/paper/accounts/{account_id}/positions",
        json={
            "idempotency_key": "next-open",
            "acknowledge_simulation_only": True,
            "quote_currency": "USD",
            "plan": approved_plan_request(risk_pct=1.0, fee_bps=0, slippage_bps=0),
        },
    )
    assert blocked.status_code == 409


def test_paper_ledger_does_not_accept_stop_close_before_stop_price(monkeypatch, tmp_path):
    monkeypatch.setenv("FINAI_ENABLE_SWARMTRADE_PAPER_LEDGER", "1")
    monkeypatch.setenv("FINAI_SWARMTRADE_PAPER_DB", str(tmp_path / "ledger.sqlite3"))
    account = client.post("/api/v1/swarmtrade/paper/accounts", json={"currency": "USD", "initial_capital": 100000}).json()
    account_id = account["account_id"]
    opened = client.post(
        f"/api/v1/swarmtrade/paper/accounts/{account_id}/positions",
        json={
            "idempotency_key": "open-stop-check",
            "acknowledge_simulation_only": True,
            "quote_currency": "USD",
            "plan": approved_plan_request(),
        },
    )
    assert opened.status_code == 200
    position_id = opened.json()["position_id"]
    response = client.post(
        f"/api/v1/swarmtrade/paper/accounts/{account_id}/positions/{position_id}/close",
        json={"idempotency_key": "close-stop-too-early", "exit_price": 98, "reason": "stop"},
    )
    assert response.status_code == 409


def test_paper_ledger_rejects_account_currency_mismatch(monkeypatch, tmp_path):
    monkeypatch.setenv("FINAI_ENABLE_SWARMTRADE_PAPER_LEDGER", "1")
    monkeypatch.setenv("FINAI_SWARMTRADE_PAPER_DB", str(tmp_path / "ledger.sqlite3"))
    account = client.post(
        "/api/v1/swarmtrade/paper/accounts",
        json={"currency": "INR", "initial_capital": 100000},
    ).json()
    response = client.post(
        f"/api/v1/swarmtrade/paper/accounts/{account['account_id']}/positions",
        json={
            "idempotency_key": "currency-mismatch",
            "acknowledge_simulation_only": True,
            "quote_currency": "USD",
            "plan": approved_plan_request(),
        },
    )
    assert response.status_code == 409
    assert "does not match instrument quote currency" in response.json()["detail"]


def test_paper_ledger_close_is_disabled_when_feature_flag_is_off(monkeypatch, tmp_path):
    monkeypatch.delenv("FINAI_ENABLE_SWARMTRADE_PAPER_LEDGER", raising=False)
    monkeypatch.setenv("FINAI_SWARMTRADE_PAPER_DB", str(tmp_path / "ledger.sqlite3"))
    response = client.post(
        "/api/v1/swarmtrade/paper/accounts/nonexistent/positions/nonexistent/close",
        json={"idempotency_key": "closed-while-disabled", "exit_price": 100, "reason": "manual"},
    )
    assert response.status_code == 503
    assert "Paper ledger is disabled" in response.json()["detail"]


def test_paper_ledger_rejects_idempotency_key_reuse_with_changed_open_payload(monkeypatch, tmp_path):
    monkeypatch.setenv("FINAI_ENABLE_SWARMTRADE_PAPER_LEDGER", "1")
    monkeypatch.setenv("FINAI_SWARMTRADE_PAPER_DB", str(tmp_path / "ledger.sqlite3"))
    account = client.post(
        "/api/v1/swarmtrade/paper/accounts",
        json={"currency": "USD", "initial_capital": 100000},
    ).json()
    account_id = account["account_id"]
    base_body = {
        "idempotency_key": "same-open-key",
        "acknowledge_simulation_only": True,
        "quote_currency": "USD",
        "plan": approved_plan_request(),
    }
    first = client.post(
        f"/api/v1/swarmtrade/paper/accounts/{account_id}/positions",
        json=base_body,
    )
    assert first.status_code == 200, first.text

    changed_body = {
        **base_body,
        "plan": approved_plan_request(target_price=115),
    }
    replay = client.post(
        f"/api/v1/swarmtrade/paper/accounts/{account_id}/positions",
        json=changed_body,
    )
    assert replay.status_code == 409
    assert "Idempotency key" in replay.json()["detail"]


def test_paper_ledger_rejects_idempotency_key_reuse_with_changed_close_payload(monkeypatch, tmp_path):
    monkeypatch.setenv("FINAI_ENABLE_SWARMTRADE_PAPER_LEDGER", "1")
    monkeypatch.setenv("FINAI_SWARMTRADE_PAPER_DB", str(tmp_path / "ledger.sqlite3"))
    account = client.post(
        "/api/v1/swarmtrade/paper/accounts",
        json={"currency": "USD", "initial_capital": 100000},
    ).json()
    account_id = account["account_id"]
    opened = client.post(
        f"/api/v1/swarmtrade/paper/accounts/{account_id}/positions",
        json={
            "idempotency_key": "open-for-close-key-test",
            "acknowledge_simulation_only": True,
            "quote_currency": "USD",
            "plan": approved_plan_request(),
        },
    )
    assert opened.status_code == 200, opened.text
    position_id = opened.json()["position_id"]

    first_close = client.post(
        f"/api/v1/swarmtrade/paper/accounts/{account_id}/positions/{position_id}/close",
        json={"idempotency_key": "same-close-key", "exit_price": 115, "reason": "target"},
    )
    assert first_close.status_code == 200, first_close.text

    changed_close = client.post(
        f"/api/v1/swarmtrade/paper/accounts/{account_id}/positions/{position_id}/close",
        json={"idempotency_key": "same-close-key", "exit_price": 116, "reason": "target"},
    )
    assert changed_close.status_code == 409
    assert "Idempotency key" in changed_close.json()["detail"]

def test_paper_ledger_persists_account_across_instances(tmp_path):
    db_path = tmp_path / "persistent-ledger.sqlite3"
    first = PaperLedger(db_path)
    account = first.create_account(label="Restart test", currency="INR", initial_capital=25000)

    # A new ledger object represents a fresh application process using the same DB.
    second = PaperLedger(db_path)
    reloaded = second.get_account(account["account_id"])
    assert reloaded["label"] == "Restart test"
    assert reloaded["currency"] == "INR"
    assert reloaded["initial_capital"] == 25000
    assert reloaded["realized_pnl"] == 0
    assert reloaded["open_position_count"] == 0

def test_paper_ledger_reloads_position_history_after_new_instance(monkeypatch, tmp_path):
    monkeypatch.setenv("FINAI_ENABLE_SWARMTRADE_PAPER_LEDGER", "1")
    db_path = tmp_path / "restart-workflow.sqlite3"
    monkeypatch.setenv("FINAI_SWARMTRADE_PAPER_DB", str(db_path))
    account = client.post(
        "/api/v1/swarmtrade/paper/accounts",
        json={"label": "Restart workflow", "currency": "USD", "initial_capital": 100000},
    )
    assert account.status_code == 200, account.text
    account_id = account.json()["account_id"]
    opened = client.post(
        f"/api/v1/swarmtrade/paper/accounts/{account_id}/positions",
        json={
            "idempotency_key": "restart-open",
            "acknowledge_simulation_only": True,
            "quote_currency": "USD",
            "plan": approved_plan_request(),
        },
    )
    assert opened.status_code == 200, opened.text
    position_id = opened.json()["position_id"]
    closed = client.post(
        f"/api/v1/swarmtrade/paper/accounts/{account_id}/positions/{position_id}/close",
        json={"idempotency_key": "restart-close", "exit_price": 115, "reason": "target"},
    )
    assert closed.status_code == 200, closed.text

    # A new ledger object simulates a process restart against the same SQLite file.
    restarted = PaperLedger(db_path)
    account_after_restart = restarted.get_account(account_id)
    history_after_restart = restarted.list_positions(account_id, status="closed")
    assert account_after_restart["open_position_count"] == 0
    assert account_after_restart["realized_pnl"] == closed.json()["net_pnl"]
    assert history_after_restart["count"] == 1
    assert history_after_restart["positions"][0]["position_id"] == position_id
    assert history_after_restart["positions"][0]["status"] == "CLOSED"

def test_paper_entry_halt_blocks_new_positions_but_allows_closing_existing_position(monkeypatch, tmp_path):
    monkeypatch.setenv("FINAI_ENABLE_SWARMTRADE_PAPER_LEDGER", "1")
    monkeypatch.delenv("FINAI_SWARMTRADE_PAPER_ENTRIES_HALTED", raising=False)
    monkeypatch.delenv("FINAI_SWARMTRADE_PAPER_HALT_FILE", raising=False)
    monkeypatch.setenv("FINAI_SWARMTRADE_PAPER_DB", str(tmp_path / "entry-halt.sqlite3"))
    account = client.post(
        "/api/v1/swarmtrade/paper/accounts",
        json={"label": "Entry halt test", "currency": "USD", "initial_capital": 100000},
    )
    assert account.status_code == 200, account.text
    account_id = account.json()["account_id"]

    open_body = {
        "idempotency_key": "halt-test-open",
        "acknowledge_simulation_only": True,
        "quote_currency": "USD",
        "plan": approved_plan_request(),
    }
    opened = client.post(
        f"/api/v1/swarmtrade/paper/accounts/{account_id}/positions",
        json=open_body,
    )
    assert opened.status_code == 200, opened.text
    position_id = opened.json()["position_id"]

    monkeypatch.setenv("FINAI_SWARMTRADE_PAPER_ENTRIES_HALTED", "true")
    status = client.get("/api/v1/swarmtrade/paper/status")
    assert status.status_code == 200
    assert status.json()["new_entries_halted"] is True
    assert status.json()["close_operations_allowed_during_entry_halt"] is True

    # Retrying an already-successful idempotent request must replay; it cannot
    # create new exposure and should remain deterministic during the halt.
    replay = client.post(
        f"/api/v1/swarmtrade/paper/accounts/{account_id}/positions",
        json=open_body,
    )
    assert replay.status_code == 200
    assert replay.json()["idempotent_replay"] is True
    assert replay.json()["position_id"] == position_id

    blocked = client.post(
        f"/api/v1/swarmtrade/paper/accounts/{account_id}/positions",
        json={
            **open_body,
            "idempotency_key": "halt-test-second-open",
        },
    )
    assert blocked.status_code == 423
    assert "entry halt is active" in blocked.json()["detail"]

    # The pause prevents adding exposure but must not trap an already-open paper position.
    closed = client.post(
        f"/api/v1/swarmtrade/paper/accounts/{account_id}/positions/{position_id}/close",
        json={"idempotency_key": "halt-test-close", "exit_price": 105, "reason": "manual"},
    )
    assert closed.status_code == 200, closed.text
    assert closed.json()["execution"]["real_order_submitted"] is False
    snapshot = client.get(f"/api/v1/swarmtrade/paper/accounts/{account_id}")
    assert snapshot.status_code == 200
    assert snapshot.json()["open_position_count"] == 0

def test_paper_entry_halt_file_is_checked_dynamically(monkeypatch, tmp_path):
    monkeypatch.delenv("FINAI_SWARMTRADE_PAPER_ENTRIES_HALTED", raising=False)
    halt_file = tmp_path / "paper-entries.halt"
    monkeypatch.setenv("FINAI_SWARMTRADE_PAPER_HALT_FILE", str(halt_file))
    assert client.get("/api/v1/swarmtrade/paper/status").json()["new_entries_halted"] is False

    halt_file.write_text("operator requested entry pause", encoding="utf-8")
    assert client.get("/api/v1/swarmtrade/paper/status").json()["new_entries_halted"] is True

    halt_file.unlink()
    assert client.get("/api/v1/swarmtrade/paper/status").json()["new_entries_halted"] is False

def test_paper_entry_halt_is_rechecked_inside_write_transaction(monkeypatch, tmp_path):
    from app import swarmtrade_paper_api
    from swarmtrade import paper_ledger

    monkeypatch.setenv("FINAI_ENABLE_SWARMTRADE_PAPER_LEDGER", "1")
    monkeypatch.delenv("FINAI_SWARMTRADE_PAPER_ENTRIES_HALTED", raising=False)
    monkeypatch.delenv("FINAI_SWARMTRADE_PAPER_HALT_FILE", raising=False)
    monkeypatch.setenv("FINAI_SWARMTRADE_PAPER_DB", str(tmp_path / "transaction-halt.sqlite3"))
    account = client.post(
        "/api/v1/swarmtrade/paper/accounts",
        json={"label": "Transaction halt test", "currency": "USD", "initial_capital": 100000},
    )
    assert account.status_code == 200, account.text

    # Simulate a halt becoming active after the API pre-check but before the
    # ledger acquires its write transaction.
    monkeypatch.setattr(swarmtrade_paper_api, "_entries_halted", lambda: False)
    monkeypatch.setattr(paper_ledger, "paper_entries_halted", lambda: True)
    response = client.post(
        f"/api/v1/swarmtrade/paper/accounts/{account.json()['account_id']}/positions",
        json={
            "idempotency_key": "transaction-halt-open",
            "acknowledge_simulation_only": True,
            "quote_currency": "USD",
            "plan": approved_plan_request(),
        },
    )
    assert response.status_code == 423
    assert "entry halt is active" in response.json()["detail"]
    assert PaperLedger(tmp_path / "transaction-halt.sqlite3").list_positions(
        account.json()["account_id"], status="open"
    )["count"] == 0
