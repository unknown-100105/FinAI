import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional


TRACE_DIR = Path("xai/traces")


class XAITrace:

    def __init__(self, session_id: str):
        self.session_id = session_id
        self.started_at = datetime.now().isoformat()

        self.data = {
            "trace_id": self._make_trace_id(),
            "session_id": session_id,
            "started_at": self.started_at,
            "completed_at": None,

            "user_input": None,

            "router": {
                "intent": None,
                "raw_prediction": None,
                "confidence": None,
                "margin": None,
                "decision": None,
                "reason": None,
                "top_k": [],
            },

            "policy": {
                "status": None,
                "risk_level": None,
                "authentication_required": None,
                "confirmation_required": None,
                "tool": None,
            },

            "session": {
                "authenticated": False,
                "awaiting_authentication": False,
                "awaiting_confirmation": False,
                "pending_intent": None,
                "pending_tool": None,
            },

            "tool": {
                "name": None,
                "executed": False,
                "success": None,
                "message": None,
                "data": {},
            },

            "model": {
                "model_id": None,
                "status": None,
                "capability": None,
                "source": None,
                "language": None,
                "persona": None,
                "metrics": {},
            },

            "claims": {
                "items": [],
                "total_count": 0,
                "authoritative_count": 0,
                "all_verified": False,
            },

            "final": {
                "stage": None,
                "status": None,
                "message": None,
            },
        }

    def _make_trace_id(self) -> str:
        return (
            f"{self.session_id}-"
            f"{datetime.now().strftime('%Y%m%d%H%M%S%f')}"
        )

    def set_user_input(self, text: str):
        self.data["user_input"] = str(text)

    def record_router(self, router_result: Optional[Dict[str, Any]]):
        if not router_result:
            return

        self.data["router"] = {
            "intent": self._safe_value(
                router_result.get("intent")
            ),
            "raw_prediction": self._safe_value(
                router_result.get("raw_prediction")
            ),
            "confidence": self._safe_float(
                router_result.get("confidence")
            ),
            "margin": self._safe_float(
                router_result.get("margin")
            ),
            "decision": self._safe_value(
                router_result.get("decision")
            ),
            "reason": self._safe_value(
                router_result.get("reason")
            ),
            "top_k": self._clean_top_k(
                router_result.get("top_k", [])
            ),
        }

    def record_policy(self, policy_result: Optional[Dict[str, Any]]):
        if not policy_result:
            return

        self.data["policy"] = {
            "status": self._safe_value(
                policy_result.get("status")
            ),
            "risk_level": self._safe_value(
                policy_result.get("risk_level")
            ),
            "authentication_required": bool(
                policy_result.get(
                    "authentication_required",
                    False
                )
            ),
            "confirmation_required": bool(
                policy_result.get(
                    "confirmation_required",
                    False
                )
            ),
            "tool": self._safe_value(
                policy_result.get("tool")
            ),
        }

    def record_session(self, session_snapshot: Optional[Dict[str, Any]]):
        if not session_snapshot:
            return

        self.data["session"] = {
            "authenticated": bool(
                session_snapshot.get(
                    "authenticated",
                    False
                )
            ),
            "awaiting_authentication": bool(
                session_snapshot.get(
                    "awaiting_authentication",
                    False
                )
            ),
            "awaiting_confirmation": bool(
                session_snapshot.get(
                    "awaiting_confirmation",
                    False
                )
            ),
            "pending_intent": self._safe_value(
                session_snapshot.get(
                    "pending_intent"
                )
            ),
            "pending_tool": self._safe_value(
                session_snapshot.get(
                    "pending_tool"
                )
            ),
        }

    def record_tool(self, tool_result: Optional[Dict[str, Any]]):
        if not tool_result:
            return

        self.data["tool"] = {
            "name": self._safe_value(
                tool_result.get("tool")
            ),
            "executed": True,
            "success": bool(
                tool_result.get("success", False)
            ),
            "message": self._safe_value(
                tool_result.get("message")
            ),
            "data": self._clean_value(
                tool_result.get("data", {})
            ),
        }

    def record_model(self, model_result: Optional[Dict[str, Any]]):

        if not model_result:
            return

        selection = model_result.get("selection") or {}

        self.data["model"] = {
            "model_id": self._safe_value(
                model_result.get("model_id")
            ),
            "status": self._safe_value(
                model_result.get("status")
            ),
            "capability": self._safe_value(
                selection.get("capability")
            ),
            "source": self._safe_value(
                model_result.get("source")
            ),
            "language": self._safe_value(
                model_result.get("language")
            ),
            "persona": self._safe_value(
                model_result.get("persona")
            ),
            "metrics": self._clean_value(
                model_result.get("metrics", {})
            ),
        }

    def record_response_generation(
        self,
        response_generation: Optional[Dict[str, Any]],
    ):

        if not response_generation:
            return

        self.record_model(response_generation)

        claim_verification = (
            response_generation.get(
                "claim_verification"
            )
            or {}
        )

        claims = claim_verification.get(
            "claims",
            [],
        )

        report = (
            claim_verification.get(
                "report"
            )
            or {}
        )

        verification_passed = bool(
            claim_verification.get(
                "passed",
                False,
            )
        )

        trace_claims = self._clean_value(
            claims
        )

        if verification_passed:
            for claim in trace_claims:
                if isinstance(claim, dict):
                    claim["verification_status"] = (
                        "VERIFIED"
                    )

                    metadata = claim.get(
                        "metadata"
                    )

                    if not isinstance(
                        metadata,
                        dict,
                    ):
                        metadata = {}

                    metadata[
                        "verified_against"
                    ] = (
                        "response_verification"
                    )

                    claim["metadata"] = metadata

        self.data["claims"] = {
            "items": trace_claims,
            "total_count": len(trace_claims),
            "authoritative_count": 0,
            "all_verified": (
                verification_passed
                and bool(trace_claims)
            ),
            "verification": {
                "applicable": bool(
                    claim_verification.get(
                        "applicable",
                        False,
                    )
                ),
                "passed": bool(
                    claim_verification.get(
                        "passed",
                        False,
                    )
                ),
                "report": self._clean_value(
                    report
                ),
            },
        }

    def record_claims(self, claim_set: Optional[Any]):

        if not claim_set:
            return

        if not hasattr(claim_set, "to_dict"):
            raise TypeError(
                "record_claims expects a ClaimSet-like object "
                "with to_dict()."
            )

        items = claim_set.to_dict()

        authoritative_count = 0

        if hasattr(claim_set, "authoritative_claims"):
            authoritative_count = len(
                claim_set.authoritative_claims()
            )

        all_verified = False

        if hasattr(claim_set, "all_verified"):
            all_verified = bool(
                claim_set.all_verified()
            )

        self.data["claims"] = {
            "items": self._clean_value(items),
            "total_count": len(items),
            "authoritative_count": authoritative_count,
            "all_verified": all_verified,
        }

    def record_final(
        self,
        stage: Optional[str],
        status: Optional[str],
        message: Optional[str],
    ):

        self.data["final"] = {
            "stage": self._safe_value(stage),
            "status": self._safe_value(status),
            "message": self._safe_value(message),
        }

    def complete(self):
        self.data["completed_at"] = datetime.now().isoformat()

    def save(self) -> Path:

        self.complete()

        TRACE_DIR.mkdir(
            parents=True,
            exist_ok=True
        )

        trace_id = str(self.data["trace_id"])

        path = TRACE_DIR / f"{trace_id}.json"

        with open(
            path,
            "w",
            encoding="utf-8"
        ) as f:

            json.dump(
                self.data,
                f,
                indent=2,
                ensure_ascii=False
            )

        return path

    @staticmethod
    def _safe_value(value):

        if value is None:
            return None

        return str(value)

    @staticmethod
    def _safe_float(value):

        if value is None:
            return None

        try:
            return float(value)
        except (TypeError, ValueError):
            return None

    @classmethod
    def _clean_value(cls, value):

        if value is None:
            return None

        if isinstance(value, dict):
            return {
                str(k): cls._clean_value(v)
                for k, v in value.items()
            }

        if isinstance(value, (list, tuple)):
            return [
                cls._clean_value(v)
                for v in value
            ]

        if isinstance(value, (str, int, float, bool)):
            return value

        return str(value)

    @classmethod
    def _clean_top_k(cls, values):

        cleaned = []

        if not isinstance(values, list):
            return cleaned

        for item in values:

            if not isinstance(item, dict):
                continue

            cleaned.append({
                "intent": cls._safe_value(
                    item.get("intent")
                ),
                "confidence": cls._safe_float(
                    item.get("confidence")
                ),
            })

        return cleaned


