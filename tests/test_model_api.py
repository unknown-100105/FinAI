from app.models_api import models, route_preview


def test_model_catalog_includes_provider_metadata():
    payload = models()
    rows = payload["models"]
    gemini = next(row for row in rows if row["model_id"] == "gemini-cloud")

    assert gemini["provider"] == "gemini"
    assert "configured" in gemini
    assert "quality_tier" in gemini
    assert "cost_tier" in gemini


def test_route_preview_returns_auditable_policy():
    result = route_preview(
        {
            "capability": "financial_qa",
            "risk_level": "high",
            "language": "English",
        }
    )

    assert result["capability"] == "financial_qa"
    assert result["risk_level"] == "high"
    assert result["policy"] == "heuristic"
    assert result["fallback_chain"]
