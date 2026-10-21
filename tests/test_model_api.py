from app.models_api import models, route_preview, resources


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
            "data_sensitivity": "standard",
        }
    )

    assert result["capability"] == "financial_qa"
    assert result["risk_level"] == "high"
    assert result["policy"] == "heuristic"
    assert result["fallback_chain"]

def test_route_preview_enforces_offline_constraints():
    result = route_preview(
        {
            "capability": "financial_qa",
            "risk_level": "medium",
            "language": "English",
            "network_mode": "offline",
        }
    )
    assert result["provider"] == "local"
    assert result["reason"] == "offline_local_only"
    assert result["network_mode"] == "offline"


def test_resource_api_exposes_hardware_and_local_model_fit():
    result = resources()
    assert "hardware" in result
    assert "cpu_cores" in result["hardware"]
    assert "ram_gb" in result["hardware"]
    assert "vram_gb" in result["hardware"]
    assert "local_models" in result
    assert result["local_models"]
    assert "resource" in result["local_models"][0]


def test_route_preview_defaults_to_restricted_data_sensitivity(monkeypatch):
    observed = {}

    class FakeRoute:
        def to_dict(self):
            return {"provider": "local", "data_sensitivity": observed["data_sensitivity"]}

    def fake_route(self, **kwargs):
        observed.update(kwargs)
        return FakeRoute()

    monkeypatch.setattr("app.models_api.ModelRouter.route", fake_route)
    result = route_preview({"capability": "financial_qa"})

    assert observed["data_sensitivity"] == "restricted"
    assert result["provider"] == "local"
