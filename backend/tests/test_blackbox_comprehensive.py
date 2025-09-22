"""
Comprehensive black-box tests for CustomerCareGPT
Tests the system from an external user perspective without knowledge of internal implementation
"""

import pytest
import asyncio
import json
import tempfile
import os
import time
from datetime import datetime, timedelta
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

class TestUserRegistrationBlackBox:
    """Black-box tests for user registration from user perspective"""
    
    def test_successful_user_registration(self):
        """Test successful user registration as a new user would experience it"""
        user_data = {
            "email": "newuser@example.com",
            "password": "SecurePassword123!",
            "full_name": "New User",
            "workspace_name": "My Company"
        }
        
        response = client.post("/api/v1/auth/register", json=user_data)
        
        # Verify response
        assert response.status_code == 201
        data = response.json()
        
        # Verify response contains expected fields
        assert "user_id" in data
        assert "workspace_id" in data
        assert "email" in data
        assert data["email"] == user_data["email"]
        
        # Verify user_id and workspace_id are valid UUIDs or similar
        assert len(data["user_id"]) > 0
        assert len(data["workspace_id"]) > 0
    
    def test_registration_with_invalid_email(self):
        """Test registration with invalid email format"""
        user_data = {
            "email": "invalid-email-format",
            "password": "SecurePassword123!",
            "full_name": "Test User",
            "workspace_name": "Test Company"
        }
        
        response = client.post("/api/v1/auth/register", json=user_data)
        
        # Should return validation error
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data
    
    def test_registration_with_weak_password(self):
        """Test registration with weak password"""
        user_data = {
            "email": "test@example.com",
            "password": "123",
            "full_name": "Test User",
            "workspace_name": "Test Company"
        }
        
        response = client.post("/api/v1/auth/register", json=user_data)
        
        # Should return validation error
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data
    
    def test_registration_with_missing_fields(self):
        """Test registration with missing required fields"""
        user_data = {
            "email": "test@example.com",
            "password": "SecurePassword123!"
            # Missing full_name and workspace_name
        }
        
        response = client.post("/api/v1/auth/register", json=user_data)
        
        # Should return validation error
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data
    
    def test_registration_with_duplicate_email(self):
        """Test registration with already existing email"""
        user_data = {
            "email": "duplicate@example.com",
            "password": "SecurePassword123!",
            "full_name": "Test User",
            "workspace_name": "Test Company"
        }
        
        # First registration should succeed
        response1 = client.post("/api/v1/auth/register", json=user_data)
        assert response1.status_code == 201
        
        # Second registration with same email should fail
        response2 = client.post("/api/v1/auth/register", json=user_data)
        assert response2.status_code == 400
        data = response2.json()
        assert "email" in data.get("detail", "").lower()

class TestUserAuthenticationBlackBox:
    """Black-box tests for user authentication from user perspective"""
    
    def test_successful_login(self):
        """Test successful user login"""
        # First register a user
        user_data = {
            "email": "logintest@example.com",
            "password": "LoginTest123!",
            "full_name": "Login Test User",
            "workspace_name": "Login Test Company"
        }
        
        register_response = client.post("/api/v1/auth/register", json=user_data)
        assert register_response.status_code == 201
        
        # Then login
        login_data = {
            "email": "logintest@example.com",
            "password": "LoginTest123!"
        }
        
        response = client.post("/api/v1/auth/login", json=login_data)
        
        # Verify login response
        assert response.status_code == 200
        data = response.json()
        
        # Verify response contains expected fields
        assert "access_token" in data
        assert "token_type" in data
        assert "user" in data
        assert data["token_type"] == "bearer"
        assert data["user"]["email"] == login_data["email"]
        
        # Verify token is not empty
        assert len(data["access_token"]) > 0
    
    def test_login_with_wrong_password(self):
        """Test login with incorrect password"""
        # First register a user
        user_data = {
            "email": "wrongpass@example.com",
            "password": "CorrectPassword123!",
            "full_name": "Wrong Pass User",
            "workspace_name": "Wrong Pass Company"
        }
        
        register_response = client.post("/api/v1/auth/register", json=user_data)
        assert register_response.status_code == 201
        
        # Then try to login with wrong password
        login_data = {
            "email": "wrongpass@example.com",
            "password": "WrongPassword123!"
        }
        
        response = client.post("/api/v1/auth/login", json=login_data)
        
        # Should return authentication error
        assert response.status_code == 401
        data = response.json()
        assert "detail" in data
    
    def test_login_with_nonexistent_email(self):
        """Test login with non-existent email"""
        login_data = {
            "email": "nonexistent@example.com",
            "password": "SomePassword123!"
        }
        
        response = client.post("/api/v1/auth/login", json=login_data)
        
        # Should return authentication error
        assert response.status_code == 401
        data = response.json()
        assert "detail" in data
    
    def test_login_with_missing_credentials(self):
        """Test login with missing email or password"""
        # Missing password
        login_data = {
            "email": "test@example.com"
        }
        
        response = client.post("/api/v1/auth/login", json=login_data)
        assert response.status_code == 422
        
        # Missing email
        login_data = {
            "password": "SomePassword123!"
        }
        
        response = client.post("/api/v1/auth/login", json=login_data)
        assert response.status_code == 422

