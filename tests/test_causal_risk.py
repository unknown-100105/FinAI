from causal_risk.engine import graph_snapshot, run_counterfactual

def test_causal_graph_has_directed_edges():
    graph=graph_snapshot()
    assert len(graph["nodes"]) >= 8
    assert len(graph["edges"]) >= 9
    assert graph["edges"][0]["source"] != graph["edges"][0]["target"]

def test_counterfactual_is_deterministic():
    shock={"rates":75,"supply":60,"oil":35,"credit":40,"usd":15}
    allocation={"equity":55,"debt":30,"gold":10,"cash":5}
    first=run_counterfactual(shock,allocation)
    second=run_counterfactual(shock,allocation)
    assert first == second
    assert 0 <= first["systemic_stress"] <= 100
