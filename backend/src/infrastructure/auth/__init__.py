"""Infrastructure layer - authentication implementations.
Concrete implementations of authentication and session management.
"""
from typing import Optional, Dict, Any
import jwt
from datetime import datetime, timedelta


class JWTAuthenticator:
    """JWT authentication implementation."""

    def __init__(self, secret_key: str = None, algorithm: str = "HS256", access_token_expire_minutes: int = 30):
        self.secret_key = secret_key or "default-secret-key"
        self.algorithm = algorithm
        self.access_token_expire_minutes = access_token_expire_minutes

    def create_access_token(self, data: Dict[str, Any], expires_delta: timedelta = None) -> str:
        """Create an access token."""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=self.access_token_expire_minutes)
        
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt

    def verify_token(self, token: str) -> Dict[str, Any]:
        """Verify and decode a token."""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return payload
        except jwt.ExpiredSignatureError:
            raise jwt.ExpiredSignatureError("Token has expired")
        except jwt.InvalidTokenError:
            raise jwt.InvalidTokenError("Invalid token")


class PasswordHasher:
    """Password hashing implementation using bcrypt."""

    def hash_password(self, password: str) -> str:
        """Hash a password."""
        import bcrypt
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
        return hashed.decode('utf-8')

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash."""
        import bcrypt
        return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))


class InMemorySessionManager:
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


def get_session_manager():
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
