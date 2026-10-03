import numpy as np


def test_multimodal_ingestion_builds_provenance_nodes_and_edges():
    from causal_risk.multimodal_ingestion import (
        build_document_nodes,
        build_event_nodes,
        build_portfolio_edges,
        build_relation_edges,
    )

    docs = build_document_nodes([{
        "id": "filing-1",
        "type": "10K",
        "text": "supply risk",
        "embedding": [0.1, 0.2],
        "source": "sec",
    }])
    events = build_event_nodes([{
        "id": "event-1",
        "type": "supply_disruption",
        "severity": 0.8,
        "source": "news",
    }])
    edges = build_relation_edges([{
        "source": "event-1",
        "target": "filing-1",
        "relation": "affects",
        "weight": 0.7,
        "modality": "event",
        "source_document": "news-1",
    }])
    exposures = build_portfolio_edges([{
        "factor": "rates",
        "asset": "bond-fund",
        "weight": 0.3,
    }])
    assert docs[0].provenance == "sec"
    assert events[0].modality == "event"
    assert edges[0].provenance == "news-1"
    assert exposures[0].relation == "portfolio_exposure"


def test_text_graph_alignment_is_deterministic():
    from causal_risk.llm_alignment import align_text_to_graph

    result = align_text_to_graph(
        [1.0, 0.0],
        {"rates": [1.0, 0.0], "oil": [0.0, 1.0]},
    )
    assert result["status"] == "TEXT_GRAPH_ALIGNMENT_READY"
    assert result["matches"][0]["node_id"] == "rates"
    assert np.isclose(result["matches"][0]["similarity"], 1.0)


def test_text_graph_alignment_does_not_claim_causality():
    from causal_risk.llm_alignment import align_text_to_graph

    result = align_text_to_graph([1.0, 0.0], {"rates": [1.0, 0.0]})
    assert "causality" in result["semantics"].lower()
