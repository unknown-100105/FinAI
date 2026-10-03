from datetime import datetime

from orchestrator.hybrid_engine import FinAIHybridEngine
from orchestrator.session import SessionStore
from xai.trace import XAITrace


class XAISessionOrchestrator:

    def __init__(
        self,
        engine=None,
        response_service=None,
    ):
        self.engine = (
            engine
            if engine is not None
            else FinAIHybridEngine(
                response_service=response_service
            )
        )
        self.sessions = SessionStore()

    def handle_message(
        self,
        session_id: str,
        user_text: str,
        generate_response: bool = False,
        language: str = "English",
        persona: str = "neutral",
        max_new_tokens: int = 256,
        model_id: str | None = None,
    ):

        session = self.sessions.get(session_id)

        trace = XAITrace(session_id)

        trace.set_user_input(user_text)

        # ---------------------------------------------------------
        # TURN A: Pending authentication
        # ---------------------------------------------------------

        if session.awaiting_authentication:

            # Never interpret an arbitrary message as authentication.
            if not self._is_authentication(user_text):

                message = (
                    "Authentication is required before continuing. "
                    "Please complete authentication and reply with "
                    "'authenticated'."
                )

                trace.record_session(session.snapshot())

                trace.record_final(
                    stage="session",
                    status="AUTH_REQUIRED",
                    message=message,
                )

                trace_path = trace.save()

                return {
                    "status": "AUTH_REQUIRED",
                    "message": message,
                    "trace_id": trace.data["trace_id"],
                    "trace_path": str(trace_path),
                    "session": session.snapshot(),
                }

            session.authenticate()

            pending_request = session.pending_request

            if not pending_request:

                session.clear_pending_operation()

                trace.record_session(session.snapshot())

                trace.record_final(
                    stage="session",
                    status="ERROR",
                    message="No pending operation was found.",
                )

                trace_path = trace.save()

                return {
                    "status": "ERROR",
                    "message": "No pending operation was found.",
                    "trace_id": trace.data["trace_id"],
                    "trace_path": str(trace_path),
                    "session": session.snapshot(),
                }

            result = self._process_engine(
                user_text=pending_request,
                authenticated=True,
                confirmed=False,
                generate_response=generate_response,
                language=language,
                persona=persona,
                max_new_tokens=max_new_tokens,
                model_id=model_id,
            )

            trace.record_router(result.get("router"))
            trace.record_policy(result.get("policy"))
            trace.record_execution_plan(
                result.get("execution_plan")
            )
            trace.record_rag(result.get("rag"))
            trace.record_response_generation(
                result.get("response_generation")
            )

            updated = self._update_session(
                session,
                pending_request,
                result,
            )

            trace.record_session(updated["session"])

            if result.get("tool"):
                trace.record_tool(result["tool"])

            trace.record_final(
                stage=result.get("stage"),
                status=result.get("status"),
                message=result.get("message"),
            )

            trace_path = trace.save()

            return {
                **result,
                "trace_id": trace.data["trace_id"],
                "trace_path": str(trace_path),
                "session": updated["session"],
            }

        # ---------------------------------------------------------
        # TURN B: Pending confirmation
        # ---------------------------------------------------------

        if session.awaiting_confirmation:

            if not self._is_confirmation(user_text):

                trace.record_session(session.snapshot())

                trace.record_final(
                    stage="session",
                    status="CONFIRMATION_REQUIRED",
                    message=(
                        "This operation has not been confirmed. "
                        "Please explicitly confirm it to continue."
                    ),
                )

                trace_path = trace.save()

                return {
                    "status": "CONFIRMATION_REQUIRED",
                    "message": (
                        "This operation has not been confirmed. "
                        "Please explicitly confirm it to continue."
                    ),
                    "trace_id": trace.data["trace_id"],
                    "trace_path": str(trace_path),
                    "session": session.snapshot(),
                }

            pending_request = session.pending_request
            pending_intent = session.pending_intent

            if not pending_request:

                session.clear_pending_operation()

                trace.record_session(session.snapshot())

                trace.record_final(
                    stage="session",
                    status="ERROR",
                    message="No pending operation was found.",
                )

                trace_path = trace.save()

                return {
                    "status": "ERROR",
                    "message": "No pending operation was found.",
                    "trace_id": trace.data["trace_id"],
                    "trace_path": str(trace_path),
                    "session": session.snapshot(),
                }

            result = self._process_engine(
                user_text=pending_request,
                authenticated=session.is_authenticated(),
                confirmed=True,
                generate_response=generate_response,
                language=language,
                persona=persona,
                max_new_tokens=max_new_tokens,
                model_id=model_id,
            )

            trace.record_router(result.get("router"))
            trace.record_policy(result.get("policy"))
            trace.record_execution_plan(
                result.get("execution_plan")
            )
            trace.record_rag(result.get("rag"))
            trace.record_response_generation(
                result.get("response_generation")
            )

            current_intent = None

            if result.get("router"):
                current_intent = result["router"].get("intent")

            # -----------------------------------------------------
            # Security invariant:
            # confirmation must apply to the same intent that
            # originally requested confirmation.
            # -----------------------------------------------------

            if current_intent != pending_intent:

                trace.record_session(session.snapshot())

                trace.record_final(
                    stage="security",
                    status="SECURITY_REVIEW_REQUIRED",
                    message=(
                        "The confirmed request does not match "
                        "the pending operation."
                    ),
                )

                trace_path = trace.save()

                return {
                    "status": "SECURITY_REVIEW_REQUIRED",
                    "message": (
                        "The confirmed request does not match "
                        "the pending operation."
                    ),
                    "trace_id": trace.data["trace_id"],
                    "trace_path": str(trace_path),
                    "session": session.snapshot(),
                    "result": result,
                }

            session.clear_pending_operation()

            trace.record_session(session.snapshot())

            if result.get("tool"):
                trace.record_tool(result["tool"])

            trace.record_final(
                stage=result.get("stage"),
                status=result.get("status"),
                message=result.get("message"),
            )

            trace_path = trace.save()

            return {
                **result,
                "trace_id": trace.data["trace_id"],
                "trace_path": str(trace_path),
                "session": session.snapshot(),
            }

        # ---------------------------------------------------------
        # NORMAL NEW REQUEST
        # ---------------------------------------------------------

        result = self._process_engine(
            user_text=user_text,
            authenticated=session.is_authenticated(),
            confirmed=False,
            generate_response=generate_response,
            language=language,
            persona=persona,
            max_new_tokens=max_new_tokens,
        )

        trace.record_router(result.get("router"))
        trace.record_policy(result.get("policy"))
        trace.record_execution_plan(
            result.get("execution_plan")
        )
        trace.record_rag(result.get("rag"))
        trace.record_response_generation(
            result.get("response_generation")
        )

        updated = self._update_session(
            session,
            user_text,
            result,
        )

        trace.record_session(updated["session"])

        if result.get("tool"):
            trace.record_tool(result["tool"])

        response_generation = (
            result.get("response_generation")
            or {}
        )

        final_status = (
            response_generation.get("status")
            or result.get("status")
        )

        final_message = (
            response_generation.get("response")
            or result.get("response")
            or result.get("message")
        )

        trace.record_final(
            stage=result.get("stage"),
            status=final_status,
            message=final_message,
        )

        trace_path = trace.save()

        return {
            **result,
            "trace_id": trace.data["trace_id"],
            "trace_path": str(trace_path),
            "session": updated["session"],
        }

    def authenticate_session(self, session_id: str):
        """Authenticate a development/demo session explicitly."""
        session = self.sessions.get(session_id)
        session.authenticate()
        return session.snapshot()

    def logout_session(self, session_id: str):
        """End the current session authentication state."""
        session = self.sessions.get(session_id)
        session.logout()
        return session.snapshot()

    def _process_engine(
        self,
        user_text,
        authenticated,
        confirmed,
        generate_response=False,
        language="English",
        persona="neutral",
        max_new_tokens=256,
        model_id=None,
    ):
        kwargs = {
            "user_text": user_text,
            "authenticated": authenticated,
            "confirmed": confirmed,
        }

        # Preserve compatibility with engines that implement only
        # the original process(...) contract.
        if generate_response:
            kwargs.update({
                "generate_response": True,
                "language": language,
                "persona": persona,
                "max_new_tokens": max_new_tokens,
                "model_id": model_id,
            })

        return self.engine.process(**kwargs)

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
                intent=str(
                    result["router"]["intent"]
                ),
                tool=policy.get("tool"),
                awaiting_authentication=True,
                awaiting_confirmation=False,
            )

        elif status == "CONFIRMATION_REQUIRED":

            policy = result.get("policy") or {}

            session.set_pending_operation(
                request=request,
                intent=str(
                    result["router"]["intent"]
                ),
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

            session.clear_pending_operation()

        return {
            **result,
            "session": session.snapshot(),
        }

    @staticmethod
    def _is_authentication(text: str):

        normalized = text.strip().lower()

        return normalized in {
            "authenticated",
            "authentication complete",
            "authenticated successfully",
            "otp verified",
            "verification complete",
        }

    @staticmethod
    def _is_confirmation(text: str):

        normalized = text.strip().lower()

        return normalized in {
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


if __name__ == "__main__":

    app = XAISessionOrchestrator()

    session_id = "xai-demo-001"

    conversation = [
        "My card is lost",
        "authenticated",
        "yes",
        "How much is my account balance?",
    ]

    print("=" * 80)
    print("FinAI XAI SESSION ORCHESTRATOR TEST")
    print("=" * 80)

    for number, user_text in enumerate(
        conversation,
        start=1,
    ):

        print()
        print(f"TURN {number}")
        print("-" * 80)
        print("USER:", user_text)

        result = app.handle_message(
            session_id=session_id,
            user_text=user_text,
        )

        print("STATUS:", result["status"])
        print("MESSAGE:", result["message"])
        print("TRACE ID:", result["trace_id"])
        print("TRACE PATH:", result["trace_path"])

        if result.get("router"):
            print(
                "INTENT:",
                result["router"].get("intent")
            )

        if result.get("policy"):
            print(
                "POLICY:",
                result["policy"].get("status")
            )

        if result.get("tool"):
            print(
                "TOOL:",
                result["tool"].get("tool")
            )
            print(
                "TOOL SUCCESS:",
                result["tool"].get("success")
            )

        print(
            "SESSION:",
            result["session"]
        )




