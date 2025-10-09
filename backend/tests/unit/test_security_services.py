"""
Unit tests for Security Services
Tests all security-related services for production readiness
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, MagicMock, AsyncMock
from datetime import datetime, timedelta

from app.services.file_security import FileSecurityService
from app.services.csrf_protection import CSRFProtectionService
from app.services.database_security import DatabaseSecurityService
from app.services.input_validation import InputValidationService
from app.services.token_revocation import TokenRevocationService
from app.services.websocket_security import WebSocketSecurityService

class TestFileSecurityService:
    """Unit tests for FileSecurityService"""
    
    @pytest.fixture
    def file_security_service(self):
        return FileSecurityService()
    
    def test_initialization(self, file_security_service):
        """Test service initialization"""
        assert file_security_service is not None
        assert hasattr(file_security_service, 'allowed_extensions')
        assert hasattr(file_security_service, 'max_file_size')
    
    def test_validate_file_extension(self, file_security_service):
        """Test file extension validation"""
        # Test allowed extensions
        assert file_security_service.validate_file_extension("test.pdf") is True
        assert file_security_service.validate_file_extension("test.txt") is True
        assert file_security_service.validate_file_extension("test.docx") is True
        
        # Test disallowed extensions
        assert file_security_service.validate_file_extension("test.exe") is False
        assert file_security_service.validate_file_extension("test.bat") is False
        assert file_security_service.validate_file_extension("test.sh") is False
    
    def test_validate_file_size(self, file_security_service):
        """Test file size validation"""
        # Test valid sizes
        assert file_security_service.validate_file_size(1024 * 1024) is True  # 1MB
        assert file_security_service.validate_file_size(10 * 1024 * 1024) is True  # 10MB
        
        # Test invalid sizes
        assert file_security_service.validate_file_size(100 * 1024 * 1024) is False  # 100MB
        assert file_security_service.validate_file_size(0) is False  # Empty file
    
    def test_scan_for_malware(self, file_security_service):
        """Test malware scanning"""
        # Test clean file
        clean_content = b"This is clean content for testing"
        is_clean = file_security_service.scan_for_malware(clean_content)
        assert is_clean is True
        
        # Test suspicious content
        suspicious_content = b"eval(base64_decode('malicious_code'))"
        is_clean = file_security_service.scan_for_malware(suspicious_content)
        assert is_clean is False
    
    def test_validate_file_content_type(self, file_security_service):
        """Test file content type validation"""
        # Test valid content types
        assert file_security_service.validate_content_type("application/pdf") is True
        assert file_security_service.validate_content_type("text/plain") is True
        assert file_security_service.validate_content_type("application/vnd.openxmlformats-officedocument.wordprocessingml.document") is True
        
        # Test invalid content types
        assert file_security_service.validate_content_type("application/octet-stream") is False
        assert file_security_service.validate_content_type("text/html") is False
    
    def test_sanitize_filename(self, file_security_service):
        """Test filename sanitization"""
        # Test normal filename
        sanitized = file_security_service.sanitize_filename("normal_file.pdf")
        assert sanitized == "normal_file.pdf"
        
        # Test filename with special characters
        sanitized = file_security_service.sanitize_filename("file with spaces & symbols!.pdf")
        assert " " not in sanitized
        assert "&" not in sanitized
        assert "!" not in sanitized
        
        # Test filename with path traversal
        sanitized = file_security_service.sanitize_filename("../../../etc/passwd")
        assert "../" not in sanitized
        assert "etc" not in sanitized

class TestCSRFProtectionService:
    """Unit tests for CSRFProtectionService"""
    
    @pytest.fixture
    def csrf_service(self):
        return CSRFProtectionService()
    
    def test_initialization(self, csrf_service):
        """Test service initialization"""
        assert csrf_service is not None
        assert hasattr(csrf_service, 'secret_key')
    
    def test_generate_csrf_token(self, csrf_service):
        """Test CSRF token generation"""
        token = csrf_service.generate_csrf_token("user_123")
        
        assert isinstance(token, str)
        assert len(token) > 0
        assert token != "user_123"  # Should be different from user ID
    
    def test_validate_csrf_token(self, csrf_service):
        """Test CSRF token validation"""
        user_id = "user_123"
        token = csrf_service.generate_csrf_token(user_id)
        
        # Test valid token
        is_valid = csrf_service.validate_csrf_token(token, user_id)
        assert is_valid is True
        
        # Test invalid token
        is_valid = csrf_service.validate_csrf_token("invalid_token", user_id)
        assert is_valid is False
        
        # Test token for different user
        is_valid = csrf_service.validate_csrf_token(token, "different_user")
        assert is_valid is False
    
    def test_csrf_token_expiration(self, csrf_service):
        """Test CSRF token expiration"""
        user_id = "user_123"
        token = csrf_service.generate_csrf_token(user_id)
        
        # Mock time to simulate expiration
        with patch('time.time', return_value=time.time() + 3600):  # 1 hour later
            is_valid = csrf_service.validate_csrf_token(token, user_id)
            assert is_valid is False
    
    def test_cleanup_expired_tokens(self, csrf_service):
        """Test cleanup of expired tokens"""
        user_id = "user_123"
        token = csrf_service.generate_csrf_token(user_id)
        
        # Force expiration
        with patch('time.time', return_value=time.time() + 3600):
            csrf_service.cleanup_expired_tokens()
            
            # Token should be invalid after cleanup
            is_valid = csrf_service.validate_csrf_token(token, user_id)
            assert is_valid is False

class TestDatabaseSecurityService:
    """Unit tests for DatabaseSecurityService"""
    
    @pytest.fixture
    def db_security_service(self, db_session):
        return DatabaseSecurityService(db_session)
    
    def test_initialization(self, db_security_service):
        """Test service initialization"""
        assert db_security_service is not None
        assert hasattr(db_security_service, 'db')
    
    def test_validate_sql_query(self, db_security_service):
        """Test SQL query validation"""
        # Test safe queries
        assert db_security_service.validate_sql_query("SELECT * FROM users WHERE id = ?") is True
        assert db_security_service.validate_sql_query("INSERT INTO users (name) VALUES (?)") is True
        
        # Test dangerous queries
        assert db_security_service.validate_sql_query("DROP TABLE users") is False
        assert db_security_service.validate_sql_query("DELETE FROM users") is False
        assert db_security_service.validate_sql_query("UPDATE users SET password = 'hacked'") is False
    
    def test_detect_sql_injection(self, db_security_service):
        """Test SQL injection detection"""
        # Test safe input
        assert db_security_service.detect_sql_injection("normal_user_input") is False
        assert db_security_service.detect_sql_injection("user@example.com") is False
        
        # Test SQL injection attempts
        assert db_security_service.detect_sql_injection("'; DROP TABLE users; --") is True
        assert db_security_service.detect_sql_injection("1' OR '1'='1") is True
        assert db_security_service.detect_sql_injection("admin'--") is True
    
    def test_sanitize_input(self, db_security_service):
        """Test input sanitization"""
        # Test normal input
        sanitized = db_security_service.sanitize_input("normal input")
        assert sanitized == "normal input"
        
        # Test input with SQL injection
        malicious = "'; DROP TABLE users; --"
        sanitized = db_security_service.sanitize_input(malicious)
        assert "DROP" not in sanitized
        assert "TABLE" not in sanitized
        assert ";" not in sanitized
    
    def test_audit_database_access(self, db_security_service):
        """Test database access auditing"""
        user_id = "user_123"
        operation = "SELECT"
        table = "users"
        
        with patch.object(db_security_service, 'log_access') as mock_log:
            db_security_service.audit_database_access(user_id, operation, table)
            mock_log.assert_called_once_with(user_id, operation, table)

class TestInputValidationService:
    """Unit tests for InputValidationService"""
    
    @pytest.fixture
    def validation_service(self):
        return InputValidationService()
    
    def test_initialization(self, validation_service):
        """Test service initialization"""
        assert validation_service is not None
        assert hasattr(validation_service, 'max_length')
    
    def test_validate_email(self, validation_service):
        """Test email validation"""
        # Test valid emails
        assert validation_service.validate_email("test@example.com") is True
        assert validation_service.validate_email("user.name+tag@domain.co.uk") is True
        
        # Test invalid emails
        assert validation_service.validate_email("invalid-email") is False
        assert validation_service.validate_email("@example.com") is False
        assert validation_service.validate_email("test@") is False
    
    def test_validate_password_strength(self, validation_service):
        """Test password strength validation"""
        # Test strong passwords
        assert validation_service.validate_password_strength("StrongPass123!") is True
        assert validation_service.validate_password_strength("MySecure#Password2024") is True
        
        # Test weak passwords
        assert validation_service.validate_password_strength("123") is False
        assert validation_service.validate_password_strength("password") is False
        assert validation_service.validate_password_strength("Password") is False  # No numbers/special chars
    
    def test_validate_json_input(self, validation_service):
        """Test JSON input validation"""
        # Test valid JSON
        assert validation_service.validate_json_input('{"key": "value"}') is True
        assert validation_service.validate_json_input('[1, 2, 3]') is True
        
        # Test invalid JSON
        assert validation_service.validate_json_input('{"key": "value"') is False
        assert validation_service.validate_json_input('invalid json') is False
    
    def test_detect_xss(self, validation_service):
        """Test XSS detection"""
        # Test safe content
        assert validation_service.detect_xss("Normal text content") is False
        assert validation_service.detect_xss("User input without scripts") is False
        
        # Test XSS attempts
        assert validation_service.detect_xss("<script>alert('xss')</script>") is True
        assert validation_service.detect_xss("javascript:alert('xss')") is True
        assert validation_service.detect_xss("<img src=x onerror=alert('xss')>") is True
    
    def test_sanitize_html(self, validation_service):
        """Test HTML sanitization"""
        # Test safe HTML
        safe_html = "<p>This is safe content</p>"
        sanitized = validation_service.sanitize_html(safe_html)
        assert "<p>" in sanitized
        
        # Test dangerous HTML
        dangerous_html = "<script>alert('xss')</script><p>Content</p>"
        sanitized = validation_service.sanitize_html(dangerous_html)
        assert "<script>" not in sanitized
        assert "<p>" in sanitized

class TestTokenRevocationService:
    """Unit tests for TokenRevocationService"""
    
    @pytest.fixture
    def token_service(self, db_session):
        return TokenRevocationService(db_session)
    
    def test_initialization(self, token_service):
        """Test service initialization"""
        assert token_service is not None
        assert hasattr(token_service, 'db')
    
    def test_revoke_token(self, token_service):
        """Test token revocation"""
        token_id = "token_123"
        user_id = "user_123"
        
        with patch.object(token_service, 'add_to_blacklist') as mock_blacklist:
            result = token_service.revoke_token(token_id, user_id)
            assert result is True
            mock_blacklist.assert_called_once_with(token_id, user_id)
    
    def test_is_token_revoked(self, token_service):
        """Test token revocation check"""
        token_id = "token_123"
        
        # Test non-revoked token
        with patch.object(token_service, 'check_blacklist', return_value=False):
            is_revoked = token_service.is_token_revoked(token_id)
            assert is_revoked is False
        
        # Test revoked token
        with patch.object(token_service, 'check_blacklist', return_value=True):
            is_revoked = token_service.is_token_revoked(token_id)
            assert is_revoked is True
    
    def test_cleanup_expired_tokens(self, token_service):
        """Test cleanup of expired tokens"""
        with patch.object(token_service, 'remove_expired_tokens') as mock_cleanup:
            token_service.cleanup_expired_tokens()
            mock_cleanup.assert_called_once()
    
    def test_revoke_all_user_tokens(self, token_service):
        """Test revoking all tokens for a user"""
        user_id = "user_123"
        
        with patch.object(token_service, 'blacklist_user_tokens') as mock_blacklist:
            result = token_service.revoke_all_user_tokens(user_id)
            assert result is True
            mock_blacklist.assert_called_once_with(user_id)

class TestWebSocketSecurityService:
    """Unit tests for WebSocketSecurityService"""
    
    @pytest.fixture
    def ws_security_service(self):
        return WebSocketSecurityService()
    
    def test_initialization(self, ws_security_service):
        """Test service initialization"""
        assert ws_security_service is not None
        assert hasattr(ws_security_service, 'rate_limiter')
    
    def test_validate_websocket_token(self, ws_security_service):
        """Test WebSocket token validation"""
        # Test valid token
        with patch('jwt.decode') as mock_decode:
            mock_decode.return_value = {"user_id": "user_123", "workspace_id": "ws_123"}
            
            result = ws_security_service.validate_websocket_token("valid_token")
            assert result == {"user_id": "user_123", "workspace_id": "ws_123"}
    
    def test_validate_websocket_token_invalid(self, ws_security_service):
        """Test WebSocket token validation with invalid token"""
        with patch('jwt.decode') as mock_decode:
            mock_decode.side_effect = Exception("Invalid token")
            
            result = ws_security_service.validate_websocket_token("invalid_token")
            assert result is None
    
    def test_validate_message_content(self, ws_security_service):
        """Test WebSocket message content validation"""
        # Test valid message
        valid_message = {
            "type": "chat_message",
            "content": "Hello, how can I help?",
            "session_id": "session_123"
        }
        
        is_valid = ws_security_service.validate_message_content(valid_message)
        assert is_valid is True
        
        # Test invalid message
        invalid_message = {
            "type": "chat_message",
            "content": "<script>alert('xss')</script>",
            "session_id": "session_123"
        }
        
        is_valid = ws_security_service.validate_message_content(invalid_message)
        assert is_valid is False
    
    def test_rate_limit_websocket_connection(self, ws_security_service):
        """Test WebSocket connection rate limiting"""
        user_id = "user_123"
        
        # Test within rate limit
        with patch.object(ws_security_service, 'rate_limiter') as mock_limiter:
            mock_limiter.is_allowed.return_value = True
            
            is_allowed = ws_security_service.rate_limit_connection(user_id)
            assert is_allowed is True
        
        # Test rate limit exceeded
        with patch.object(ws_security_service, 'rate_limiter') as mock_limiter:
            mock_limiter.is_allowed.return_value = False
            
            is_allowed = ws_security_service.rate_limit_connection(user_id)
            assert is_allowed is False
    
    def test_sanitize_websocket_message(self, ws_security_service):
        """Test WebSocket message sanitization"""
        message = {
            "type": "chat_message",
            "content": "Hello <script>alert('xss')</script> world",
            "session_id": "session_123"
        }
        
        sanitized = ws_security_service.sanitize_message(message)
        
        assert sanitized["type"] == "chat_message"
        assert "<script>" not in sanitized["content"]
        assert "Hello" in sanitized["content"]
        assert "world" in sanitized["content"]
        assert sanitized["session_id"] == "session_123"

if __name__ == "__main__":
    pytest.main([__file__, "-v"])

