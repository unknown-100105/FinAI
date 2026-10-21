import pytest
from pydantic import ValidationError


def test_risk_calibration_rejects_nan_matrix_values():
    from app.advanced_causal_api import RiskCalibrationRequest

    with pytest.raises(ValidationError):
        RiskCalibrationRequest(
            samples=[[float("nan"), 0.0] for _ in range(60)],
            target=[0.0] * 60,
            feature_names=["rates", "credit"],
        )


def test_multimodal_training_rejects_infinite_features():
    from app.advanced_causal_api import MultimodalTrainRequest

    with pytest.raises(ValidationError):
        MultimodalTrainRequest(
            inputs={"market": [[float("inf"), 1.0]]}
        )


def test_research_counterfactual_rejects_nan_shock():
    from app.advanced_causal_api import ResearchCounterfactualRequest

    with pytest.raises(ValidationError):
        ResearchCounterfactualRequest(
            shock={"rates": float("nan")},
            allocation={"equity": 55, "debt": 30, "gold": 10, "cash": 5},
            nodes=["rates"],
            edges=[],
        )


def test_experimental_epcrp_rejects_nan_edge_coefficient():
    from app.patent_mechanism_api import EPCRPEvaluateRequest

    with pytest.raises(ValidationError):
        EPCRPEvaluateRequest(
            nodes=[{"name": "A"}, {"name": "B"}],
            edges=[{
                "source": "A",
                "target": "B",
                "coefficient": float("nan"),
            }],
            interventions={"A": 1.0},
            portfolio_exposures={"B": 1.0},
            as_of="2026-10-13T00:00:00Z",
        )


def test_screening_request_rejects_infinite_nested_interval():
    from app.patent_mechanism_api import ScreeningRequest

    with pytest.raises(ValidationError):
        ScreeningRequest(
            nodes=[{
                "name": "A",
                "domain": {"low": 0.0, "high": 1.0},
            }],
            target="A",
            target_interval={"low": 0.0, "high": float("inf")},
        )
