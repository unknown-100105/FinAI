from typing import Any, Dict, Optional

from xai.trace import XAITrace


class XAIIntegration:

    def __init__(self, session_id: str, user_text: str):
        self.trace = XAITrace(session_id)
        self.trace.set_user_input(user_text)

    def record_router(self, router_result: Optional[Dict[str, Any]]):
        self.trace.record_router(router_result)

    def record_policy(self, policy_result: Optional[Dict[str, Any]]):
        self.trace.record_policy(policy_result)

    def record_session(self, session_result: Optional[Dict[str, Any]]):
        self.trace.record_session(session_result)

    def record_tool(self, tool_result: Optional[Dict[str, Any]]):
        self.trace.record_tool(tool_result)

    def record_claims(self, claim_set):
        self.trace.record_claims(claim_set)

    def record_finance(
        self,
        operation: str,
        status: str,
        parameters: Dict[str, Any],
        result: Optional[Dict[str, Any]],
        source: str,
    ):

        self.trace.data["finance"] = {
            "operation": str(operation),
            "status": str(status),
            "parameters": self.trace._clean_value(parameters),
            "result": self.trace._clean_value(result),
            "source": str(source),
        }

    def record_portfolio(
        self,
        status: str,
        portfolio: Optional[Dict[str, Any]],
        concentration: Optional[Dict[str, Any]],
        historical_risk: Optional[Dict[str, Any]],
        xai_sources: Optional[Dict[str, Any]],
    ):

        self.trace.data["portfolio"] = {
            "status": str(status),
            "portfolio": self.trace._clean_value(portfolio),
            "concentration": self.trace._clean_value(
                concentration
            ),
            "historical_risk": self.trace._clean_value(
                historical_risk
            ),
            "xai_sources": self.trace._clean_value(
                xai_sources
            ),
        }

    def record_final(
        self,
        stage: str,
        status: str,
        message: str,
    ):

        self.trace.record_final(
            stage=stage,
            status=status,
            message=message,
        )

    def save(self):

        return self.trace.save()

