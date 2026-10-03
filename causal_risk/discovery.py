from __future__ import annotations

from typing import Any, Dict, Sequence

import numpy as np
from scipy.linalg import expm
from scipy.optimize import minimize


def _standardize(x: np.ndarray) -> np.ndarray:
    centered = x - np.mean(x, axis=0, keepdims=True)
    scale = np.std(centered, axis=0, keepdims=True)
    return centered / np.where(scale < 1e-12, 1.0, scale)


def _h(W: np.ndarray) -> float:
    d = W.shape[0]
    return float(np.trace(expm(W * W)) - d)


def notears_linear(
    samples: Sequence[Sequence[float]],
    *,
    lambda1: float = 0.02,
    max_outer_iter: int = 12,
    max_inner_iter: int = 120,
    threshold: float = 0.10,
) -> Dict[str, Any]:
    """Learn a linear DAG with the NOTEARS augmented-Lagrangian objective.

    W[i, j] represents a directed effect from variable i to variable j.
    This implementation is intentionally small and dependency-light for FinAI
    research use; it is not a substitute for a production causal-identification
    pipeline with validated assumptions and domain constraints.
    """
    X = np.asarray(samples, dtype=float)
    if X.ndim != 2 or X.shape[0] < 8 or X.shape[1] < 2:
        raise ValueError("samples must be a 2-D matrix with at least 8 rows and 2 variables")
    if not np.isfinite(X).all():
        raise ValueError("samples contain non-finite values")

    X = _standardize(X)
    n, d = X.shape
    W = np.zeros((d, d), dtype=float)
    rho = 1.0
    alpha = 0.0

    def objective_flat(w_flat: np.ndarray) -> tuple[float, np.ndarray]:
        w = w_flat.reshape(d, d)
        residual = X - X @ w
        loss = 0.5 / n * float(np.sum(residual * residual))
        grad = -(X.T @ residual) / n
        h_val = _h(w)
        h_grad = 2.0 * w * expm(w * w).T
        value = loss + lambda1 * float(np.sum(np.abs(w)))
        value += 0.5 * rho * h_val * h_val + alpha * h_val
        grad = grad + rho * h_val * h_grad + alpha * h_grad
        np.fill_diagonal(grad, 0.0)
        return value, grad.reshape(-1)

    for _ in range(max_outer_iter):
        result = minimize(
            lambda flat: objective_flat(flat),
            W.reshape(-1),
            jac=True,
            method="L-BFGS-B",
            options={"maxiter": max_inner_iter, "ftol": 1e-8},
        )
        W = result.x.reshape(d, d)
        np.fill_diagonal(W, 0.0)
        h_val = _h(W)
        alpha += rho * h_val
        if h_val <= 1e-8:
            break
        rho *= 10.0

    W[np.abs(W) < threshold] = 0.0
    order = []
    # Topological order is used only for presentation; the optimization enforces
    # acyclicity in the continuous objective.
    remaining = set(range(d))
    while remaining:
        candidate = min(remaining, key=lambda j: np.count_nonzero(W[list(remaining), j]))
        order.append(candidate)
        remaining.remove(candidate)

    return {
        "adjacency": W.tolist(),
        "acyclicity": round(_h(W), 8),
        "n_samples": n,
        "n_variables": d,
        "topological_order": order,
        "threshold": threshold,
        "method": "NOTEARS-linear",
        "status": "research_implemented",
    }
