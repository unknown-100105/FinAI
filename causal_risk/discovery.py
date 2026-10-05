from __future__ import annotations

from typing import Any, Dict, Sequence

import numpy as np
from scipy.linalg import expm
from scipy.optimize import minimize


MAX_ROWS = 5_000
MAX_VARIABLES = 100


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
    max_abs_weight: float = 2.0,
    rho_growth: float = 4.0,
    rho_max: float = 1e6,
    h_tolerance: float = 1e-8,
) -> Dict[str, Any]:
    """Learn a bounded linear DAG with the NOTEARS augmented-Lagrangian objective.

    W[i, j] represents a directed effect from variable i to variable j.
    The implementation is a compact research baseline. It reports optimizer
    diagnostics and bounds weights to reduce numerical overflow in expm(W*W).
    """
    X = np.asarray(samples, dtype=float)
    if X.ndim != 2 or X.shape[0] < 8 or X.shape[1] < 2:
        raise ValueError(
            "samples must be a 2-D matrix with at least 8 rows and 2 variables"
        )
    if X.shape[0] > MAX_ROWS:
        raise ValueError(f"samples exceed the maximum of {MAX_ROWS} rows")
    if X.shape[1] > MAX_VARIABLES:
        raise ValueError(f"samples exceed the maximum of {MAX_VARIABLES} variables")
    if not np.isfinite(X).all():
        raise ValueError("samples contain non-finite values")
    if lambda1 < 0:
        raise ValueError("lambda1 must be non-negative")
    if threshold < 0:
        raise ValueError("threshold must be non-negative")
    if max_outer_iter < 1 or max_inner_iter < 1:
        raise ValueError("optimization iteration limits must be positive")
    if max_abs_weight <= 0 or max_abs_weight > 5:
        raise ValueError("max_abs_weight must be between 0 and 5")
    if rho_growth <= 1.0 or rho_growth > 10.0:
        raise ValueError("rho_growth must be between 1 and 10")
    if rho_max <= 1.0:
        raise ValueError("rho_max must be greater than 1")
    if h_tolerance <= 0:
        raise ValueError("h_tolerance must be positive")

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

    bounds = [(-float(max_abs_weight), float(max_abs_weight))] * (d * d)
    outer_iterations = 0
    final_result = None
    h_history: list[float] = []
    rho_history: list[float] = []
    previous_h = float("inf")
    for outer in range(max_outer_iter):
        outer_iterations = outer + 1
        final_result = minimize(
            lambda flat: objective_flat(flat),
            W.reshape(-1),
            jac=True,
            method="L-BFGS-B",
            bounds=bounds,
            options={"maxiter": max_inner_iter, "ftol": 1e-8},
        )
        if not np.isfinite(final_result.x).all():
            raise ValueError("NOTEARS optimizer produced non-finite weights")
        W = final_result.x.reshape(d, d)
        np.fill_diagonal(W, 0.0)
        h_val = max(0.0, _h(W))
        h_history.append(float(h_val))
        rho_history.append(float(rho))
        alpha += rho * h_val
        if h_val <= h_tolerance:
            break
        # Gradually increase the augmented-Lagrangian penalty rather than
        # multiplying it by 10 every iteration. This reduces overshooting in
        # wide/poorly-scaled problems while retaining pressure toward a DAG.
        improved = previous_h == float("inf") or h_val < previous_h * 0.95
        if not improved:
            rho = min(rho * rho_growth, rho_max)
        else:
            rho = min(rho * max(1.25, rho_growth ** 0.5), rho_max)
        previous_h = h_val
        if rho >= rho_max and len(h_history) >= 3:
            recent = h_history[-3:]
            if max(recent) - min(recent) < max(h_tolerance * 10, 1e-7):
                break

    W[np.abs(W) < threshold] = 0.0
    acyclicity = _h(W)
    order = []
    remaining = set(range(d))
    while remaining:
        candidate = min(
            remaining,
            key=lambda j: np.count_nonzero(W[list(remaining), j]),
        )
        order.append(candidate)
        remaining.remove(candidate)

    optimizer_success = bool(final_result.success) if final_result is not None else False
    optimizer_status = int(final_result.status) if final_result is not None else -1
    optimizer_message = str(final_result.message) if final_result is not None else "not_run"

    return {
        "adjacency": W.tolist(),
        "acyclicity": round(acyclicity, 8),
        "n_samples": n,
        "n_variables": d,
        "topological_order": order,
        "threshold": threshold,
        "max_abs_weight": max_abs_weight,
        "optimizer": {
            "success": optimizer_success,
            "status": optimizer_status,
            "message": optimizer_message,
            "outer_iterations": outer_iterations,
            "rho_growth": rho_growth,
            "rho_max": rho_max,
            "rho_history": rho_history,
            "acyclicity_history": h_history,
            "acyclicity_converged": bool(acyclicity <= h_tolerance),
        },
        "method": "NOTEARS-linear",
        "status": "research_implemented",
        "research_boundary": (
            "Adaptive augmented-Lagrangian penalty growth improves numerical "
            "robustness but does not solve confounding, temporal feedback, or "
            "causal identification."
        ),
    }
