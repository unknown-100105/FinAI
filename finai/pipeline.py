from .router import route_model_output, execute_tool
from .rag import retrieve_context


class FinAIPipeline:
    """
    Main orchestration layer for FinAI.

    The model itself is injected later.
    For now, this class can operate with
    mock structured model responses.
    """

    def __init__(self, model_engine=None):

        self.model_engine = model_engine

    # --------------------------------------------------------
    # Temporary model interface
    # --------------------------------------------------------

    def generate_model_output(self, user_text: str):

        """
        Temporary rule-based mock.

        This is ONLY for testing the complete
        application pipeline.

        Later this will call:
            self.model_engine.generate(...)
        """

        text = user_text.lower()

        if "balance" in text:

            return """
INTENT: ACCOUNT_BALANCE
RISK_LEVEL: medium
REQUIRES_TOOL: true
RESPONSE: I can check your account balance.
"""

        if "pending" in text:

            return """
INTENT: PAYMENT_PENDING
RISK_LEVEL: medium
REQUIRES_TOOL: true
RESPONSE: I can check your pending payment.
"""

        if "lost card" in text or "lost my card" in text:

            return """
INTENT: CARD_LOST
RISK_LEVEL: high
REQUIRES_TOOL: true
RESPONSE: Your card needs to be blocked.
"""

        return """
INTENT: GENERAL_FINANCE
RISK_LEVEL: low
REQUIRES_TOOL: false
RESPONSE: I can provide general financial information.
"""

    # --------------------------------------------------------
    # Main request processor
    # --------------------------------------------------------

    def process(
        self,
        user_text: str,
        authenticated: bool = False,
        confirmed: bool = False,
    ):

        # ----------------------------------------------------
        # Generate structured model output
        # ----------------------------------------------------

        if self.model_engine is not None:

            model_output = (
                self.model_engine.generate(
                    user_text
                )
            )

        else:

            model_output = (
                self.generate_model_output(
                    user_text
                )
            )

        # ----------------------------------------------------
        # Router
        # ----------------------------------------------------

        route = route_model_output(
            user_text,
            model_output,
        )

        # ----------------------------------------------------
        # Blocked request
        # ----------------------------------------------------

        if not route.allowed:

            return {
                "status": "blocked",
                "intent": route.intent,
                "risk_level": route.risk_level,
                "message": route.reason,
                "model_output": model_output,
            }

        # ----------------------------------------------------
        # Tool path
        # ----------------------------------------------------

        if route.tool_name is not None:

            tool_result = execute_tool(
                route,
                authenticated=authenticated,
                confirmed=confirmed,
            )

            return {
                "status": "tool",
                "intent": route.intent,
                "risk_level": route.risk_level,
                "tool": route.tool_name,
                "tool_result": tool_result,
                "model_output": model_output,
            }

        # ----------------------------------------------------
        # Knowledge/RAG path
        # ----------------------------------------------------

        results, context = retrieve_context(
            user_text,
            top_k=3,
        )

        return {
            "status": "rag",
            "intent": route.intent,
            "risk_level": route.risk_level,
            "documents": len(results),
            "context": context,
            "model_output": model_output,
        }