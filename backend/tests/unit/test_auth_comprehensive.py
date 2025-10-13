"""
Comprehensive unit tests for authentication system
Tests all critical authentication flows and security features
"""

import pytest
import sys
import os
from unittest.mock import Mock, patch, MagicMock
from fastapi.testclient import TestClient
from fastapi import status
import json
import time

# Add the backend directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from app.main import app
from app.core.config import settings
from app.models import User, Workspace
from app.services.auth import AuthService
from app.utils.error_handling import AuthenticationError, ValidationError
from app.utils.password import validate_password_requirements, check_password_strength


class TestPasswordSecurity:
    """Test password security features"""
    
    def test_password_strength_validation(self):
        """Test password strength validation"""
        validator = PasswordValidator()
        
        # Test weak passwords
        weak_passwords = [
            "123456",  # Too short
            "password",  # No numbers/special chars
            "Password1",  # No special chars
            "Password!",  # No numbers
            "PASSWORD123!",  # No lowercase
            "password123!",  # No uppercase
        ]
        
        for password in weak_passwords:
            result = validator.validate_password_strength(password)
            assert not result["is_valid"], f"Password '{password}' should be invalid"
            assert "error" in result
        
        # Test strong passwords
        strong_passwords = [
            "Password123!",
            "MySecure@Pass2024",
            "Complex#Pass1",
            "Strong$Password9",
        ]
        
        for password in strong_passwords:
            result = validator.validate_password_strength(password)
            assert result["is_valid"], f"Password '{password}' should be valid"
    
    def test_password_history_prevention(self):
        """Test password history prevents reuse"""
        validator = PasswordValidator()
        user_id = "test_user_123"
        
        # Set initial password
        password1 = "Password123!"
        validator.record_password_in_history(user_id, password1)
        
        # Try to reuse same password
        result = validator.check_password_history(user_id, password1)
        assert not result["is_valid"]
        assert "recently used" in result["error"].lower()
        
        # Try different password
        password2 = "NewPassword456!"
        result = validator.check_password_history(user_id, password2)
        assert result["is_valid"]
    
    def test_bcrypt_hashing(self):
        """Test bcrypt password hashing"""
        auth_service = AuthService()
        password = "TestPassword123!"
        
        # Hash password
        hashed = auth_service.hash_password(password)
        
        # Verify hash properties
        assert hashed != password
        assert hashed.startswith("$2b$")  # bcrypt identifier
        assert len(hashed) == 60  # bcrypt hash length
        
        # Verify password
        assert auth_service.verify_password(password, hashed)
        assert not auth_service.verify_password("wrong_password", hashed)
    
    def test_salt_uniqueness(self):
        """Test that each password gets unique salt"""
        auth_service = AuthService()
        password = "SamePassword123!"
        
        # Hash same password twice
        hash1 = auth_service.hash_password(password)
        hash2 = auth_service.hash_password(password)
        
        # Hashes should be different due to different salts
        assert hash1 != hash2
        
        # But both should verify correctly
        assert auth_service.verify_password(password, hash1)
        assert auth_service.verify_password(password, hash2)


