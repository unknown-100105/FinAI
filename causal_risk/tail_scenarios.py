from __future__ import annotations

from typing import Any, Dict, Mapping, Sequence

import numpy as np


def generate_tail_scenarios(
    base_shock: Mapping[str, float],
    *,
    draws: int = 256,
    seed: int = 42,
    scale: float = 0.35,
) -> Dict[str, Any]:
    """Generate reproducible multivariate stress scenarios.

    This is the calibrated Monte-Carlo baseline behind the future GFlowNet
    interface. It deliberately does not claim to be a trained GFlowNet.
    """
    if draws < 8 or draws > 5000:
        raise ValueError("draws must be between 8 and 5000")
    rng = np.random.default_rng(seed)
    keys = tuple(sorted(base_shock))
    center = np.asarray([float(base_shock[key]) for key in keys], dtype=float)
    covariance = np.diag(np.maximum(np.abs(center) * scale, 5.0) ** 2)
    samples = rng.multivariate_normal(center, covariance, size=draws)
    stress = np.linalg.norm(samples / np.maximum(np.abs(center), 10.0), axis=1)
    threshold = float(np.quantile(stress, 0.90))
    tail = samples[stress >= threshold]
    scenarios = [
        {
            "scenario_id": f"tail-{idx + 1:03d}",
            "shock": {key: round(float(value), 3) for key, value in zip(keys, row)},
            "tail_score": round(float(score), 4),
        }
        for idx, (row, score) in enumerate(zip(tail[:20], stress[stress >= threshold][:20]))
    ]
    return {
        "status": "BASELINE_GENERATED",
        "method": "reproducible Monte-Carlo tail sampler",
        "gfnets_status": "interface_ready_not_trained",
        "draws": draws,
        "tail_quantile": 0.90,
        "scenario_count": len(scenarios),
        "scenarios": scenarios,
    }