class TestDocumentUploadBlackBox:
    """Black-box tests for document upload from user perspective"""
    
    def test_successful_document_upload(self):
        """Test successful document upload"""
        # First register and login
        user_data = {
            "email": "docupload@example.com",
            "password": "DocUpload123!",
            "full_name": "Doc Upload User",
            "workspace_name": "Doc Upload Company"
        }
        
        register_response = client.post("/api/v1/auth/register", json=user_data)
        assert register_response.status_code == 201
        
        login_data = {
            "email": "docupload@example.com",
            "password": "DocUpload123!"
        }
        
        login_response = client.post("/api/v1/auth/login", json=login_data)
        assert login_response.status_code == 200
        
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # Create a test document
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("This is a test document for upload testing.")
            temp_file_path = f.name
        
        try:
            # Upload document
            with open(temp_file_path, 'rb') as f:
                files = {"file": ("test_document.txt", f, "text/plain")}
                response = client.post("/api/v1/documents/upload", files=files, headers=headers)
                
                # Verify upload response
                assert response.status_code == 200
                data = response.json()
                
                # Verify response contains expected fields
                assert "document_id" in data
                assert "job_id" in data
                assert "status" in data
                assert data["status"] == "processing"
                
                # Verify document_id is not empty
                assert len(data["document_id"]) > 0
        
        finally:
            os.unlink(temp_file_path)
    
    def test_document_upload_without_authentication(self):
        """Test document upload without authentication"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("Test document")
            temp_file_path = f.name
        
        try:
            with open(temp_file_path, 'rb') as f:
                files = {"file": ("test_document.txt", f, "text/plain")}
                response = client.post("/api/v1/documents/upload", files=files)
                
                # Should return authentication error
                assert response.status_code == 401
        
        finally:
            os.unlink(temp_file_path)
    
    def test_document_upload_with_invalid_file_type(self):
        """Test document upload with unsupported file type"""
        # First register and login
        user_data = {
            "email": "invalidfile@example.com",
            "password": "InvalidFile123!",
            "full_name": "Invalid File User",
            "workspace_name": "Invalid File Company"
        }
        
        register_response = client.post("/api/v1/auth/register", json=user_data)
        assert register_response.status_code == 201
        
        login_data = {
            "email": "invalidfile@example.com",
            "password": "InvalidFile123!"
        }
        
        login_response = client.post("/api/v1/auth/login", json=login_data)
        assert login_response.status_code == 200
        
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # Create an image file (unsupported type)
        with tempfile.NamedTemporaryFile(mode='w', suffix='.jpg', delete=False) as f:
            f.write("Fake image content")
            temp_file_path = f.name
        
        try:
            with open(temp_file_path, 'rb') as f:
                files = {"file": ("test_image.jpg", f, "image/jpeg")}
                response = client.post("/api/v1/documents/upload", files=files, headers=headers)
                
                # Should return validation error
                assert response.status_code == 400
                data = response.json()
                assert "detail" in data
        
        finally:
            os.unlink(temp_file_path)
    
    def test_document_upload_with_large_file(self):
        """Test document upload with file that's too large"""
        # First register and login
        user_data = {
            "email": "largefile@example.com",
            "password": "LargeFile123!",
            "full_name": "Large File User",
            "workspace_name": "Large File Company"
        }
        
        register_response = client.post("/api/v1/auth/register", json=user_data)
        assert register_response.status_code == 201
        
        login_data = {
            "email": "largefile@example.com",
            "password": "LargeFile123!"
        }
        
        login_response = client.post("/api/v1/auth/login", json=login_data)
        assert login_response.status_code == 200
        
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # Create a large file (simulate by creating a file with repeated content)
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            # Write 20MB of content
            for _ in range(20000):
                f.write("This is a large file content. " * 50)
            temp_file_path = f.name
        
        try:
            with open(temp_file_path, 'rb') as f:
                files = {"file": ("large_document.txt", f, "text/plain")}
                response = client.post("/api/v1/documents/upload", files=files, headers=headers)
                
                # Should return file size error
                assert response.status_code == 413
                data = response.json()
                assert "detail" in data
        
        finally:
            os.unlink(temp_file_path)