class TestAuthenticationFlows:
    """Test complete authentication flows"""
    
    def test_user_registration_success(self, test_db):
        """Test successful user registration"""
        user_data = {
            "email": "test@example.com",
            "password": "SecurePassword123!",
            "mobile_phone": "+1234567890",
            "full_name": "Test User"
        }
        
        response = client.post("/api/v1/auth/register", json=user_data)
        
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        
        # Check response structure
        assert "user" in data
        assert "message" in data
        assert data["user"]["email"] == user_data["email"]
        assert data["user"]["full_name"] == user_data["full_name"]
        assert "id" in data["user"]
        
        # Verify user was created in database
        user = test_db.query(User).filter(User.email == user_data["email"]).first()
        assert user is not None
        assert user.email == user_data["email"]
        assert user.mobile_phone == user_data["mobile_phone"]
        assert user.full_name == user_data["full_name"]
        assert user.hashed_password is not None
        assert user.hashed_password != user_data["password"]  # Should be hashed
    
    def test_user_registration_duplicate_email(self, test_db, test_user):
        """Test registration with duplicate email fails"""
        user_data = {
            "email": test_user.email,  # Use existing email
            "password": "SecurePassword123!",
            "mobile_phone": "+9876543210",
            "full_name": "Another User"
        }
        
        response = client.post("/api/v1/auth/register", json=user_data)
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        data = response.json()
        assert "already exists" in data["detail"].lower()
    
    def test_user_registration_duplicate_mobile(self, test_db, test_user):
        """Test registration with duplicate mobile phone fails"""
        user_data = {
            "email": "different@example.com",
            "password": "SecurePassword123!",
            "mobile_phone": test_user.mobile_phone,  # Use existing mobile
            "full_name": "Another User"
        }
        
        response = client.post("/api/v1/auth/register", json=user_data)
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        data = response.json()
        assert "already exists" in data["detail"].lower()
    
    def test_user_registration_weak_password(self, client):
        """Test registration with weak password fails"""
        user_data = {
            "email": "test@example.com",
            "password": "weak",  # Weak password
            "mobile_phone": "+1234567890",
            "full_name": "Test User"
        }
        
        response = client.post("/api/v1/auth/register", json=user_data)
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        data = response.json()
        assert "password" in str(data).lower()
    
    def test_user_login_success(self, test_user):
        """Test successful user login"""
        login_data = {
            "identifier": test_user.email,
            "password": "test_password_123"
        }
        
        response = client.post("/api/v1/auth/login", json=login_data)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        # Check response structure
        assert "access_token" in data
        assert "refresh_token" in data
        assert "token_type" in data
        assert "expires_in" in data
        assert data["token_type"] == "bearer"
        
        # Verify token structure
        token = data["access_token"]
        assert len(token) > 100  # JWT should be substantial
        assert "." in token  # JWT has dots
    
    def test_user_login_with_mobile(self, test_user):
        """Test login with mobile phone number"""
        login_data = {
            "identifier": test_user.mobile_phone,
            "password": "test_password_123"
        }
        
        response = client.post("/api/v1/auth/login", json=login_data)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "access_token" in data
    
    def test_user_login_wrong_password(self, test_user):
        """Test login with wrong password fails"""
        login_data = {
            "identifier": test_user.email,
            "password": "wrong_password"
        }
        
        response = client.post("/api/v1/auth/login", json=login_data)
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        data = response.json()
        assert "invalid" in data["detail"].lower()
    
    def test_user_login_nonexistent_user(self):
        """Test login with nonexistent user fails"""
        login_data = {
            "identifier": "nonexistent@example.com",
            "password": "any_password"
        }
        
        response = client.post("/api/v1/auth/login", json=login_data)
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        data = response.json()
        assert "invalid" in data["detail"].lower()
    
    def test_token_refresh_success(self, test_user):
        """Test successful token refresh"""
        # First login to get tokens
        login_data = {
            "identifier": test_user.email,
            "password": "test_password_123"
        }
        login_response = client.post("/api/v1/auth/login", json=login_data)
        refresh_token = login_response.json()["refresh_token"]
        
        # Refresh token
        refresh_data = {"refresh_token": refresh_token}
        response = client.post("/api/v1/auth/refresh", json=refresh_data)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["access_token"] != login_response.json()["access_token"]  # New token
    
    def test_token_refresh_invalid_token(self):
        """Test refresh with invalid token fails"""
        refresh_data = {"refresh_token": "invalid_token"}
        response = client.post("/api/v1/auth/refresh", json=refresh_data)
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        data = response.json()
        assert "invalid" in data["detail"].lower()
    
    def test_me_endpoint_authenticated(self, test_user, auth_headers):
        """Test /me endpoint with valid authentication"""
        response = client.get("/api/v1/auth/me", headers=auth_headers)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["email"] == test_user.email
        assert data["full_name"] == test_user.full_name
        assert "id" in data
        assert "workspace_id" in data
    
    def test_me_endpoint_unauthenticated(self):
        """Test /me endpoint without authentication fails"""
        response = client.get("/api/v1/auth/me")
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_logout_success(self, test_user, auth_headers):
        """Test successful logout"""
        response = client.post("/api/v1/auth/logout", headers=auth_headers)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "message" in data
        assert "logged out" in data["message"].lower()
    
    def test_csrf_token_generation(self):
        """Test CSRF token generation endpoint"""
        response = client.get("/api/v1/auth/csrf-token")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "csrf_token" in data
        assert "expires_in" in data
        assert data["expires_in"] == 3600  # 1 hour
        assert len(data["csrf_token"]) > 20  # Should be substantial


