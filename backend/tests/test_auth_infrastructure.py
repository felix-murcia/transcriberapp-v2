"""
Tests for authentication infrastructure implementations.
Covers user authentication, JWT tokens, and security features.
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
import jwt
from backend.src.infrastructure.auth import JWTAuthenticator, PasswordHasher


class TestJWTAuthenticator:
    """Test JWT authentication implementation."""

    def test_init_with_default_config(self):
        """Test JWTAuthenticator initialization with default config."""
        authenticator = JWTAuthenticator()
        assert authenticator.secret_key is not None
        assert authenticator.algorithm == "HS256"
        assert authenticator.access_token_expire_minutes == 30

    def test_init_with_custom_config(self):
        """Test JWTAuthenticator initialization with custom config."""
        authenticator = JWTAuthenticator(
            secret_key="custom-secret",
            algorithm="RS256",
            access_token_expire_minutes=60
        )
        assert authenticator.secret_key == "custom-secret"
        assert authenticator.algorithm == "RS256"
        assert authenticator.access_token_expire_minutes == 60

    def test_create_access_token(self):
        """Test access token creation."""
        authenticator = JWTAuthenticator(secret_key="test-secret")
        
        token = authenticator.create_access_token(data={"sub": "test-user"})
        
        # Assert token is a string
        assert isinstance(token, str)
        
        # Assert token can be decoded
        decoded = jwt.decode(token, "test-secret", algorithms=["HS256"])
        assert decoded["sub"] == "test-user"
        assert "exp" in decoded

    def test_create_access_token_with_custom_expire(self):
        """Test access token creation with custom expiration."""
        authenticator = JWTAuthenticator(secret_key="test-secret")
        
        token = authenticator.create_access_token(
            data={"sub": "test-user"}, 
            expires_delta=timedelta(minutes=15)
        )
        
        decoded = jwt.decode(token, "test-secret", algorithms=["HS256"])
        # Check expiration is set correctly
        assert decoded["exp"] > datetime.utcnow().timestamp()

    def test_verify_token_valid(self):
        """Test token verification with valid token."""
        authenticator = JWTAuthenticator(secret_key="test-secret")
        
        token = authenticator.create_access_token(data={"sub": "test-user"})
        payload = authenticator.verify_token(token)
        
        assert payload["sub"] == "test-user"

    def test_verify_token_invalid(self):
        """Test token verification with invalid token."""
        authenticator = JWTAuthenticator(secret_key="test-secret")
        
        with pytest.raises(jwt.InvalidTokenError):
            authenticator.verify_token("invalid-token")

    def test_verify_token_expired(self):
        """Test token verification with expired token."""
        authenticator = JWTAuthenticator(secret_key="test-secret")
        
        # Create expired token
        expired_token = jwt.encode(
            {"sub": "test-user", "exp": datetime.utcnow() - timedelta(minutes=1)},
            "test-secret",
            algorithm="HS256"
        )
        
        with pytest.raises(jwt.ExpiredSignatureError):
            authenticator.verify_token(expired_token)

    def test_verify_token_wrong_secret(self):
        """Test token verification with wrong secret."""
        authenticator1 = JWTAuthenticator(secret_key="secret1")
        authenticator2 = JWTAuthenticator(secret_key="secret2")
        
        token = authenticator1.create_access_token(data={"sub": "test-user"})
        
        with pytest.raises(jwt.InvalidTokenError):
            authenticator2.verify_token(token)


class TestPasswordHasher:
    """Test password hashing implementation."""

    def test_hash_password(self):
        """Test password hashing."""
        hasher = PasswordHasher()
        
        password = "test-password"
        hashed = hasher.hash_password(password)
        
        # Assert hashed password is different from original
        assert hashed != password
        # Assert hashed password is a string
        assert isinstance(hashed, str)
        # Assert hashed password has proper length (bcrypt typically 60 chars)
        assert len(hashed) > 50

    def test_verify_password_correct(self):
        """Test password verification with correct password."""
        hasher = PasswordHasher()
        
        password = "test-password"
        hashed = hasher.hash_password(password)
        
        assert hasher.verify_password(password, hashed) is True

    def test_verify_password_incorrect(self):
        """Test password verification with incorrect password."""
        hasher = PasswordHasher()
        
        password = "test-password"
        wrong_password = "wrong-password"
        hashed = hasher.hash_password(password)
        
        assert hasher.verify_password(wrong_password, hashed) is False

    def test_verify_password_empty(self):
        """Test password verification with empty password."""
        hasher = PasswordHasher()
        
        password = ""
        hashed = hasher.hash_password(password)
        
        assert hasher.verify_password(password, hashed) is True

    def test_hash_password_consistency(self):
        """Test that same password produces different hashes (salted)."""
        hasher = PasswordHasher()
        
        password = "test-password"
        hash1 = hasher.hash_password(password)
        hash2 = hasher.hash_password(password)
        
        # Different hashes due to salt
        assert hash1 != hash2
        # Both should verify correctly
        assert hasher.verify_password(password, hash1) is True
        assert hasher.verify_password(password, hash2) is True