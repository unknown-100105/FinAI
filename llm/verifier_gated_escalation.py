"""Bounded policy for verifier-gated model escalation.

The caller supplies candidates that have already passed the application's model
routing policy. This module deliberately does not select providers or bypass
privacy/network restrictions.
"""
from __future__ import annotations

from typing import Any, Callable, Iterable
import time


def verifier_gated_escalate(
    *,
    candidates: Iterable[str],
    generate: Callable[[str], dict[str, Any]],
    verify: Callable[[str], tuple[dict[str, Any], dict[str, Any]]],
    max_attempts: int = 1,
) -> dict[str, Any]:
    """Try a bounded list of pre-approved models; accept only verified answers."""
    limit = max(0, min(int(max_attempts), 2))
    trace: list[dict[str, Any]] = []
    attempts = 0
    for model_id in candidates:
        if attempts >= limit:
            break
        attempts += 1
        started = time.perf_counter()
        try:
            generated = generate(model_id)
            if not isinstance(generated, dict):
                raise TypeError("model adapter must return a dict")
            response = str(generated.get("response", "")).strip()
            verification, claim_verification = verify(response)
            passed = (
                not verification.get("applicable", False)
                or verification.get("passed", False)
            ) and (
                not claim_verification.get("applicable", False)
                or claim_verification.get("passed", False)
            )
            trace.append({
                "model_id": model_id,
                "status": "accepted" if passed else "verification_failed",
                "verification_passed": bool(verification.get("passed", True)),
                "claim_verification_passed": bool(claim_verification.get("passed", True)),
                "latency_ms": round((time.perf_counter() - started) * 1000.0, 3),
            })
            if passed:
                generated["model_id"] = model_id
                generated["status"] = "GENERATED_VERIFIED_ESCALATED"
                generated["verification"] = verification
                generated["claim_verification"] = claim_verification
                generated["verification_escalation"] = {
                    "attempted": True,
                    "accepted": True,
                    "to_model": model_id,
                    "attempt_count": attempts,
                    "total_latency_ms": round(
                        sum(float(item.get("latency_ms", 0.0)) for item in trace), 3
                    ),
                    "trace": trace,
                }
                return generated
        except Exception as exc:
            trace.append({
                "model_id": model_id,
                "status": "generation_failed",
                "error_type": type(exc).__name__,
                "latency_ms": round((time.perf_counter() - started) * 1000.0, 3),
            })
    return {
        "verification_escalation": {
            "attempted": attempts > 0,
            "accepted": False,
            "attempt_count": attempts,
            "total_latency_ms": round(
                sum(float(item.get("latency_ms", 0.0)) for item in trace), 3
            ),
            "trace": trace,
        }
    }
