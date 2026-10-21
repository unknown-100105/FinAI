from __future__ import annotations

import math
from typing import Any, Dict, Mapping


def validate_allocation(allocation: Mapping[str, float]) -> Dict[str, Any]:
    values: Dict[str, float] = {}
    errors = []

    for key, value in allocation.items():
        try:
            numeric = float(value)
        except (TypeError, ValueError, OverflowError):
            errors.append(f"non-numeric allocation: {key}")
            continue

        if not math.isfinite(numeric):
            errors.append(f"non-finite allocation: {key}")
            continue

        values[key] = numeric

    total = sum(values.values())

    for key, value in values.items():
        if value < 0:
            errors.append(f"{key} allocation cannot be negative")

    if not math.isfinite(total):
        errors.append("allocation total must be finite")
        total_percent = None
    else:
        if abs(total - 100.0) > 0.01:
            errors.append(f"allocation must sum to 100; received {total:.4f}")
        total_percent = round(total, 4)

    return {
        "passed": not errors,
        "errors": errors,
        "total_percent": total_percent,
        "checked": [
            "finite_numeric_weights",
            "non_negative_weights",
            "allocation_sum_100",
        ],
    }


def validate_shocks(shock: Mapping[str, float], allowed: tuple[str, ...]) -> Dict[str, Any]:
    errors = []

    for key, value in shock.items():
        if key not in allowed:
            errors.append(f"unknown intervention variable: {key}")

        try:
            numeric = float(value)
        except (TypeError, ValueError, OverflowError):
            errors.append(f"non-numeric shock: {key}")
            continue

        if not math.isfinite(numeric):
            errors.append(f"non-finite shock: {key}")
            continue

        if abs(numeric) > 150:
            errors.append(f"shock outside research bounds \u00b1150: {key}")

    return {"passed": not errors, "errors": errors}
