"""Infrastructure layer - authentication implementations.
Concrete implementations of authentication and session management.
"""
from typing import Optional, Dict, Any
from backend.src.domain.ports import SessionManagerPort


class InMemorySessionManager(SessionManagerPort):
    """In-memory session manager implementation."""

    def __init__(self):
        self._sessions: Dict[str, Dict[str, Any]] = {}

    def create_session(self, user_id: str, session_data: Dict[str, Any]) -> str:
        """Create a new session."""
        import uuid
        session_token = str(uuid.uuid4())
        self._sessions[session_token] = {
            "user_id": user_id,
            **session_data,
        }
        return session_token

    def validate_session(self, session_token: str) -> bool:
        """Validate a session token."""
        return session_token in self._sessions

    def get_session_data(self, session_token: str) -> Optional[Dict[str, Any]]:
        """Get session data."""
        return self._sessions.get(session_token)

    def delete_session(self, session_token: str) -> bool:
        """Delete a session."""
        if session_token in self._sessions:
            del self._sessions[session_token]
            return True
        return False


# =============================================================================
# Factory functions
# =============================================================================

_session_manager = None


def get_session_manager() -> SessionManagerPort:
    """Get or create the session manager."""
    global _session_manager
    if _session_manager is None:
        _session_manager = InMemorySessionManager()
    return _session_manager


def get_auth_service():
    """Get auth service - placeholder for actual auth service."""
    class SimpleAuthService:
        def authenticate(self, username: str, password: str) -> Dict[str, Any]:
            """Simple authentication - accepts any non-empty credentials."""
            if username and password:
                return {"success": True, "user_id": username}
            return {"success": False, "error": "Invalid credentials"}

    return SimpleAuthService()
