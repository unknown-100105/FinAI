from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app import swarmtrade_agent_mesh_api
from swarmtrade.agent_mesh import AgentEvidenceStore

client = TestClient(app)


def evidence_payload(**overrides):
    now = datetime.now(timezone.utc)
    payload = {
        "evidence_id": "evidence-1",
        "agent_id": "technical-01",
        "role": "technical",
        "agent_version": "test-v1",
        "instrument": "NSE:RELIANCE",
        "claim": "Price momentum is positive over the selected horizon.",
        "source_ids": ["market-feed:tick-1"],
        "source_timestamp": now.isoformat(),
        "observed_at": now.isoformat(),
        "confidence": 0.72,
        "stance": "bullish",
        "invalidation": "Momentum reverses below the measured threshold.",
        "missing_data": [],
    }
    payload.update(overrides)
    return payload


@pytest.fixture
def isolated_store(tmp_path, monkeypatch):
    store = AgentEvidenceStore(tmp_path / "agent-evidence.sqlite3")
    monkeypatch.setattr(swarmtrade_agent_mesh_api, "store", store)
    return store


def test_agent_mesh_status_never_enables_live_orders():
    response = client.get("/api/v1/swarmtrade/agent-mesh/status")
    assert response.status_code == 200
    assert response.json()["mode"] == "research_only"
    assert response.json()["live_order_execution"] is False
    assert response.json()["trade_signal_authority"] is False


def test_agent_mesh_shares_persistent_provenance_aware_evidence(isolated_store):
    run = client.post("/api/v1/swarmtrade/agent-mesh/runs", json={
        "symbol": "reliance", "asset_class": "equity", "venue": "NSE", "timeframe": "15m"
    })
    assert run.status_code == 200
    run_id = run.json()["run_id"]
    assert run.json()["order_submission_enabled"] is False

    submitted = client.post(
        f"/api/v1/swarmtrade/agent-mesh/runs/{run_id}/evidence",
        json=evidence_payload(),
    )
    assert submitted.status_code == 200
    assert submitted.json()["accepted"] is True
    assert submitted.json()["execution_authority"] is False

    summary = client.get(f"/api/v1/swarmtrade/agent-mesh/runs/{run_id}/summary")
    assert summary.status_code == 200
    body = summary.json()
    assert body["evidence_count"] == 1
    assert body["distinct_roles"] == ["technical"]
    assert body["stance_counts"]["bullish"] == 1
    assert body["evidence"][0]["source_ids"] == ["market-feed:tick-1"]
    assert body["order_submission_enabled"] is False


def test_agent_mesh_rejects_unknown_run_and_unknown_agent_role(isolated_store):
    missing = client.post("/api/v1/swarmtrade/agent-mesh/runs/no-such-run/evidence",
                          json=evidence_payload())
    assert missing.status_code == 404

    run = isolated_store.create_run({"symbol": "BTCUSD", "asset_class": "crypto"})
    with pytest.raises(ValueError, match="supported agent role"):
        isolated_store.add_evidence(run["run_id"], evidence_payload(role="order_submitter"))


def test_agent_mesh_rejects_future_source_timestamp(isolated_store):
    run = isolated_store.create_run({"symbol": "AAPL", "asset_class": "equity"})
    future = (datetime.now(timezone.utc) + timedelta(minutes=5)).isoformat()
    with pytest.raises(ValueError, match="future"):
        isolated_store.add_evidence(run["run_id"], evidence_payload(source_timestamp=future))


def test_agent_mesh_rejects_missing_provenance_and_invalid_confidence(isolated_store):
    run = isolated_store.create_run({"symbol": "ES", "asset_class": "future", "venue": "CME"})
    with pytest.raises(ValueError, match="source_ids"):
        isolated_store.add_evidence(run["run_id"], evidence_payload(source_ids=[]))
    with pytest.raises(ValueError, match="confidence"):
        isolated_store.add_evidence(run["run_id"], evidence_payload(confidence=1.2))


def test_agent_mesh_duplicate_evidence_id_is_not_silently_overwritten(isolated_store):
    run = isolated_store.create_run({"symbol": "AAPL", "asset_class": "equity"})
    isolated_store.add_evidence(run["run_id"], evidence_payload())
    with pytest.raises(Exception):
        isolated_store.add_evidence(run["run_id"], evidence_payload())
    summary = isolated_store.summary(run["run_id"])
    assert summary["evidence_count"] == 1