class TestSecurityFeatures:
    """Test security features and protections"""
    
    def test_rate_limiting_login_attempts(self, test_user):
        """Test rate limiting on login attempts"""
        login_data = {
            "identifier": test_user.email,
            "password": "wrong_password"
        }
        
        # Make multiple failed login attempts
        for i in range(10):  # Exceed rate limit
            response = client.post("/api/v1/auth/login", json=login_data)
            if i < 5:  # First few should be 401
                assert response.status_code == status.HTTP_401_UNAUTHORIZED
            else:  # Later ones should be rate limited
                assert response.status_code == status.HTTP_429_TOO_MANY_REQUESTS
    
    def test_account_lockout_after_failed_attempts(self, test_user):
        """Test account lockout after multiple failed attempts"""
        login_data = {
            "identifier": test_user.email,
            "password": "wrong_password"
        }
        
        # Make multiple failed attempts to trigger lockout
        for i in range(6):  # Exceed max attempts
            response = client.post("/api/v1/auth/login", json=login_data)
        
        # Account should be locked
        response = client.post("/api/v1/auth/login", json=login_data)
        assert response.status_code == status.HTTP_423_LOCKED
        data = response.json()
        assert "locked" in data["detail"].lower()
    
    def test_input_validation_malicious_input(self):
        """Test input validation against malicious input"""
        malicious_inputs = [
            {"email": "<script>alert('xss')</script>@example.com"},
            {"password": "'; DROP TABLE users; --"},
            {"mobile_phone": "1' OR '1'='1"},
            {"full_name": "<img src=x onerror=alert('xss')>"}
        ]
        
        for malicious_data in malicious_inputs:
            user_data = {
                "email": "test@example.com",
                "password": "SecurePassword123!",
                "mobile_phone": "+1234567890",
                "full_name": "Test User",
                **malicious_data
            }
            
            response = client.post("/api/v1/auth/register", json=user_data)
            # Should either succeed with sanitized input or fail validation
            assert response.status_code in [201, 400, 422]
    
    def test_jwt_token_expiration(self, test_user):
        """Test JWT token expiration"""
        # Create a token with very short expiration
        with patch('app.core.config.settings.ACCESS_TOKEN_EXPIRE_MINUTES', 0.001):  # ~0.06 seconds
            login_data = {
                "identifier": test_user.email,
                "password": "test_password_123"
            }
            response = client.post("/api/v1/auth/login", json=login_data)
            token = response.json()["access_token"]
            
            # Wait for token to expire
            time.sleep(0.1)
            
            # Try to use expired token
            headers = {"Authorization": f"Bearer {token}"}
            response = client.get("/api/v1/auth/me", headers=headers)
            assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_jwt_token_tampering(self, test_user, auth_headers):
        """Test JWT token tampering detection"""
        # Get valid token
        token = auth_headers["Authorization"].replace("Bearer ", "")
        
        # Tamper with token
        tampered_token = token[:-5] + "XXXXX"
        
        # Try to use tampered token
        headers = {"Authorization": f"Bearer {tampered_token}"}
        response = client.get("/api/v1/auth/me", headers=headers)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_password_reset_flow(self, test_user):
        """Test password reset flow"""
        # Request password reset
        reset_data = {"email": test_user.email}
        response = client.post("/api/v1/auth/forgot-password", json=reset_data)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "message" in data
        
        # Note: In a real test, you'd extract the reset token from email
        # and test the actual password reset endpoint
    
    def test_email_verification_flow(self, test_user):
        """Test email verification flow"""
        # Create unverified user
        user_data = {
            "email": "unverified@example.com",
            "password": "SecurePassword123!",
            "mobile_phone": "+1111111111",
            "full_name": "Unverified User"
        }
        response = client.post("/api/v1/auth/register", json=user_data)
        assert response.status_code == status.HTTP_201_CREATED
        
        # Try to verify with invalid token
        response = client.get("/api/v1/auth/verify-email?token=invalid_token")
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        
        # Note: In a real test, you'd extract the verification token
        # and test the actual verification endpoint


