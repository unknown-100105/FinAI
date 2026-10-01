from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RiskDriver:
    name: str
    contribution: float
    explanation: str


@dataclass(frozen=True)
class RiskExplanation:
    risk_score: float
    risk_level: str
    drivers: tuple[RiskDriver, ...]


def classify_risk(score: float) -> str:
    if score < 33:
        return "low"

    if score < 66:
        return "medium"

    return "high"


def build_risk_explanation(
    concentration_score: float,
    volatility_score: float = 0.0,
    drawdown_score: float = 0.0,
) -> RiskExplanation:

    raw = {
        "concentration": max(0.0, concentration_score),
        "volatility": max(0.0, volatility_score),
        "drawdown": max(0.0, drawdown_score),
    }

    total = sum(raw.values())

    if total == 0:
        drivers = ()
        score = 0.0
    else:
        score = min(100.0, total / 3.0)

        drivers = tuple(
            RiskDriver(
                name=name,
                contribution=value / total,
                explanation=f"{name.replace('_', ' ').title()} contributed to portfolio risk.",
            )
            for name, value in sorted(
                raw.items(),
                key=lambda item: item[1],
                reverse=True,
            )
            if value > 0
        )

    return RiskExplanation(
        risk_score=score,
        risk_level=classify_risk(score),
        drivers=drivers,
    )