import json
from pathlib import Path

import numpy as np


def test_empirical_channel_calibration_replaces_research_prior():
    from causal_risk.channel_calibration import COEFFICIENT_KEYS, fit_channel_calibration

    rng = np.random.default_rng(42)
    n = 100
    x = {
        "rates": rng.normal(size=n),
        "credit": rng.normal(size=n),
        "oil": rng.normal(size=n),
        "usd": rng.normal(size=n),
        "liquidity": rng.normal(size=n),
        "equity": rng.normal(size=n),
    }
    equity = x["equity"] + 0.4 * x["liquidity"] + rng.normal(scale=0.05, size=n)
    debt = (
        -0.2 * x["rates"]
        -0.3 * x["credit"]
        + 0.1 * x["oil"]
        -0.15 * x["liquidity"]
        + rng.normal(scale=0.05, size=n)
    )
    gold = (
        -0.1 * x["usd"]
        -0.05 * x["rates"]
        + 0.08 * x["oil"]
        + rng.normal(scale=0.05, size=n)
    )
    portfolio = 0.6 * equity + 0.3 * debt + 0.1 * gold
    systemic = (
        0.3 * np.abs(x["liquidity"])
        + 0.3 * np.abs(equity)
        + 0.2 * np.abs(debt)
        + 0.2 * np.abs(portfolio)
        + rng.normal(scale=0.05, size=n)
    )
    rows = [
        {key: float(values[i]) for key, values in x.items()}
        for i in range(n)
    ]
    result = fit_channel_calibration(
        rows,
        {
            "equity": equity,
            "debt": debt,
            "gold": gold,
            "portfolio": portfolio,
            "systemic_stress": systemic,
        },
        alpha=0.5,
    )
    assert result["status"] == "empirical_fit"
    assert result["validation"]["chronological_split"] is True
    assert set(result["coefficients"]) == set(COEFFICIENT_KEYS)
    assert result["coefficients"]["equity_from_liquidity"] > 0


def test_risk_calibration_can_select_reviewed_empirical_bundle(tmp_path, monkeypatch):
    from causal_risk.risk_calibration import load_risk_calibration

    base = load_risk_calibration()
    bundle = dict(base)
    bundle["version"] = "test-empirical"
    bundle["status"] = "empirical_fit"
    bundle["validation"] = {
        "empirical_fit_available": True,
        "causal_identification": False,
    }
    target = tmp_path / "empirical.json"
    target.write_text(json.dumps(bundle), encoding="utf-8")
    monkeypatch.setenv("FINAI_RISK_CALIBRATION_PATH", str(target))
    selected = load_risk_calibration()
    assert selected["version"] == "test-empirical"
    assert selected["status"] == "empirical_fit"


def test_causal_stress_reward_is_finite_and_positive():
    import torch

    from causal_risk.stress_objectives import CausalStressReward

    reward = CausalStressReward(
        empirical_center=(50.0, 40.0),
        empirical_scale=(10.0, 10.0),
        edge_matrix=((0.0, 0.8), (0.0, 0.0)),
        portfolio_weights=(0.7, 0.3),
    )
    values = reward(torch.tensor([[1.0, 1.0], [-1.0, 0.5]]))
    assert values.shape == (2,)
    assert torch.isfinite(values).all()
    assert torch.all(values > 0)


def test_gflownet_accepts_causal_empirical_reward():
    from causal_risk.gfnets import GFlowConfig, GFlowNetTailGenerator
    from causal_risk.stress_objectives import CausalStressReward

    generator = GFlowNetTailGenerator(
        2,
        GFlowConfig(hidden_dim=16, epochs=2, seed=4),
    )
    reward = CausalStressReward(
        empirical_center=(75.0, 50.0),
        empirical_scale=(20.0, 15.0),
        edge_matrix=((0.0, 0.5), (0.0, 0.0)),
        portfolio_weights=(0.6, 0.4),
    )
    result = generator.train(
        reward_fn=reward,
        objective_name="causal_empirical_tail_reward",
    )
    assert result["objective"] == "causal_empirical_tail_reward"
    assert result["reward_metadata"]["objective"] == "causal_empirical_tail_reward"