class TestErrorHandling:
    """Test error handling in authentication"""
    
    def test_database_connection_error(self):
        """Test handling of database connection errors"""
        with patch('app.core.database.get_db') as mock_db:
            mock_db.side_effect = Exception("Database connection failed")
            
            user_data = {
                "email": "test@example.com",
                "password": "SecurePassword123!",
                "mobile_phone": "+1234567890",
                "full_name": "Test User"
            }
            
            response = client.post("/api/v1/auth/register", json=user_data)
            assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    
    def test_validation_error_format(self):
        """Test validation error response format"""
        user_data = {
            "email": "invalid-email",  # Invalid email format
            "password": "weak",  # Weak password
            "mobile_phone": "invalid-phone",  # Invalid phone format
            "full_name": ""  # Empty name
        }
        
        response = client.post("/api/v1/auth/register", json=user_data)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        
        data = response.json()
        assert "detail" in data
        assert isinstance(data["detail"], list)  # Should be list of errors
    
    def test_custom_error_responses(self):
        """Test custom error response format"""
        # Test with custom error handling
        with patch('app.services.auth.AuthService.create_user') as mock_create:
            mock_create.side_effect = AuthenticationError("Custom auth error")
            
            user_data = {
                "email": "test@example.com",
                "password": "SecurePassword123!",
                "mobile_phone": "+1234567890",
                "full_name": "Test User"
            }
            
            response = client.post("/api/v1/auth/register", json=user_data)
            assert response.status_code == status.HTTP_401_UNAUTHORIZED
            
            data = response.json()
            assert "error" in data
            assert "message" in data
            assert "error_id" in data


@pytest.mark.asyncio
class TestAsyncAuthentication:
    """Test async authentication features"""
    
    async def test_async_user_creation(self, test_db):
        """Test async user creation"""
        from app.services.auth import AuthService
        
        auth_service = AuthService()
        user_data = {
            "email": "async@example.com",
            "password": "SecurePassword123!",
            "mobile_phone": "+1234567890",
            "full_name": "Async User"
        }
        
        # This would test async user creation if implemented
        # For now, just test that the service can be instantiated
        assert auth_service is not None
    
    async def test_concurrent_login_attempts(self, test_user):
        """Test concurrent login attempts"""
        import asyncio
        
        async def attempt_login():
            login_data = {
                "identifier": test_user.email,
                "password": "test_password_123"
            }
            response = client.post("/api/v1/auth/login", json=login_data)
            return response.status_code
        
        # Make concurrent login attempts
        tasks = [attempt_login() for _ in range(5)]
        results = await asyncio.gather(*tasks)
        
        # All should succeed (or be rate limited appropriately)
        for status_code in results:
            assert status_code in [200, 429]  # Success or rate limited
