from datetime import datetime

from orchestrator.engine import FinAIOrchestrator
from orchestrator.session import SessionStore


class SessionOrchestrator:

    def __init__(self):
        self.engine = FinAIOrchestrator()
        self.sessions = SessionStore()

    def handle_message(
        self,
        session_id: str,
        user_text: str,
    ):

        session = self.sessions.get(session_id)

        # ---------------------------------------------------------
        # If there is a pending operation awaiting authentication,
        # resume THAT operation after authentication.
        # ---------------------------------------------------------

        if session.awaiting_authentication:

            session.authenticate()

            pending_request = session.pending_request

            if not pending_request:
                session.clear_pending_operation()

                return {
                    "status": "ERROR",
                    "message": "No pending operation was found.",
                    "session": session.snapshot(),
                }

            result = self.engine.process(
                user_text=pending_request,
                authenticated=True,
                confirmed=False,
            )

            return self._update_session(
                session,
                pending_request,
                result,
            )

        # ---------------------------------------------------------
        # If there is a pending operation awaiting confirmation,
        # this message acts as the confirmation event.
        # ---------------------------------------------------------

        if session.awaiting_confirmation:

            confirmation = self._is_confirmation(user_text)

            if not confirmation:

                return {
                    "status": "CONFIRMATION_REQUIRED",
                    "message": (
                        "This operation has not been confirmed. "
                        "Please explicitly confirm it to continue."
                    ),
                    "session": session.snapshot(),
                }

            pending_request = session.pending_request

            if not pending_request:

                session.clear_pending_operation()

                return {
                    "status": "ERROR",
                    "message": "No pending operation was found.",
                    "session": session.snapshot(),
                }

            pending_intent = session.pending_intent

            result = self.engine.process(
                user_text=pending_request,
                authenticated=session.is_authenticated(),
                confirmed=True,
            )

            # Only consume confirmation if the router still identifies
            # the exact pending intent.
            current_intent = (
                result.get("router", {}).get("intent")
                if result.get("router")
                else None
            )

            if current_intent != pending_intent:

                return {
                    "status": "SECURITY_REVIEW_REQUIRED",
                    "message": (
                        "The confirmed request does not match the "
                        "pending operation."
                    ),
                    "session": session.snapshot(),
                    "result": result,
                }

            session.clear_pending_operation()

            return {
                **result,
                "session": session.snapshot(),
            }

        # ---------------------------------------------------------
        # Normal new request
        # ---------------------------------------------------------

        result = self.engine.process(
            user_text=user_text,
            authenticated=session.is_authenticated(),
            confirmed=False,
        )

        return self._update_session(
            session,
            user_text,
            result,
        )

    def _update_session(
        self,
        session,
        request,
        result,
    ):

        status = result.get("status")

        if status == "AUTH_REQUIRED":

            policy = result.get("policy") or {}

            session.set_pending_operation(
                request=request,
                intent=result["router"]["intent"],
                tool=policy.get("tool"),
                awaiting_authentication=True,
                awaiting_confirmation=False,
            )

        elif status == "CONFIRMATION_REQUIRED":

            policy = result.get("policy") or {}

            session.set_pending_operation(
                request=request,
                intent=result["router"]["intent"],
                tool=policy.get("tool"),
                awaiting_authentication=False,
                awaiting_confirmation=True,
            )

        elif status in {
            "TOOL_EXECUTED",
            "ALLOWED_NO_TOOL",
            "UNKNOWN",
            "CLARIFICATION_REQUIRED",
        }:

            if not session.awaiting_authentication:
                session.clear_pending_operation()

        return {
            **result,
            "session": session.snapshot(),
        }

    @staticmethod
    def _is_confirmation(text: str) -> bool:

        normalized = text.strip().lower()

        confirmation_phrases = {
            "yes",
            "yes please",
            "confirm",
            "confirmed",
            "i confirm",
            "proceed",
            "proceed please",
            "do it",
            "go ahead",
        }

        return normalized in confirmation_phrases


if __name__ == "__main__":

    app = SessionOrchestrator()

    session_id = "demo-session-001"

    print("=" * 80)
    print("FinAI SESSION-AWARE ORCHESTRATOR TEST")
    print("=" * 80)

    # ---------------------------------------------------------
    # TURN 1 — User requests sensitive action
    # ---------------------------------------------------------

    print()
    print("TURN 1")
    print("-" * 80)

    result = app.handle_message(
        session_id,
        "My card is lost",
    )

    print("USER: My card is lost")
    print("STATUS:", result["status"])
    print("MESSAGE:", result["message"])
    print("SESSION:", result["session"])

    # ---------------------------------------------------------
    # TURN 2 — Authentication completed
    # ---------------------------------------------------------

    print()
    print("TURN 2")
    print("-" * 80)

    result = app.handle_message(
        session_id,
        "authenticated",
    )

    print("USER: authenticated")
    print("STATUS:", result["status"])
    print("MESSAGE:", result["message"])
    print("SESSION:", result["session"])

    # ---------------------------------------------------------
    # TURN 3 — Confirmation
    # ---------------------------------------------------------

    print()
    print("TURN 3")
    print("-" * 80)

    result = app.handle_message(
        session_id,
        "yes",
    )

    print("USER: yes")
    print("STATUS:", result["status"])
    print("MESSAGE:", result["message"])
    print("SESSION:", result["session"])

    if result.get("tool"):
        print("TOOL:", result["tool"]["tool"])
        print("SUCCESS:", result["tool"]["success"])
        print("DATA:", result["tool"]["data"])

    # ---------------------------------------------------------
    # TURN 4 — Normal request after operation
    # ---------------------------------------------------------

    print()
    print("TURN 4")
    print("-" * 80)

    result = app.handle_message(
        session_id,
        "How much is my account balance?",
    )

    print("USER: How much is my account balance?")
    print("STATUS:", result["status"])
    print("MESSAGE:", result["message"])
    print("SESSION:", result["session"])