def test_temporal_sequence_training_has_future_holdout():
    import torch

    from causal_risk.temporal_gnn import (
        TemporalSnapshot,
        build_temporal_edges,
        train_temporal_sequence_model,
    )

    rng = np.random.default_rng(8)
    snapshots = []
    edges = build_temporal_edges([0, 1, 0], [1, 2, 2], [1.0, 1.0, 2.0])
    for i in range(6):
        X = torch.tensor(rng.normal(size=(3, 2)), dtype=torch.float32)
        y = torch.tensor(
            X[:, 0].numpy() * 0.3 + i * 0.02,
            dtype=torch.float32,
        )
        snapshots.append(TemporalSnapshot(X, y, edges))
    result = train_temporal_sequence_model(
        snapshots,
        hidden_features=8,
        heads=2,
        epochs=2,
        seed=7,
        device="cpu",
    )
    assert result["status"] == "TGAT_TEMPORAL_HOLDOUT_VALIDATION_READY"
    assert result["chronological_holdout"] is True
    assert result["test_snapshots"] == 2
    assert np.isfinite(result["future_holdout_mae"])


def test_multimodal_encoder_trains_with_masked_modalities():
    from causal_risk.multimodal_encoder import (
        MultimodalEncoderConfig,
        train_multimodal_encoder,
    )

    rng = np.random.default_rng(11)
    inputs = {
        "market": rng.normal(size=(12, 3)).tolist(),
        "macro": rng.normal(size=(12, 2)).tolist(),
        "text": rng.normal(size=(12, 4)).tolist(),
    }
    result = train_multimodal_encoder(
        inputs,
        config=MultimodalEncoderConfig(hidden_dim=8, layers=1, heads=2),
        epochs=3,
        mask_probability=0.75,
        seed=3,
    )
    assert result["status"] == "MULTIMODAL_ENCODER_RESEARCH_TRAINED"
    assert result["missing_modality_support"] is True
    assert len(result["embedding"]) == 12
    assert len(result["embedding"][0]) == 8


