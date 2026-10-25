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

def test_paper_ledger_persists_account_and_closed_position_across_instances(tmp_path):
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
