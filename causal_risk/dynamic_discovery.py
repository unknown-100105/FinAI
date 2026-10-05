from __future__ import annotations

from typing import Any, Dict, Sequence

import numpy as np
from sklearn.linear_model import Ridge


def discover_lagged_graph(
    samples: Sequence[Sequence[float]],
    *,
    lags: int = 1,
    alpha: float = 1.0,
    threshold: float = 0.08,
) -> Dict[str, Any]:
    """DYNOTEARS-style lagged causal screening.

    For each target at time t, estimate effects from variables at t-1..t-lags.
    The result is a temporal edge matrix. Full constrained DYNOTEARS is kept as
    a future research extension; this component provides a reproducible temporal
    baseline for the FinAI causal stack.
    """
    X = np.asarray(samples, dtype=float)
    if X.ndim != 2 or X.shape[0] <= lags + 8:
        raise ValueError("insufficient time-series samples")
    if lags < 1:
        raise ValueError("lags must be >= 1")
    if not np.isfinite(X).all():
        raise ValueError("samples contain non-finite values")

    n, d = X.shape
    features = []
    targets = X[lags:]
    for lag in range(1, lags + 1):
        features.append(X[lags - lag : n - lag])
    Z = np.concatenate(features, axis=1)

    coeff = np.zeros((lags, d, d), dtype=float)
    for target_idx in range(d):
        model = Ridge(alpha=alpha)
        model.fit(Z, targets[:, target_idx])
        raw = model.coef_.reshape(lags, d)
        coeff[:, :, target_idx] = raw

    coeff[np.abs(coeff) < threshold] = 0.0

    edges = []
    for lag_idx in range(lags):
        for src in range(d):
            for dst in range(d):
                weight = float(coeff[lag_idx, src, dst])
                if weight:
                    edges.append(
                        {
                            "source": src,
                            "target": dst,
                            "lag": lag_idx + 1,
                            "weight": round(weight, 6),
                        }
                    )

    return {
        "lagged_coefficients": coeff.tolist(),
        "edges": edges,
        "n_samples": n,
        "n_variables": d,
        "lags": lags,
        "method": "DYNOTEARS-style temporal ridge screening",
        "status": "research_baseline",
    }
