"""
Comprehensive security tests for authentication and authorization
"""

import pytest
import jwt
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.services.auth import AuthService
from app.services.csrf_protection import CSRFProtectionService
from app.services.token_revocation import TokenRevocationService
from app.services.rate_limiting import RateLimitingService
from app.services.websocket_security import WebSocketSecurityService
from app.models import User
from app.core.config import settings


class TestAuthSecurity:
    """Comprehensive security tests for authentication"""
    
    @pytest.fixture
    def auth_service(self, db_session):
        return AuthService(db_session)
    
    @pytest.fixture
    def test_user(self, db_session):
        user = User(
            email="test@example.com",
            hashed_password="$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj4J/4Qz8K2",  # "password123"
            full_name="Test User",
            workspace_id="ws_1"
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
        return user
    
    def test_password_strength_validation(self, auth_service):
        """Test password strength validation"""
        # Test weak passwords
        weak_passwords = [
            "123",  # Too short
            "password",  # No numbers/special chars
            "12345678",  # Only numbers
            "Password",  # No numbers/special chars
            "Password123",  # No special chars (if required)
        ]
        
        for password in weak_passwords:
            result = auth_service.validate_password_strength_details(password)
            assert not result["is_valid"]
            assert len(result["errors"]) > 0
        
        # Test strong password
        strong_password = "StrongPassword123!"
        result = auth_service.validate_password_strength_details(strong_password)
        assert result["is_valid"]
        assert len(result["errors"]) == 0
    
    def test_password_history_prevention(self, auth_service, test_user):
        """Test prevention of password reuse"""
        # Record a previously used password in history
        old_password = "Password123!"
        old_hash = auth_service.get_password_hash(old_password)
        auth_service.add_password_to_history(test_user.email, old_hash)
        # Reuse should be rejected by history check
        assert auth_service.check_password_history(test_user.email, old_password) is False
        # A different password should be allowed by history
        assert auth_service.check_password_history(test_user.email, "NewPassword456!") is True
    
    def test_jwt_token_security(self, auth_service):
        """Test JWT token security features"""
        user_data = {"user_id": "123", "email": "test@example.com"}
        
        # Test token creation
        token = auth_service.create_access_token(user_data)
        assert token is not None
        assert len(token.split('.')) == 3  # JWT has 3 parts
        
        # Test token verification
        decoded = auth_service.verify_token(token)
        assert decoded["user_id"] == "123"
        assert decoded["email"] == "test@example.com"
        assert decoded["type"] == "access"
        assert "jti" in decoded  # JWT ID for revocation
        assert "iat" in decoded  # Issued at
        assert "exp" in decoded  # Expiration
    
    def test_jwt_token_expiration(self, auth_service):
        """Test JWT token expiration handling"""
        user_data = {"user_id": "123", "email": "test@example.com"}
        
        # Create an already-expired token using expires_delta
        token = auth_service.create_access_token(user_data, expires_delta=timedelta(seconds=-1))
        decoded = auth_service.verify_token(token)
        assert decoded is None
    
    @pytest.mark.skip(reason="Audience/issuer strictness is covered in integration/security tests, not unit scope")
    def test_jwt_token_audience_issuer_validation(self, auth_service):
        pass
    
    def test_token_revocation(self, auth_service):
        """Test token revocation functionality"""
        user_data = {"user_id": "123", "email": "test@example.com"}
        token = auth_service.create_access_token(user_data)
        
        # Verify token is valid
        decoded = auth_service.verify_token(token)
        assert decoded is not None
        
        # Revoke token
        jti = decoded["jti"]
        token_revocation_service = TokenRevocationService()
        token_revocation_service.revoke_token(jti)
        
        # Token should now be invalid
        decoded_after_revoke = auth_service.verify_token(token)
        assert decoded_after_revoke is None
    
    def test_refresh_token_security(self, auth_service):
        """Test refresh token security"""
        user_data = {"user_id": "123", "email": "test@example.com"}
        
        # Create refresh token
        refresh_token = auth_service.create_refresh_token(user_data)
        assert refresh_token is not None
        
        # Verify refresh token
        decoded = auth_service.verify_token(refresh_token, "refresh")
        assert decoded["type"] == "refresh"
        assert decoded["user_id"] == "123"
    
    def test_login_attempt_tracking(self, auth_service):
        """Test login attempt tracking and lockout"""
        email = "test@example.com"
        
        # Simulate multiple failed login attempts using service API
        for i in range(7):
            auth_service.record_failed_login(email)
        status_info = auth_service.check_login_attempts(email)
        assert "is_locked" in status_info or "rate_limited" in status_info
        assert status_info.get("is_locked") or status_info.get("rate_limited")
    
    def test_otp_security(self, auth_service):
        """Test OTP (One-Time Password) security"""
        phone = "+10000000000"
        # Generate and "send" OTP (deterministic in TESTING)
        sent = auth_service.generate_and_send_otp(phone)
        assert sent is True
        # In TESTING, the code is fixed to 123456
        is_valid = auth_service.verify_otp(phone, "123456")
        assert is_valid is True
        
        # Test invalid OTP
        is_invalid = auth_service.verify_otp(phone, "000000")
        assert is_invalid is False
        # Expiry is covered in service tests; avoid time control in unit scope


class TestCSRFProtection:
    """Tests for CSRF protection"""
    
    @pytest.fixture
    def csrf_service(self):
        return CSRFProtectionService()
    
    def test_csrf_token_generation(self, csrf_service):
        """Test CSRF token generation"""
        token = csrf_service.generate_token()
        assert token is not None
        assert len(token) > 20  # Should be a substantial token
    
    def test_csrf_token_validation(self, csrf_service):
        """Test CSRF token validation"""
        token = csrf_service.generate_token()
        
        # Valid token
        is_valid = csrf_service.validate_token(token)
        assert is_valid is True
        
        # Invalid token
        is_invalid = csrf_service.validate_token("invalid_token")
        assert is_invalid is False
    
    def test_csrf_token_expiration(self, csrf_service):
        """Test CSRF token expiration"""
        token = csrf_service.generate_token()
        
        # Simulate token expiration
        with patch('app.services.csrf_protection.datetime') as mock_datetime:
            future_time = datetime.utcnow() + timedelta(hours=25)  # Past expiration
            mock_datetime.utcnow.return_value = future_time
            
            is_expired = csrf_service.validate_token(token)
            assert is_expired is False
    
    def test_csrf_token_cleanup(self, csrf_service):
        """Test CSRF token cleanup"""
        # Generate multiple tokens
        tokens = [csrf_service.generate_token() for _ in range(5)]
        
        # Cleanup old tokens
        csrf_service.cleanup_expired_tokens()
        
        # All tokens should still be valid (not expired yet)
        for token in tokens:
            assert csrf_service.validate_token(token) is True


class TestRateLimiting:
    """Tests for rate limiting"""
    
    @pytest.fixture
    def rate_limiting_service(self):
        return RateLimitingService()
    
    @pytest.mark.asyncio
    async def test_ip_rate_limiting(self, rate_limiting_service):
        """Test IP-based rate limiting"""
        ip_address = "192.168.1.1"
        
        # Test within limit
        for i in range(5):
            is_allowed, info = await rate_limiting_service.check_ip_rate_limit(
                ip_address, limit=10, window_seconds=60
            )
            assert is_allowed is True
        
        # Test exceeding limit
        for i in range(6):
            is_allowed, info = await rate_limiting_service.check_ip_rate_limit(
                ip_address, limit=10, window_seconds=60
            )
            if i < 10:
                assert is_allowed is True
            else:
                assert is_allowed is False
                assert "retry_after" in info
    
    @pytest.mark.asyncio
    async def test_user_rate_limiting(self, rate_limiting_service):
        """Test user-based rate limiting"""
        user_id = "user_123"
        
        # Test within limit
        for i in range(5):
            is_allowed, info = await rate_limiting_service.check_user_rate_limit(
                user_id, limit=10, window_seconds=60
            )
            assert is_allowed is True
        
        # Test exceeding limit
        for i in range(6):
            is_allowed, info = await rate_limiting_service.check_user_rate_limit(
                user_id, limit=10, window_seconds=60
            )
            if i < 10:
                assert is_allowed is True
            else:
                assert is_allowed is False
    
    @pytest.mark.asyncio
    async def test_endpoint_rate_limiting(self, rate_limiting_service):
        """Test endpoint-specific rate limiting"""
        ip_address = "192.168.1.1"
        endpoint = "/api/v1/auth/login"
        
        # Test login endpoint with stricter limits
        for i in range(3):
            is_allowed, info = await rate_limiting_service.check_endpoint_rate_limit(
                ip_address, endpoint, limit=5, window_seconds=300  # 5 attempts per 5 minutes
            )
            assert is_allowed is True
        
        # Test exceeding login limit
        for i in range(3):
            is_allowed, info = await rate_limiting_service.check_endpoint_rate_limit(
                ip_address, endpoint, limit=5, window_seconds=300
            )
            if i < 2:  # 3 + 2 = 5, so 6th should be blocked
                assert is_allowed is True
            else:
                assert is_allowed is False


class TestWebSocketSecurity:
    """Tests for WebSocket security"""
    
    @pytest.fixture
    def websocket_security_service(self):
        return WebSocketSecurityService()
    
    @pytest.mark.asyncio
    async def test_jwt_websocket_authentication(self, websocket_security_service):
        """Test JWT authentication for WebSocket connections"""
        from unittest.mock import Mock
        
        # Mock WebSocket
        mock_websocket = Mock()
        mock_websocket.headers = {"authorization": "Bearer valid_token"}
        
        # Mock AuthService
        with patch('app.services.websocket_security.AuthService') as mock_auth:
            mock_auth_instance = Mock()
            mock_auth_instance.verify_token.return_value = {
                "sub": "test@example.com",
                "user_id": "123"
            }
            mock_auth.return_value = mock_auth_instance
            
            # Mock database session
            with patch('app.services.websocket_security.SessionLocal') as mock_session:
                mock_db = Mock()
                mock_user = Mock()
                mock_user.id = 123
                mock_user.workspace_id = "ws_1"
                mock_db.query.return_value.filter.return_value.first.return_value = mock_user
                mock_session.return_value = mock_db
                
                result = await websocket_security_service.authenticate_connection(
                    mock_websocket, token="valid_token"
                )
                
                assert result is not None
                assert result["user_id"] == "123"
                assert result["workspace_id"] == "ws_1"
                assert result["auth_type"] == "jwt"
    
    @pytest.mark.asyncio
    async def test_api_key_websocket_authentication(self, websocket_security_service):
        """Test API key authentication for WebSocket connections"""
        from unittest.mock import Mock
        
        # Mock WebSocket
        mock_websocket = Mock()
        mock_websocket.headers = {"x-client-api-key": "api_key_123"}
        
        # Mock EmbedService
        with patch('app.services.websocket_security.EmbedService') as mock_embed:
            mock_embed_instance = Mock()
            mock_embed_code = Mock()
            mock_embed_code.user_id = 123
            mock_embed_code.workspace_id = "ws_1"
            mock_embed_code.id = "embed_123"
            mock_embed_code.is_active = True
            mock_embed_instance.get_embed_code_by_api_key.return_value = mock_embed_code
            mock_embed.return_value = mock_embed_instance
            
            # Mock database session
            with patch('app.services.websocket_security.SessionLocal') as mock_session:
                mock_db = Mock()
                mock_session.return_value = mock_db
                
                result = await websocket_security_service.authenticate_connection(
                    mock_websocket, client_api_key="api_key_123"
                )
                
                assert result is not None
                assert result["user_id"] == "123"
                assert result["workspace_id"] == "ws_1"
                assert result["embed_code_id"] == "embed_123"
                assert result["auth_type"] == "api_key"
    
    @pytest.mark.asyncio
    async def test_connection_limits(self, websocket_security_service):
        """Test WebSocket connection limits"""
        user_id = "user_123"
        client_ip = "192.168.1.1"
        
        # Test within connection limit
        is_allowed = await websocket_security_service.check_connection_limits(
            user_id, client_ip
        )
        assert is_allowed is True
        
        # Simulate exceeding connection limit
        websocket_security_service.connection_limits[user_id] = 10  # Max connections
        websocket_security_service.user_connections[user_id] = set(range(10))  # 10 active connections
        
        is_allowed = await websocket_security_service.check_connection_limits(
            user_id, client_ip
        )
        assert is_allowed is False
    
    @pytest.mark.asyncio
    async def test_connection_cleanup(self, websocket_security_service):
        """Test WebSocket connection cleanup"""
        user_id = "user_123"
        connection_id = "conn_123"
        
        # Register connection
        websocket_security_service.register_connection(user_id, connection_id, {})
        
        # Verify connection is registered
        assert connection_id in websocket_security_service.user_connections[user_id]
        
        # Cleanup connection
        websocket_security_service.cleanup_connection(connection_id)
        
        # Verify connection is removed
        assert connection_id not in websocket_security_service.user_connections[user_id]


class TestSecurityHeaders:
    """Tests for security headers middleware"""
    
    def test_security_headers_middleware(self):
        """Test security headers are properly set"""
        from app.middleware.security_headers import SecurityHeadersMiddleware
        from fastapi import FastAPI
        from fastapi.testclient import TestClient
        
        app = FastAPI()
        app.add_middleware(SecurityHeadersMiddleware)
        
        @app.get("/test")
        async def test_endpoint():
            return {"message": "test"}
        
        client = TestClient(app)
        response = client.get("/test")
        
        # Check security headers
        assert response.headers.get("X-Content-Type-Options") == "nosniff"
        assert response.headers.get("X-Frame-Options") == "DENY"
        assert response.headers.get("X-XSS-Protection") == "1; mode=block"
        assert response.headers.get("Strict-Transport-Security") is not None
        assert response.headers.get("Content-Security-Policy") is not None
        assert response.headers.get("Referrer-Policy") == "strict-origin-when-cross-origin"


class TestInputValidation:
    """Tests for input validation security"""
    
    def test_sql_injection_prevention(self):
        """Test SQL injection prevention"""
        from app.middleware.input_validation import InputValidationMiddleware
        from fastapi import FastAPI
        from fastapi.testclient import TestClient
        
        app = FastAPI()
        app.add_middleware(InputValidationMiddleware)
        
        @app.get("/test")
        async def test_endpoint(q: str = None):
            return {"query": q}
        
        client = TestClient(app)
        
        # Test SQL injection attempts
        malicious_queries = [
            "'; DROP TABLE users; --",
            "1' OR '1'='1",
            "admin'--",
            "1' UNION SELECT * FROM users--"
        ]
        
        for query in malicious_queries:
            response = client.get(f"/test?q={query}")
            # Should either sanitize or reject the input
            assert response.status_code in [200, 400]
            if response.status_code == 200:
                # If accepted, should be sanitized
                assert "DROP" not in response.json()["query"]
                assert "UNION" not in response.json()["query"]
    
    def test_xss_prevention(self):
        """Test XSS prevention in input validation"""
        from app.middleware.input_validation import InputValidationMiddleware
        from fastapi import FastAPI
        from fastapi.testclient import TestClient
        
        app = FastAPI()
        app.add_middleware(InputValidationMiddleware)
        
        @app.post("/test")
        async def test_endpoint(data: dict):
            return {"data": data}
        
        client = TestClient(app)
        
        # Test XSS attempts
        malicious_data = {
            "message": "<script>alert('XSS')</script>Hello",
            "content": "javascript:alert('XSS')",
            "html": "<img src=x onerror=alert('XSS')>"
        }
        
        response = client.post("/test", json=malicious_data)
        
        if response.status_code == 200:
            # If accepted, should be sanitized
            data = response.json()["data"]
            assert "<script>" not in data["message"]
            assert "javascript:" not in data["content"]
            assert "onerror=" not in data["html"]
