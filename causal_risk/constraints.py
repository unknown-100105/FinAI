from __future__ import annotations

from typing import Any, Dict, Mapping


def validate_allocation(allocation: Mapping[str, float]) -> Dict[str, Any]:
    values = {key: float(value) for key, value in allocation.items()}
    total = sum(values.values())
    errors = [f"{key} allocation cannot be negative" for key, value in values.items() if value < 0]
    if abs(total - 100.0) > 0.01:
        errors.append(f"allocation must sum to 100; received {total:.4f}")
    return {
        "passed": not errors,
        "errors": errors,
        "total_percent": round(total, 4),
        "checked": ["non_negative_weights", "allocation_sum_100"],
    }


def validate_shocks(shock: Mapping[str, float], allowed: tuple[str, ...]) -> Dict[str, Any]:
    errors = []
    for key, value in shock.items():
        if key not in allowed:
            errors.append(f"unknown intervention variable: {key}")
        try:
            numeric = float(value)
        except (TypeError, ValueError):
            errors.append(f"non-numeric shock: {key}")
            continue
        if abs(numeric) > 150:
            errors.append(f"shock outside research bounds ±150: {key}")
    return {"passed": not errors, "errors": errors}
