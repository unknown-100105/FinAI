from app import causal_risk_api


def test_counterfactual_falls_back_when_empirical_dependence_is_unavailable(monkeypatch):
    def unavailable(_shock):
        raise ValueError("empirical market correlation is unavailable")

    monkeypatch.setattr(causal_risk_api, "_empirical_correlation_for_shock", unavailable)
    monkeypatch.setattr(
        causal_risk_api,
        "run_counterfactual",
        lambda *args, **kwargs: {"status": "COUNTERFACTUAL_READY"},
    )

    request = causal_risk_api.CounterfactualRequest(
        shock={"rates": 75.0, "credit": 40.0},
        allocation={"equity": 55.0, "debt": 30.0, "gold": 10.0, "cash": 5.0},
        include_tail_scenarios=True,
        use_empirical_tail_dependence=True,
        tail_distribution="student_t_copula",
        tail_degrees_of_freedom=5.0,
    )

    result = causal_risk_api.counterfactual(request)

    assert result["status"] == "COUNTERFACTUAL_READY"
    assert result["tail_dependence"]["status"] == "FALLBACK"
    assert result["tail_dependence"]["used_empirical"] is False
    assert "empirical market correlation is unavailable" in result["tail_dependence"]["reason"]