if __name__ == "__main__":

    trace = XAITrace("demo-xai-session")

    trace.set_user_input(
        "How much is my account balance?"
    )

    trace.record_router({
        "intent": "ACCOUNT_BALANCE",
        "raw_prediction": "ACCOUNT_BALANCE",
        "confidence": 0.8993,
        "margin": 0.8913,
        "decision": "ROUTE",
        "reason": "high_confidence",
        "top_k": [
            {
                "intent": "ACCOUNT_BALANCE",
                "confidence": 0.8993
            },
            {
                "intent": "SUPPORT_REQUEST",
                "confidence": 0.0081
            }
        ]
    })

    trace.record_policy({
        "status": "ALLOWED",
        "risk_level": "medium",
        "authentication_required": True,
        "confirmation_required": False,
        "tool": "get_account_balance",
    })

    trace.record_session({
        "authenticated": True,
        "awaiting_authentication": False,
        "awaiting_confirmation": False,
        "pending_intent": None,
        "pending_tool": None,
    })

    trace.record_tool({
        "tool": "get_account_balance",
        "success": True,
        "message": "Account balance retrieved successfully.",
        "data": {
            "account_id": "ACC1001",
            "balance": 58240.75,
            "available_balance": 54120.50,
            "currency": "INR",
        }
    })

    trace.record_final(
        stage="tool",
        status="TOOL_EXECUTED",
        message="Account balance retrieved successfully."
    )

    saved = trace.save()

    print("=" * 80)
    print("FinAI XAI TRACE TEST")
    print("=" * 80)
    print("TRACE ID:", trace.data["trace_id"])
    print("USER:", trace.data["user_input"])
    print("INTENT:", trace.data["router"]["intent"])
    print(
        "CONFIDENCE:",
        trace.data["router"]["confidence"]
    )
    print(
        "POLICY:",
        trace.data["policy"]["status"]
    )
    print(
        "TOOL:",
        trace.data["tool"]["name"]
    )
    print(
        "TOOL SUCCESS:",
        trace.data["tool"]["success"]
    )
    print(
        "FINAL:",
        trace.data["final"]["status"]
    )
    print("SAVED:", saved)