class TestChatSessionBlackBox:
    """Black-box tests for chat sessions from user perspective"""
    
    def test_create_chat_session(self):
        """Test creating a new chat session"""
        # First register and login
        user_data = {
            "email": "chatsession@example.com",
            "password": "ChatSession123!",
            "full_name": "Chat Session User",
            "workspace_name": "Chat Session Company"
        }
        
        register_response = client.post("/api/v1/auth/register", json=user_data)
        assert register_response.status_code == 201
        
        login_data = {
            "email": "chatsession@example.com",
            "password": "ChatSession123!"
        }
        
        login_response = client.post("/api/v1/auth/login", json=login_data)
        assert login_response.status_code == 200
        
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # Create chat session
        session_data = {
            "user_label": "Test Customer"
        }
        
        response = client.post("/api/v1/chat/sessions", json=session_data, headers=headers)
        
        # Verify session creation
        assert response.status_code == 201
        data = response.json()
        
        # Verify response contains expected fields
        assert "session_id" in data
        assert "user_label" in data
        assert data["user_label"] == "Test Customer"
        
        # Verify session_id is not empty
        assert len(data["session_id"]) > 0
    
    def test_get_chat_sessions(self):
        """Test retrieving user's chat sessions"""
        # First register and login
        user_data = {
            "email": "getchats@example.com",
            "password": "GetChats123!",
            "full_name": "Get Chats User",
            "workspace_name": "Get Chats Company"
        }
        
        register_response = client.post("/api/v1/auth/register", json=user_data)
        assert register_response.status_code == 201
        
        login_data = {
            "email": "getchats@example.com",
            "password": "GetChats123!"
        }
        
        login_response = client.post("/api/v1/auth/login", json=login_data)
        assert login_response.status_code == 200
        
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # Get chat sessions
        response = client.get("/api/v1/chat/sessions", headers=headers)
        
        # Verify response
        assert response.status_code == 200
        data = response.json()
        
        # Verify response is a list
        assert isinstance(data, list)
        
        # If there are sessions, verify structure
        if len(data) > 0:
            session = data[0]
            assert "session_id" in session
            assert "user_label" in session
            assert "created_at" in session
    
    def test_chat_session_without_authentication(self):
        """Test chat session operations without authentication"""
        # Try to create session without auth
        session_data = {"user_label": "Test Customer"}
        response = client.post("/api/v1/chat/sessions", json=session_data)
        assert response.status_code == 401
        
        # Try to get sessions without auth
        response = client.get("/api/v1/chat/sessions")
        assert response.status_code == 401

