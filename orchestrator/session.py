from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional


AUTH_SESSION_MINUTES = 10


@dataclass
class SessionState:
    session_id: str

    authenticated: bool = False
    authenticated_at: Optional[datetime] = None

    pending_request: Optional[str] = None
    pending_intent: Optional[str] = None
    pending_tool: Optional[str] = None

    awaiting_authentication: bool = False
    awaiting_confirmation: bool = False

    def authenticate(self):
        self.authenticated = True
        self.authenticated_at = datetime.now()
        self.awaiting_authentication = False

    def is_authenticated(self) -> bool:
        if not self.authenticated:
            return False

        if self.authenticated_at is None:
            return False

        expiry = self.authenticated_at + timedelta(
            minutes=AUTH_SESSION_MINUTES
        )

        if datetime.now() > expiry:
            self.logout()
            return False

        return True

    def set_pending_operation(
        self,
        request: str,
        intent: str,
        tool: Optional[str],
        awaiting_authentication: bool = False,
        awaiting_confirmation: bool = False,
    ):
        self.pending_request = request
        self.pending_intent = intent
        self.pending_tool = tool

        self.awaiting_authentication = awaiting_authentication
        self.awaiting_confirmation = awaiting_confirmation

    def clear_pending_operation(self):
        self.pending_request = None
        self.pending_intent = None
        self.pending_tool = None

        self.awaiting_authentication = False
        self.awaiting_confirmation = False

    def logout(self):
        self.authenticated = False
        self.authenticated_at = None
        self.clear_pending_operation()

    def snapshot(self):
        return {
            "session_id": self.session_id,
            "authenticated": self.is_authenticated(),
            "pending_request": self.pending_request,
            "pending_intent": self.pending_intent,
            "pending_tool": self.pending_tool,
            "awaiting_authentication": self.awaiting_authentication,
            "awaiting_confirmation": self.awaiting_confirmation,
        }


class SessionStore:

    def __init__(self):
        self.sessions = {}

    def create(self, session_id: str) -> SessionState:
        session = SessionState(session_id=session_id)
        self.sessions[session_id] = session
        return session

    def get(self, session_id: str) -> SessionState:
        if session_id not in self.sessions:
            return self.create(session_id)

        return self.sessions[session_id]

    def delete(self, session_id: str):
        self.sessions.pop(session_id, None)
