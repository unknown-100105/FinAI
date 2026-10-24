from fastapi.testclient import TestClient

from app.main import app
from swarmtrade.engine import build_swarm_plan

client = TestClient(app)


def bullish_request(**overrides):
    data = {
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
    data.update(overrides)
    return data


def test_swarmtrade_is_deterministic_and_limits_agents_to_500():
    request = bullish_request()
    first = build_swarm_plan(request)
    second = build_swarm_plan(request)
    assert first == second
    assert first["agent_count"] == 500
    assert first["logical_agents_only"] is True
    assert first["status"] == "APPROVED_FOR_SIMULATION"
    assert first["execution"]["order_submitted"] is False
    assert first["execution"]["fill_claimed"] is False


def test_swarmtrade_enforces_hard_risk_budget_even_if_user_requests_more():
    result = build_swarm_plan(bullish_request(risk_pct=5))
    assert result["status"] == "APPROVED_FOR_SIMULATION"
    assert result["risk"]["effective_risk_pct"] <= 1.0
    assert result["risk"]["estimated_total_risk"] <= result["risk"]["risk_budget"] + 1e-8


def test_swarmtrade_blocks_when_daily_loss_limit_reached():
    result = build_swarm_plan(bullish_request(current_daily_loss_pct=2.0, max_daily_loss_pct=2.0))
    assert result["status"] == "REJECTED"
    assert "Daily loss limit" in result["reason"]


def test_swarmtrade_requires_valid_protective_levels():
    result = build_swarm_plan(bullish_request(stop_price=102, target_price=110))
    assert result["status"] == "REJECTED"
    assert "Long trade requires" in result["reason"]


def test_swarmtrade_options_require_explicit_max_loss_per_contract():
    result = build_swarm_plan(bullish_request(asset_class="option", multiplier=100))
    assert result["status"] == "REJECTED"
    assert "max_loss_per_unit" in result["reason"]


def test_swarmtrade_no_signal_does_not_trade():
    result = build_swarm_plan(bullish_request(signals={}))
    assert result["status"] == "NO_SIGNAL"
    assert result["execution"]["order_submitted"] is False


def test_swarmtrade_api_status_and_plan():
    status = client.get("/api/v1/swarmtrade/status")
    assert status.status_code == 200
    assert status.json()["max_logical_agents"] == 500
    response = client.post("/api/v1/swarmtrade/plan", json=bullish_request())
    assert response.status_code == 200
    assert response.json()["status"] == "APPROVED_FOR_SIMULATION"


def test_swarmtrade_api_rejects_agent_count_over_limit():
    response = client.post("/api/v1/swarmtrade/plan", json=bullish_request(agent_count=501))
    assert response.status_code == 422


def test_swarmtrade_api_rejects_unknown_signal_key():
    response = client.post("/api/v1/swarmtrade/plan", json=bullish_request(signals={"inside_info": 1}))
    assert response.status_code == 422


def test_swarmtrade_futures_require_tick_value_and_margin_metadata():
    result = build_swarm_plan(bullish_request(asset_class="future", multiplier=50))
    assert result["status"] == "REJECTED"
    assert "tick_size, tick_value, and margin_per_unit" in result["reason"]


def test_swarmtrade_future_risk_uses_exchange_tick_value():
    result = build_swarm_plan(bullish_request(
        asset_class="future",
        multiplier=50,
        tick_size=0.25,
        tick_value=12.5,
        margin_per_unit=5000,
    ))
    assert result["status"] == "APPROVED_FOR_SIMULATION"
    assert result["risk"]["risk_model"]["model"] == "futures_tick_value"
    assert result["risk"]["risk_model"]["tick_size"] == 0.25
    assert result["sizing"]["quantity"] >= 1


def test_swarmtrade_forex_requires_account_currency_pip_metadata():
    result = build_swarm_plan(bullish_request(asset_class="forex", multiplier=100000))
    assert result["status"] == "REJECTED"
    assert "pip_size, pip_value_per_unit, and margin_per_unit" in result["reason"]


def test_swarmtrade_forex_risk_uses_pip_value_and_lot_margin():
    result = build_swarm_plan(bullish_request(
        asset_class="forex",
        entry_price=1.1,
        stop_price=1.095,
        target_price=1.12,
        capital=500000,
        multiplier=100000,
        unit_step=1,
        pip_size=0.0001,
        pip_value_per_unit=10,
        margin_per_unit=2000,
        margin_rate=0.05,
        max_leverage=30,
    ))
    assert result["status"] == "APPROVED_FOR_SIMULATION"
    assert result["risk"]["risk_model"]["model"] == "forex_pip_value"
    assert result["risk"]["risk_model"]["pip_size"] == 0.0001
    assert result["sizing"]["quantity"] >= 1
