from __future__ import annotations

from typing import Any, Dict, Mapping, Sequence

import numpy as np


def _validate_correlation(correlation: Sequence[Sequence[float]], dimension: int) -> np.ndarray:
    matrix = np.asarray(correlation, dtype=float)
    if matrix.shape != (dimension, dimension):
        raise ValueError("correlation must match the number of shock variables")
    if not np.isfinite(matrix).all():
        raise ValueError("correlation contains non-finite values")
    if not np.allclose(matrix, matrix.T, atol=1e-10):
        raise ValueError("correlation must be symmetric")
    if not np.allclose(np.diag(matrix), np.ones(dimension), atol=1e-8):
        raise ValueError("correlation diagonal entries must equal 1")
    if np.any(matrix < -1.0) or np.any(matrix > 1.0):
        raise ValueError("correlation entries must be between -1 and 1")
    eigenvalues = np.linalg.eigvalsh(matrix)
    if float(np.min(eigenvalues)) < -1e-8:
        raise ValueError("correlation must be positive semidefinite")
    return matrix


def generate_tail_scenarios(
    base_shock: Mapping[str, float],
    *,
    draws: int = 256,
    seed: int = 42,
    scale: float = 0.35,
    correlation: Sequence[Sequence[float]] | None = None,
) -> Dict[str, Any]:
    """Generate reproducible multivariate stress scenarios.

    The default is an independent Gaussian Monte-Carlo baseline. An optional
    correlation matrix preserves cross-factor dependence while retaining
    marginal shock magnitudes derived from the requested scenario. Correlation
    is dimensionless, so empirical return correlations can be transferred to
    the scenario shock scale without mixing units.
    """
    if draws < 8 or draws > 5000:
        raise ValueError("draws must be between 8 and 5000")

    rng = np.random.default_rng(seed)
    keys = tuple(sorted(base_shock))
    if not keys:
        raise ValueError("base_shock must contain at least one factor")
    center = np.asarray([float(base_shock[key]) for key in keys], dtype=float)
    if not np.isfinite(center).all():
        raise ValueError("base_shock contains non-finite values")

    marginal_std = np.maximum(np.abs(center) * scale, 5.0)
    if correlation is None:
        correlation_matrix = np.eye(len(keys), dtype=float)
        dependence_model = "independent_gaussian_baseline"
        correlation_source = "shock_scale"
    else:
        correlation_matrix = _validate_correlation(correlation, len(keys))
        dependence_model = "supplied_correlation_gaussian"
        correlation_source = "caller_supplied"

    covariance_matrix = (
        marginal_std[:, None] * correlation_matrix * marginal_std[None, :]
    )
    samples = rng.multivariate_normal(center, covariance_matrix, size=draws)
    sample_correlation = np.corrcoef(samples, rowvar=False)
    if np.ndim(sample_correlation) == 0:
        sample_correlation = np.asarray([[1.0]])

    stress = np.linalg.norm(
        samples / np.maximum(np.abs(center), 10.0),
        axis=1,
    )
    threshold = float(np.quantile(stress, 0.90))
    tail_mask = stress >= threshold
    tail = samples[tail_mask]
    tail_scores = stress[tail_mask]

    scenarios = [
        {
            "scenario_id": f"tail-{idx + 1:03d}",
            "shock": {
                key: round(float(value), 3)
                for key, value in zip(keys, row)
            },
            "tail_score": round(float(score), 4),
        }
        for idx, (row, score) in enumerate(zip(tail[:20], tail_scores[:20]))
    ]

    return {
        "status": "BASELINE_GENERATED",
        "method": "reproducible multivariate Monte-Carlo tail sampler",
        "dependence_model": dependence_model,
        "correlation_source": correlation_source,
        "gfnets_status": "interface_ready_not_trained",
        "draws": draws,
        "tail_quantile": 0.90,
        "scenario_count": len(scenarios),
        "generated_correlation": [
            [round(float(value), 4) for value in row]
            for row in np.atleast_2d(sample_correlation)
        ],
        "scenarios": scenarios,
    }