class TestRAGQueryBlackBox:
    """Black-box tests for RAG queries from user perspective"""
    
    def test_rag_query_with_authentication(self):
        """Test RAG query with proper authentication"""
        # First register and login
        user_data = {
            "email": "ragquery@example.com",
            "password": "RagQuery123!",
            "full_name": "RAG Query User",
            "workspace_name": "RAG Query Company"
        }
        
        register_response = client.post("/api/v1/auth/register", json=user_data)
        assert register_response.status_code == 201
        
        login_data = {
            "email": "ragquery@example.com",
            "password": "RagQuery123!"
        }
        
        login_response = client.post("/api/v1/auth/login", json=login_data)
        assert login_response.status_code == 200
        
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # Create a chat session first
        session_data = {"user_label": "Test Customer"}
        session_response = client.post("/api/v1/chat/sessions", json=session_data, headers=headers)
        assert session_response.status_code == 201
        session_id = session_response.json()["session_id"]
        
        # Send RAG query
        query_data = {
            "query": "How can I get help with my order?",
            "session_id": session_id
        }
        
        response = client.post("/api/v1/rag/query", json=query_data, headers=headers)
        
        # Verify query response
        assert response.status_code == 200
        data = response.json()
        
        # Verify response contains expected fields
        assert "answer" in data
        assert "sources" in data
        assert "response_time_ms" in data
        assert "session_id" in data
        assert data["session_id"] == session_id
        
        # Verify answer is not empty
        assert len(data["answer"]) > 0
        
        # Verify response time is reasonable
        assert data["response_time_ms"] > 0
        assert data["response_time_ms"] < 30000  # Less than 30 seconds
    
    def test_rag_query_without_authentication(self):
        """Test RAG query without authentication"""
        query_data = {
            "query": "Test query",
            "session_id": "test_session"
        }
        
        response = client.post("/api/v1/rag/query", json=query_data)
        assert response.status_code == 401
    
    def test_rag_query_with_missing_session(self):
        """Test RAG query without session ID"""
        # First register and login
        user_data = {
            "email": "nosession@example.com",
            "password": "NoSession123!",
            "full_name": "No Session User",
            "workspace_name": "No Session Company"
        }
        
        register_response = client.post("/api/v1/auth/register", json=user_data)
        assert register_response.status_code == 201
        
        login_data = {
            "email": "nosession@example.com",
            "password": "NoSession123!"
        }
        
        login_response = client.post("/api/v1/auth/login", json=login_data)
        assert login_response.status_code == 200
        
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # Send query without session_id
        query_data = {
            "query": "Test query"
        }
        
        response = client.post("/api/v1/rag/query", json=query_data, headers=headers)
        assert response.status_code == 422
    
    def test_rag_query_with_empty_query(self):
        """Test RAG query with empty query string"""
        # First register and login
        user_data = {
            "email": "emptyquery@example.com",
            "password": "EmptyQuery123!",
            "full_name": "Empty Query User",
            "workspace_name": "Empty Query Company"
        }
        
        register_response = client.post("/api/v1/auth/register", json=user_data)
        assert register_response.status_code == 201
        
        login_data = {
            "email": "emptyquery@example.com",
            "password": "EmptyQuery123!"
        }
        
        login_response = client.post("/api/v1/auth/login", json=login_data)
        assert login_response.status_code == 200
        
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # Create a chat session
        session_data = {"user_label": "Test Customer"}
        session_response = client.post("/api/v1/chat/sessions", json=session_data, headers=headers)
        assert session_response.status_code == 201
        session_id = session_response.json()["session_id"]
        
        # Send empty query
        query_data = {
            "query": "",
            "session_id": session_id
        }
        
        response = client.post("/api/v1/rag/query", json=query_data, headers=headers)
        assert response.status_code == 422

class TestBillingBlackBox:
    """Black-box tests for billing system from user perspective"""
    
    def test_get_billing_status(self):
        """Test getting billing status"""
        # First register and login
        user_data = {
            "email": "billing@example.com",
            "password": "Billing123!",
            "full_name": "Billing User",
            "workspace_name": "Billing Company"
        }
        
        register_response = client.post("/api/v1/auth/register", json=user_data)
        assert register_response.status_code == 201
        
        login_data = {
            "email": "billing@example.com",
            "password": "Billing123!"
        }
        
        login_response = client.post("/api/v1/auth/login", json=login_data)
        assert login_response.status_code == 200
        
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # Get billing status
        response = client.get("/api/v1/billing/status", headers=headers)
        
        # Verify response
        assert response.status_code == 200
        data = response.json()
        
        # Verify response contains expected fields
        assert "tier" in data
        assert "status" in data
        assert "quota_used" in data
        assert "quota_limit" in data
        
        # Verify tier is valid
        assert data["tier"] in ["free", "pro", "enterprise"]
        
        # Verify status is valid
        assert data["status"] in ["active", "inactive", "cancelled"]
    
    def test_billing_status_without_authentication(self):
        """Test billing status without authentication"""
        response = client.get("/api/v1/billing/status")
        assert response.status_code == 401

