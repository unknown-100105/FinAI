from __future__ import annotations

from typing import Any, Mapping, Sequence

import numpy as np
from scipy.stats import t as student_t


def _validate_correlation(
    correlation: Sequence[Sequence[float]],
    dimension: int,
) -> np.ndarray:
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
    if float(np.min(np.linalg.eigvalsh(matrix))) < -1e-8:
        raise ValueError("correlation must be positive semidefinite")
    return matrix


def _sample_student_t_copula(
    rng: np.random.Generator,
    correlation: np.ndarray,
    draws: int,
    degrees_of_freedom: float,
) -> np.ndarray:
    if degrees_of_freedom <= 2:
        raise ValueError("degrees_of_freedom must be greater than 2")
    latent = rng.multivariate_normal(
        np.zeros(correlation.shape[0]),
        correlation,
        size=draws,
    )
    scale = np.sqrt(
        rng.chisquare(degrees_of_freedom, size=draws)
        / degrees_of_freedom
    )
    latent = latent / scale[:, None]
    # Convert correlated t variates back to uniforms, preserving copula
    # dependence while providing heavy-tailed marginal shocks.
    uniforms = student_t.cdf(latent, df=degrees_of_freedom)
    return student_t.ppf(uniforms, df=degrees_of_freedom)


def generate_tail_scenarios(
    base_shock: Mapping[str, float],
    *,
    draws: int = 256,
    seed: int = 42,
    scale: float = 0.35,
    correlation: Sequence[Sequence[float]] | None = None,
    distribution: str = "gaussian",
    degrees_of_freedom: float = 5.0,
) -> Dict[str, Any]:
    """Generate reproducible multivariate tail scenarios.

    The default preserves the original independent Gaussian baseline. When a
    correlation matrix is supplied, dependence is preserved across shock
    factors. A Student-t copula option adds heavier-tailed dependence for
    research stress testing. Neither mode is a trained GFlowNet.
    """
    if draws < 8 or draws > 5000:
        raise ValueError("draws must be between 8 and 5000")
    distribution = str(distribution).strip().lower()
    if distribution not in {"gaussian", "student_t_copula"}:
        raise ValueError("distribution must be 'gaussian' or 'student_t_copula'")

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
        correlation_source = "shock_scale"
    else:
        correlation_matrix = _validate_correlation(correlation, len(keys))
        correlation_source = "caller_supplied"

    if distribution == "student_t_copula":
        standardized = _sample_student_t_copula(
            rng,
            correlation_matrix,
            draws,
            degrees_of_freedom,
        )
        samples = center + standardized * marginal_std
        dependence_model = "student_t_copula"
    else:
        covariance_matrix = (
            marginal_std[:, None]
            * correlation_matrix
            * marginal_std[None, :]
        )
        samples = rng.multivariate_normal(
            center,
            covariance_matrix,
            size=draws,
        )
        dependence_model = (
            "independent_gaussian_baseline"
            if correlation is None
            else "correlated_gaussian"
        )

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
        for idx, (row, score) in enumerate(
            zip(tail[:20], tail_scores[:20])
        )
    ]

    return {
        "status": "BASELINE_GENERATED",
        "method": "reproducible multivariate tail sampler",
        "dependence_model": dependence_model,
        "correlation_source": correlation_source,
        # Backward-compatible field retained for clients/tests that still
        # describe the independent baseline in covariance terms.
        "covariance_source": correlation_source,
        "distribution": distribution,
        "degrees_of_freedom": (
            float(degrees_of_freedom)
            if distribution == "student_t_copula"
            else None
        ),
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
