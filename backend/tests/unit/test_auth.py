"""
Unit tests for authentication module
"""
import pytest
import sys
import os
from unittest.mock import Mock, patch
from fastapi.testclient import TestClient

# Add the backend directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))
from app.main import app
from app.core.config import settings
from app.models.user import User
from app.services.auth_service import AuthService
from app.core.database import get_db

client = TestClient(app)

class TestAuthService:
    """Test cases for AuthService"""
    
    def setup_method(self):
        """Setup for each test method"""
        self.auth_service = AuthService()
    
    def test_generate_password_hash(self):
        """Test password hashing"""
        password = "test_password_123"
        hashed = self.auth_service.hash_password(password)
        
        assert hashed != password
        assert len(hashed) > 50
        assert self.auth_service.verify_password(password, hashed)
    
    def test_verify_password_correct(self):
        """Test password verification with correct password"""
        password = "test_password_123"
        hashed = self.auth_service.hash_password(password)
        
        assert self.auth_service.verify_password(password, hashed) is True
    
    def test_verify_password_incorrect(self):
        """Test password verification with incorrect password"""
        password = "test_password_123"
        wrong_password = "wrong_password"
        hashed = self.auth_service.hash_password(password)
        
        assert self.auth_service.verify_password(wrong_password, hashed) is False
    
    def test_generate_jwt_token(self):
        """Test JWT token generation"""
        user_id = "test_user_123"
        token = self.auth_service.create_access_token(user_id)
        
        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 50
    
    def test_verify_jwt_token_valid(self):
        """Test JWT token verification with valid token"""
        user_id = "test_user_123"
        token = self.auth_service.create_access_token(user_id)
        
        payload = self.auth_service.verify_token(token)
        assert payload is not None
        assert payload.get("sub") == user_id
    
    def test_verify_jwt_token_invalid(self):
        """Test JWT token verification with invalid token"""
        invalid_token = "invalid_token_123"
        
        with pytest.raises(Exception):
            self.auth_service.verify_token(invalid_token)
    
    def test_password_requirements(self):
        """Test password meets security requirements"""
        # Test minimum length
        short_password = "123"
        assert not self.auth_service.validate_password_strength(short_password)
        
        # Test valid password
        valid_password = "SecurePassword123!"
        assert self.auth_service.validate_password_strength(valid_password)
        
        # Test missing uppercase
        no_upper = "securepassword123!"
        assert not self.auth_service.validate_password_strength(no_upper)
        
        # Test missing lowercase
        no_lower = "SECUREPASSWORD123!"
        assert not self.auth_service.validate_password_strength(no_lower)
        
        # Test missing numbers
        no_numbers = "SecurePassword!"
        assert not self.auth_service.validate_password_strength(no_numbers)
        
        # Test missing special characters
        no_special = "SecurePassword123"
        assert not self.auth_service.validate_password_strength(no_special)

class TestAuthEndpoints:
    """Test cases for authentication endpoints"""
    
    def test_register_user_success(self):
        """Test successful user registration"""
        user_data = {
            "email": "test@example.com",
            "password": "SecurePassword123!",
            "full_name": "Test User"
        }
        
        with patch('app.services.auth_service.AuthService.create_user') as mock_create:
            mock_create.return_value = User(id="123", email="test@example.com")
            
            response = client.post("/api/v1/auth/register", json=user_data)
            
            assert response.status_code == 201
            assert "user" in response.json()
    
    def test_register_user_invalid_email(self):
        """Test user registration with invalid email"""
        user_data = {
            "email": "invalid-email",
            "password": "SecurePassword123!",
            "full_name": "Test User"
        }
        
        response = client.post("/api/v1/auth/register", json=user_data)
        
        assert response.status_code == 422
        assert "email" in response.json()["detail"][0]["loc"]
    
    def test_register_user_weak_password(self):
        """Test user registration with weak password"""
        user_data = {
            "email": "test@example.com",
            "password": "123",
            "full_name": "Test User"
        }
        
        response = client.post("/api/v1/auth/register", json=user_data)
        
        assert response.status_code == 422
        assert "password" in response.json()["detail"][0]["loc"]
    
    def test_login_success(self):
        """Test successful user login"""
        login_data = {
            "email": "test@example.com",
            "password": "SecurePassword123!"
        }
        
        with patch('app.services.auth_service.AuthService.authenticate_user') as mock_auth:
            mock_auth.return_value = User(id="123", email="test@example.com")
            
            response = client.post("/api/v1/auth/login", json=login_data)
            
            assert response.status_code == 200
            assert "access_token" in response.json()
            assert "token_type" in response.json()
    
    def test_login_invalid_credentials(self):
        """Test login with invalid credentials"""
        login_data = {
            "email": "test@example.com",
            "password": "wrong_password"
        }
        
        with patch('app.services.auth_service.AuthService.authenticate_user') as mock_auth:
            mock_auth.return_value = None
            
            response = client.post("/api/v1/auth/login", json=login_data)
            
            assert response.status_code == 401
            assert "Invalid credentials" in response.json()["detail"]
    
    def test_get_current_user_success(self):
        """Test getting current user with valid token"""
        user_id = "test_user_123"
        token = AuthService().create_access_token(user_id)
        
        with patch('app.services.auth_service.AuthService.get_user_by_id') as mock_get_user:
            mock_get_user.return_value = User(id=user_id, email="test@example.com")
            
            response = client.get(
                "/api/v1/auth/me",
                headers={"Authorization": f"Bearer {token}"}
            )
            
            assert response.status_code == 200
            assert response.json()["id"] == user_id
    
    def test_get_current_user_invalid_token(self):
        """Test getting current user with invalid token"""
        response = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": "Bearer invalid_token"}
        )
        
        assert response.status_code == 401
        assert "Invalid token" in response.json()["detail"]
    
    def test_refresh_token_success(self):
        """Test successful token refresh"""
        user_id = "test_user_123"
        refresh_token = AuthService().create_refresh_token(user_id)
        
        with patch('app.services.auth_service.AuthService.get_user_by_id') as mock_get_user:
            mock_get_user.return_value = User(id=user_id, email="test@example.com")
            
            response = client.post(
                "/api/v1/auth/refresh",
                json={"refresh_token": refresh_token}
            )
            
            assert response.status_code == 200
            assert "access_token" in response.json()
    
    def test_logout_success(self):
        """Test successful user logout"""
        user_id = "test_user_123"
        token = AuthService().create_access_token(user_id)
        
        with patch('app.services.auth_service.AuthService.revoke_token') as mock_revoke:
            mock_revoke.return_value = True
            
            response = client.post(
                "/api/v1/auth/logout",
                headers={"Authorization": f"Bearer {token}"}
            )
            
            assert response.status_code == 200
            assert "Logged out successfully" in response.json()["message"]
