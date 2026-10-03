import numpy as np
from causal_risk.discovery import notears_linear
from causal_risk.dynamic_discovery import discover_lagged_graph
from causal_risk.engine import graph_snapshot, run_counterfactual
from causal_risk.tail_scenarios import generate_tail_scenarios


def test_causal_graph_has_directed_edges():
    graph = graph_snapshot()
    assert len(graph["nodes"]) >= 8
    assert len(graph["edges"]) >= 9
    assert graph["edges"][0]["source"] != graph["edges"][0]["target"]
    assert graph["graph_validation"] == []


def test_counterfactual_is_deterministic_and_explains_paths():
    shock = {"rates": 75, "supply": 60, "oil": 35, "credit": 40, "usd": 15}
    allocation = {"equity": 55, "debt": 30, "gold": 10, "cash": 5}
    first = run_counterfactual(shock, allocation, include_tail_scenarios=True)
    second = run_counterfactual(shock, allocation, include_tail_scenarios=True)
    assert first == second
    assert 0 <= first["systemic_stress"] <= 100
    assert first["explanation"]["primary_path"][-1] == "portfolio"
    assert first["explanation"]["primary_path"] == max(
        (path["path"] for path in first["explanation"]["paths"]),
        key=lambda path: next(
            item["strength"] for item in first["explanation"]["paths"] if item["path"] == path
        ),
    )
    assert first["validation"]["allocation"]["passed"]
    assert first["tail_evaluation"]["status"] == "SCM_EVALUATED"
    assert first["tail_evaluation"]["scenario_count"] == first["tail_scenarios"]["scenario_count"]
    assert first["tail_evaluation"]["summary"]["systemic_stress_p99"] >= first["tail_evaluation"]["summary"]["systemic_stress_p95"]
    assert first["tail_evaluation"]["scenarios"][0]["primary_path"][-1] == "portfolio"


def test_invalid_allocation_is_rejected():
    try:
        run_counterfactual({"rates": 10}, {"equity": 60, "debt": 30})
    except ValueError as exc:
        assert "sum to 100" in str(exc)
    else:
        raise AssertionError("expected invalid allocation to fail")


def test_notears_learns_dag_and_acyclicity():
    rng = np.random.default_rng(42)
    x1 = rng.normal(size=80)
    x2 = 0.8 * x1 + rng.normal(scale=0.2, size=80)
    x3 = 0.6 * x2 + rng.normal(scale=0.2, size=80)
    learned = notears_linear(np.column_stack([x1, x2, x3]), threshold=0.12, max_outer_iter=5)
    assert learned["method"] == "NOTEARS-linear"
    assert learned["status"] == "research_implemented"
    assert learned["acyclicity"] < 0.05


def test_dynamic_discovery_returns_lagged_edges():
    rng = np.random.default_rng(7)
    x = rng.normal(size=(90, 3))
    x[1:, 1] += 0.7 * x[:-1, 0]
    result = discover_lagged_graph(x, lags=1, threshold=0.02)
    assert result["method"].startswith("DYNOTEARS-style")
    assert result["n_samples"] == 90
    assert result["edges"]


def test_tail_sampler_is_reproducible_and_gfn_ready():
    first = generate_tail_scenarios({"rates": 75, "supply": 60}, draws=32, seed=11)
    second = generate_tail_scenarios({"rates": 75, "supply": 60}, draws=32, seed=11)
    assert first == second
    assert first["gfnets_status"] == "interface_ready_not_trained"


def test_combined_graph_discovery_returns_labeled_structural_and_temporal_edges():
    from app.main import app
    from fastapi.testclient import TestClient

    rng = np.random.default_rng(123)
    x1 = rng.normal(size=80)
    x2 = 0.7 * x1 + rng.normal(scale=0.25, size=80)
    x3 = rng.normal(size=80)
    samples = np.column_stack([x1, x2, x3])
    samples[1:, 2] += 0.6 * samples[:-1, 0]

    client = TestClient(app)
    response = client.post(
        "/api/v1/causal-risk/discover/graph",
        json={
            "samples": samples.tolist(),
            "node_ids": ["rates", "credit", "equity"],
            "lags": 1,
            "threshold": 0.05,
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "research_graph_ready"
    assert payload["node_ids"] == ["rates", "credit", "equity"]
    assert payload["contemporaneous"]["status"] == "research_implemented"
    assert payload["temporal"]["status"] == "research_baseline"
    assert all(edge["source"] in payload["node_ids"] for edge in payload["temporal"]["edges"])
    assert all(edge["modality"] == "DYNOTEARS-style-temporal-ridge" for edge in payload["temporal"]["edges"])


def test_combined_graph_discovery_rejects_node_id_length_mismatch():
    from app.main import app
    from fastapi.testclient import TestClient

    samples = np.ones((20, 3)).tolist()
    client = TestClient(app)
    response = client.post(
        "/api/v1/causal-risk/discover/graph",
        json={"samples": samples, "node_ids": ["rates", "credit"]},
    )
    assert response.status_code == 422
    assert "node_ids length" in response.json()["detail"]


def test_market_graph_discovery_requires_multiple_proxies():
    from app.main import app
    from fastapi.testclient import TestClient

    client = TestClient(app)
    response = client.post(
        "/api/v1/causal-risk/discover/market-graph",
        json={"proxies": {"rates": "^TNX"}},
    )
    assert response.status_code == 422
    assert "at least two" in response.json()["detail"]