class TestSystemHealthBlackBox:
    """Black-box tests for system health from external perspective"""
    
    def test_health_endpoint(self):
        """Test basic health endpoint"""
        response = client.get("/health")
        
        # Verify response
        assert response.status_code == 200
        data = response.json()
        
        # Verify response contains expected fields
        assert "status" in data
        assert "timestamp" in data
        assert "version" in data
        
        # Verify status is healthy
        assert data["status"] == "healthy"
        
        # Verify version is not empty
        assert len(data["version"]) > 0
    
    def test_readiness_endpoint(self):
        """Test readiness endpoint"""
        response = client.get("/ready")
        
        # Verify response
        assert response.status_code == 200
        data = response.json()
        
        # Verify response contains expected fields
        assert "status" in data
        assert "components" in data
        
        # Verify components are present
        components = data["components"]
        assert isinstance(components, dict)
        assert len(components) > 0
    
    def test_metrics_endpoint(self):
        """Test metrics endpoint"""
        response = client.get("/metrics")
        
        # Verify response
        assert response.status_code == 200
        assert "text/plain" in response.headers.get("content-type", "")
        
        # Verify metrics content
        metrics_content = response.text
        assert len(metrics_content) > 0
        
        # Verify metrics contain expected data
        assert "http_requests_total" in metrics_content
    
    def test_status_endpoint(self):
        """Test detailed status endpoint"""
        response = client.get("/status")
        
        # Verify response
        assert response.status_code == 200
        data = response.json()
        
        # Verify response contains expected fields
        assert "service" in data
        assert "version" in data
        assert "health" in data
        assert "readiness" in data

class TestErrorHandlingBlackBox:
    """Black-box tests for error handling from user perspective"""
    
    def test_invalid_endpoint(self):
        """Test accessing non-existent endpoint"""
        response = client.get("/api/v1/nonexistent")
        assert response.status_code == 404
        
        data = response.json()
        assert "detail" in data
    
    def test_invalid_http_method(self):
        """Test using wrong HTTP method"""
        response = client.delete("/api/v1/auth/login")
        assert response.status_code == 405
        
        data = response.json()
        assert "detail" in data
    
    def test_malformed_json(self):
        """Test sending malformed JSON"""
        response = client.post(
            "/api/v1/auth/login",
            data="invalid json",
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 422
    
    def test_missing_content_type(self):
        """Test sending data without proper content type"""
        response = client.post("/api/v1/auth/login", data="some data")
        assert response.status_code == 422

class TestRateLimitingBlackBox:
    """Black-box tests for rate limiting from user perspective"""
    
    def test_rate_limiting_behavior(self):
        """Test rate limiting behavior"""
        # Make multiple requests to trigger rate limiting
        for i in range(100):
            response = client.get("/health")
            
            # If rate limiting is triggered, should return 429
            if response.status_code == 429:
                data = response.json()
                assert "rate limit" in data.get("detail", "").lower()
                break
            else:
                # Should return 200 for health endpoint
                assert response.status_code == 200

class TestSecurityBlackBox:
    """Black-box tests for security from external perspective"""
    
    def test_cors_headers(self):
        """Test CORS headers are present"""
        response = client.options("/", headers={"Origin": "http://localhost:3000"})
        
        # Verify CORS headers
        assert "access-control-allow-origin" in response.headers
        assert "access-control-allow-methods" in response.headers
        assert "access-control-allow-headers" in response.headers
    
    def test_security_headers(self):
        """Test security headers are present"""
        response = client.get("/health")
        
        # Verify security headers
        security_headers = [
            "X-Content-Type-Options",
            "X-Frame-Options",
            "X-XSS-Protection"
        ]
        
        for header in security_headers:
            assert header in response.headers
    
    def test_sql_injection_attempts(self):
        """Test SQL injection attempts are handled safely"""
        malicious_inputs = [
            "'; DROP TABLE users; --",
            "1' OR '1'='1",
            "admin'--",
            "'; INSERT INTO users VALUES ('hacker', 'password'); --"
        ]
        
        for malicious_input in malicious_inputs:
            response = client.post("/api/v1/auth/login", json={
                "email": malicious_input,
                "password": "test"
            })
            
            # Should not crash the system
            assert response.status_code in [400, 422, 401]
            
            # Should not return sensitive information
            if response.status_code == 200:
                data = response.json()
                assert "password" not in str(data).lower()
    
    def test_xss_attempts(self):
        """Test XSS attempts are handled safely"""
        xss_payloads = [
            "<script>alert('xss')</script>",
            "javascript:alert('xss')",
            "<img src=x onerror=alert('xss')>",
            "';alert('xss');//"
        ]
        
        for payload in xss_payloads:
            response = client.post("/api/v1/auth/register", json={
                "email": payload,
                "password": "TestPassword123!",
                "full_name": payload,
                "workspace_name": "Test Company"
            })
            
            # Should not crash the system
            assert response.status_code in [400, 422, 201]
            
            # If successful, verify payload is not reflected in response
            if response.status_code == 201:
                data = response.json()
                assert payload not in str(data)

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