def test_temporal_training_api_uses_future_holdout():
    from app.main import app
    from fastapi.testclient import TestClient

    snapshots = []
    for i in range(5):
        snapshots.append({
            "node_features": [[0.1 + i * 0.01, 0.2], [0.2, 0.1], [0.4, 0.3]],
            "target": [0.1, 0.2, 0.4],
            "edge_sources": [0, 1, 0],
            "edge_targets": [1, 2, 2],
            "time_deltas": [1.0, 1.0, 2.0],
        })
    response = TestClient(app).post(
        "/api/v1/causal-risk/temporal-gnn/train",
        json={
            "snapshots": snapshots,
            "epochs": 1,
            "hidden_features": 8,
            "heads": 2,
            "device": "cpu",
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["chronological_holdout"] is True


def test_advanced_api_enforces_multimodal_node_limit():
    from app.main import app
    from fastapi.testclient import TestClient

    nodes = [
        {
            "node_id": f"n-{i}",
            "node_type": "asset",
            "modality": "market",
            "features": [1.0],
            "provenance": "test",
        }
        for i in range(501)
    ]
    response = TestClient(app).post(
        "/api/v1/causal-risk/multimodal/encode",
        json={
            "nodes": nodes,
            "edges": [],
            "target_node": "n-0",
            "modality_vectors": {"market": [1.0]},
        },
    )
    assert response.status_code == 422


def test_channel_calibration_api_returns_empirical_bundle():
    from app.main import app
    from fastapi.testclient import TestClient

    rng = np.random.default_rng(55)
    n = 80
    rows = []
    for i in range(n):
        rates, credit, oil, usd, liq = rng.normal(size=5)
        equity = 0.3 * liq + rng.normal(scale=0.05)
        debt = -0.2 * rates - 0.15 * credit + 0.1 * oil - 0.1 * liq + rng.normal(scale=0.05)
        gold = -0.1 * usd + 0.05 * rates + 0.03 * oil + rng.normal(scale=0.05)
        portfolio = 0.6 * equity + 0.3 * debt + 0.1 * gold
        rows.append({
            "rates": float(rates), "credit": float(credit), "oil": float(oil),
            "usd": float(usd), "liquidity": float(liq), "equity": float(equity),
        })
    observed = {
        "equity": [0.3 * row["liquidity"] for row in rows],
        "debt": [-0.2 * row["rates"] - 0.15 * row["credit"] + 0.1 * row["oil"] - 0.1 * row["liquidity"] for row in rows],
        "gold": [-0.1 * row["usd"] + 0.05 * row["rates"] + 0.03 * row["oil"] for row in rows],
        "portfolio": [0.0 for _ in rows],
        "systemic_stress": [abs(row["liquidity"]) for row in rows],
    }
    response = TestClient(app).post(
        "/api/v1/causal-risk/risk-calibration/fit-channels",
        json={"scm_samples": rows, "observed_channels": observed},
    )
    assert response.status_code == 200
    assert response.json()["status"] == "empirical_fit"


def test_research_evaluation_metrics_are_available():
    from causal_risk.research_evaluation import (
        ablation_summary,
        perturb_features,
        scenario_quality_metrics,
        tail_backtest_metrics,
    )

    tail = tail_backtest_metrics(
        [1.0, 2.0, 0.5, 3.0],
        [1.2, 1.8, 1.0, 2.5],
        level=0.75,
    )
    assert tail["status"] == "TAIL_BACKTEST_READY"

    scenarios = np.asarray([[1.0, 0.5], [1.2, 0.6], [0.8, 0.4]])
    quality = scenario_quality_metrics(
        scenarios,
        [[0.9, 0.45], [1.1, 0.55]],
        causal_edge_matrix=[[0.0, 0.5], [0.0, 0.0]],
    )
    assert quality["status"] == "SCENARIO_QUALITY_READY"
    assert quality["causal_direction_alignment"] is not None

    summary = ablation_summary(
        {"baseline": {"mae": 1.0}, "finai": {"mae": 0.8}},
        primary_metric="mae",
    )
    assert summary["status"] == "ABLATION_SUMMARY_READY"
    perturbed = perturb_features([[1.0, 2.0], [3.0, 4.0]], scale=2.0, missing_columns=[1], seed=2)
    assert np.allclose(perturbed[:, 1], 0.0)


def test_multimodal_training_api_returns_json_serializable_result():
    from fastapi.testclient import TestClient
    from app.main import app

    response = TestClient(app).post(
        "/api/v1/causal-risk/multimodal/train",
        json={
            "inputs": {
                "market": [
                    [0.1, 0.2],
                    [0.2, 0.3],
                    [0.3, 0.5],
                    [0.4, 0.6],
                ],
                "macro": [
                    [0.4, 0.2],
                    [0.3, 0.4],
                    [0.2, 0.5],
                    [0.1, 0.6],
                ],
            },
            "hidden_dim": 8,
            "layers": 1,
            "heads": 2,
            "epochs": 1,
            "learning_rate": 0.001,
            "mask_probability": 0.5,
            "seed": 42,
        },
    )

    assert response.status_code == 200, response.text

    payload = response.json()
    assert payload["status"] == "MULTIMODAL_ENCODER_RESEARCH_TRAINED"
    assert payload["embedding_dimension"] == 8
    assert payload["model_persisted"] is False
    assert "model" not in payload
    assert len(payload["embedding"]) == 4
    assert len(payload["embedding"][0]) == 8
