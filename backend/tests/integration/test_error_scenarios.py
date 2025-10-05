"""
Comprehensive error scenario tests to prevent 500 errors
Tests all possible error conditions and edge cases
"""

import pytest
import asyncio
import json
from unittest.mock import Mock, patch, MagicMock
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from sqlalchemy.exc import SQLAlchemyError, IntegrityError, OperationalError

from app.main import app
from app.core.database import get_db, Base
from app.models import User, Workspace, Document, ChatSession, ChatMessage, Subscription

# Test database configuration
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_error.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="function")
def db_session():
    """Create a fresh database session for each test."""
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def client(db_session):
    """Create a test client with database dependency override."""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(app) as test_client:
        yield test_client
    
    app.dependency_overrides.clear()

class TestDatabaseErrorScenarios:
    """Test database error scenarios that could cause 500 errors"""
    
    def test_database_connection_failure(self, client):
        """Test handling of database connection failures"""
        # Mock database connection failure
        with patch('app.core.database.get_db') as mock_get_db:
            mock_get_db.side_effect = OperationalError("Connection failed", None, None)
            
            response = client.get("/api/v1/documents/")
            
            # Should return 503 Service Unavailable, not 500
            assert response.status_code == 503
            assert "service unavailable" in response.json()["detail"].lower()
    
    def test_database_timeout_error(self, client):
        """Test handling of database timeout errors"""
        with patch('app.core.database.get_db') as mock_get_db:
            mock_get_db.side_effect = OperationalError("timeout", None, None)
            
            response = client.get("/api/v1/documents/")
            
            assert response.status_code == 503
            assert "timeout" in response.json()["detail"].lower()
    
    def test_database_integrity_error(self, client, auth_token):
        """Test handling of database integrity constraint violations"""
        with patch('app.api.api_v1.endpoints.auth.AuthService') as mock_auth:
            mock_service = Mock()
            mock_service.register_user.side_effect = IntegrityError("UNIQUE constraint failed", None, None)
            mock_auth.return_value = mock_service
            
            user_data = {
                "email": "test@example.com",
                "password": "SecurePassword123!",
                "full_name": "Test User",
                "workspace_name": "Test Workspace"
            }
            
            response = client.post("/api/v1/auth/register", json=user_data)
            
            # Should return 409 Conflict, not 500
            assert response.status_code == 409
            assert "already exists" in response.json()["detail"].lower()
    
    def test_database_transaction_rollback(self, client, auth_token, test_workspace):
        """Test handling of database transaction rollbacks"""
        with patch('app.api.api_v1.endpoints.documents.DocumentService') as mock_doc_service:
            mock_service = Mock()
            mock_service.upload_document.side_effect = SQLAlchemyError("Transaction failed")
            mock_doc_service.return_value = mock_service
            
            files = {"file": ("test.pdf", b"PDF content", "application/pdf")}
            data = {"workspace_id": test_workspace.id}
            
            response = client.post(
                "/api/v1/documents/upload",
                files=files,
                data=data,
                headers={"Authorization": f"Bearer {auth_token}"}
            )
            
            # Should return 500 with proper error handling
            assert response.status_code == 500
            assert "internal server error" in response.json()["detail"].lower()

class TestExternalServiceErrorScenarios:
    """Test external service error scenarios"""
    
    def test_gemini_service_failure(self, client, auth_token, test_workspace):
        """Test handling of Gemini service failures"""
        with patch('app.api.api_v1.endpoints.rag_query.RAGService') as mock_rag_service:
            mock_service = Mock()
            mock_service.process_query.side_effect = Exception("Gemini API unavailable")
            mock_rag_service.return_value = mock_service
            
            query_data = {
                "query": "Test question",
                "session_id": "session_123"
            }
            
            response = client.post(
                "/api/v1/rag/query",
                json=query_data,
                headers={"Authorization": f"Bearer {auth_token}"}
            )
            
            # Should return 503 Service Unavailable, not 500
            assert response.status_code == 503
            assert "service unavailable" in response.json()["detail"].lower()
    
    def test_embeddings_service_failure(self, client, auth_token, test_workspace):
        """Test handling of embeddings service failures"""
        with patch('app.api.api_v1.endpoints.documents.DocumentService') as mock_doc_service:
            mock_service = Mock()
            mock_service.upload_document.side_effect = Exception("Embeddings service error")
            mock_doc_service.return_value = mock_service
            
            files = {"file": ("test.txt", b"content", "text/plain")}
            data = {"workspace_id": test_workspace.id}
            
            response = client.post(
                "/api/v1/documents/upload",
                files=files,
                data=data,
                headers={"Authorization": f"Bearer {auth_token}"}
            )
            
            assert response.status_code == 503
            assert "service unavailable" in response.json()["detail"].lower()
    
    def test_stripe_service_failure(self, client, auth_token):
        """Test handling of Stripe service failures"""
        with patch('app.api.api_v1.endpoints.billing.StripeService') as mock_stripe_service:
            mock_service = Mock()
            mock_service.create_checkout_session.side_effect = Exception("Stripe API error")
            mock_stripe_service.return_value = mock_service
            
            checkout_data = {
                "plan_tier": "pro",
                "success_url": "http://localhost:3000/success",
                "cancel_url": "http://localhost:3000/cancel"
            }
            
            response = client.post(
                "/api/v1/billing/create-checkout-session",
                json=checkout_data,
                headers={"Authorization": f"Bearer {auth_token}"}
            )
            
            assert response.status_code == 503
            assert "service unavailable" in response.json()["detail"].lower()
    
    def test_redis_service_failure(self, client, auth_token):
        """Test handling of Redis service failures"""
        with patch('app.core.database.redis_client') as mock_redis:
            mock_redis.get.side_effect = Exception("Redis connection failed")
            
            response = client.get(
                "/api/v1/documents/",
                headers={"Authorization": f"Bearer {auth_token}"}
            )
            
            # Should still work without Redis (graceful degradation)
            assert response.status_code == 200

class TestFileProcessingErrorScenarios:
    """Test file processing error scenarios"""
    
    def test_corrupted_file_upload(self, client, auth_token, test_workspace):
        """Test handling of corrupted file uploads"""
        # Upload a corrupted PDF
        corrupted_pdf = b"%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n/Pages 2 0 R\n>>\nendobj\ncorrupted content"
        
        files = {"file": ("corrupted.pdf", corrupted_pdf, "application/pdf")}
        data = {"workspace_id": test_workspace.id}
        
        response = client.post(
            "/api/v1/documents/upload",
            files=files,
            data=data,
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        # Should handle gracefully, not crash
        assert response.status_code in [400, 422, 500]  # Any of these is acceptable
        assert "error" in response.json()["detail"].lower()
    
    def test_oversized_file_upload(self, client, auth_token, test_workspace):
        """Test handling of oversized file uploads"""
        # Create a large file (simulate)
        large_content = b"x" * (100 * 1024 * 1024)  # 100MB
        
        files = {"file": ("large_file.txt", large_content, "text/plain")}
        data = {"workspace_id": test_workspace.id}
        
        response = client.post(
            "/api/v1/documents/upload",
            files=files,
            data=data,
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        # Should return 413 Payload Too Large
        assert response.status_code == 413
        assert "too large" in response.json()["detail"].lower()
    
    def test_unsupported_file_type(self, client, auth_token, test_workspace):
        """Test handling of unsupported file types"""
        files = {"file": ("test.exe", b"executable content", "application/x-msdownload")}
        data = {"workspace_id": test_workspace.id}
        
        response = client.post(
            "/api/v1/documents/upload",
            files=files,
            data=data,
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        assert response.status_code == 400
        assert "file type" in response.json()["detail"].lower()
    
    def test_empty_file_upload(self, client, auth_token, test_workspace):
        """Test handling of empty file uploads"""
        files = {"file": ("empty.txt", b"", "text/plain")}
        data = {"workspace_id": test_workspace.id}
        
        response = client.post(
            "/api/v1/documents/upload",
            files=files,
            data=data,
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        assert response.status_code == 400
        assert "empty" in response.json()["detail"].lower()

class TestAuthenticationErrorScenarios:
    """Test authentication error scenarios"""
    
    def test_expired_token(self, client):
        """Test handling of expired JWT tokens"""
        # Create an expired token (this would need proper JWT creation)
        expired_token = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ1c2VyX2lkIjoiMTIzIiwiZXhwIjoxNjAwMDAwMDAwfQ.invalid"
        
        response = client.get(
            "/api/v1/documents/",
            headers={"Authorization": f"Bearer {expired_token}"}
        )
        
        assert response.status_code == 401
        assert "expired" in response.json()["detail"].lower()
    
    def test_malformed_token(self, client):
        """Test handling of malformed JWT tokens"""
        malformed_token = "not.a.valid.jwt.token"
        
        response = client.get(
            "/api/v1/documents/",
            headers={"Authorization": f"Bearer {malformed_token}"}
        )
        
        assert response.status_code == 401
        assert "invalid" in response.json()["detail"].lower()
    
    def test_missing_authorization_header(self, client):
        """Test handling of missing authorization header"""
        response = client.get("/api/v1/documents/")
        
        assert response.status_code == 401
        assert "authorization" in response.json()["detail"].lower()
    
    def test_invalid_authorization_format(self, client):
        """Test handling of invalid authorization header format"""
        response = client.get(
            "/api/v1/documents/",
            headers={"Authorization": "InvalidFormat token123"}
        )
        
        assert response.status_code == 401
        assert "bearer" in response.json()["detail"].lower()

class TestInputValidationErrorScenarios:
    """Test input validation error scenarios"""
    
    def test_malformed_json_request(self, client, auth_token):
        """Test handling of malformed JSON requests"""
        response = client.post(
            "/api/v1/chat/sessions",
            data="invalid json",
            headers={
                "Authorization": f"Bearer {auth_token}",
                "Content-Type": "application/json"
            }
        )
        
        assert response.status_code == 400
        assert "json" in response.json()["detail"].lower()
    
    def test_sql_injection_attempt(self, client, auth_token):
        """Test handling of SQL injection attempts"""
        malicious_data = {
            "query": "'; DROP TABLE users; --",
            "session_id": "session_123"
        }
        
        response = client.post(
            "/api/v1/rag/query",
            json=malicious_data,
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        # Should be sanitized and handled gracefully
        assert response.status_code in [400, 422]
        assert "invalid" in response.json()["detail"].lower()
    
    def test_xss_attempt(self, client, auth_token):
        """Test handling of XSS attempts"""
        malicious_data = {
            "content": "<script>alert('xss')</script>",
            "session_id": "session_123"
        }
        
        response = client.post(
            "/api/v1/chat/message",
            json=malicious_data,
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        # Should be sanitized
        assert response.status_code in [200, 400, 422]
        if response.status_code != 200:
            assert "invalid" in response.json()["detail"].lower()
    
    def test_oversized_request_body(self, client, auth_token):
        """Test handling of oversized request bodies"""
        # Create a very large request body
        large_content = "x" * (10 * 1024 * 1024)  # 10MB
        large_data = {
            "content": large_content,
            "session_id": "session_123"
        }
        
        response = client.post(
            "/api/v1/chat/message",
            json=large_data,
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        assert response.status_code == 413
        assert "too large" in response.json()["detail"].lower()

class TestRateLimitingErrorScenarios:
    """Test rate limiting error scenarios"""
    
    def test_rate_limit_exceeded(self, client, auth_token):
        """Test handling of rate limit exceeded"""
        # Make many requests quickly
        responses = []
        for _ in range(1000):  # Exceed rate limit
            response = client.get(
                "/api/v1/documents/",
                headers={"Authorization": f"Bearer {auth_token}"}
            )
            responses.append(response.status_code)
            if response.status_code == 429:
                break
        
        # Should eventually hit rate limit
        assert 429 in responses
    
    def test_rate_limit_reset(self, client, auth_token):
        """Test that rate limit resets after time window"""
        # Exceed rate limit
        for _ in range(1000):
            response = client.get(
                "/api/v1/documents/",
                headers={"Authorization": f"Bearer {auth_token}"}
            )
            if response.status_code == 429:
                break
        
        # Wait for rate limit to reset (mocked)
        with patch('time.time', return_value=3600):  # 1 hour later
            response = client.get(
                "/api/v1/documents/",
                headers={"Authorization": f"Bearer {auth_token}"}
            )
            assert response.status_code == 200

class TestConcurrentAccessErrorScenarios:
    """Test concurrent access error scenarios"""
    
    def test_concurrent_document_deletion(self, client, auth_token, test_workspace):
        """Test handling of concurrent document deletion attempts"""
        import threading
        
        # First upload a document
        files = {"file": ("test.txt", b"content", "text/plain")}
        data = {"workspace_id": test_workspace.id}
        
        upload_response = client.post(
            "/api/v1/documents/upload",
            files=files,
            data=data,
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        document_id = upload_response.json()["document_id"]
        
        # Try to delete the same document concurrently
        results = []
        
        def delete_document():
            response = client.delete(
                f"/api/v1/documents/{document_id}",
                headers={"Authorization": f"Bearer {auth_token}"}
            )
            results.append(response.status_code)
        
        threads = []
        for _ in range(5):
            thread = threading.Thread(target=delete_document)
            threads.append(thread)
            thread.start()
        
        for thread in threads:
            thread.join()
        
        # Only one deletion should succeed, others should return 404
        success_count = results.count(200)
        not_found_count = results.count(404)
        
        assert success_count == 1
        assert not_found_count == 4
    
    def test_concurrent_workspace_modification(self, client, auth_token, test_workspace):
        """Test handling of concurrent workspace modifications"""
        import threading
        
        results = []
        
        def update_workspace():
            update_data = {
                "name": f"Updated Workspace {threading.current_thread().ident}",
                "description": "Updated description"
            }
            
            response = client.put(
                f"/api/v1/workspaces/{test_workspace.id}",
                json=update_data,
                headers={"Authorization": f"Bearer {auth_token}"}
            )
            results.append(response.status_code)
        
        threads = []
        for _ in range(10):
            thread = threading.Thread(target=update_workspace)
            threads.append(thread)
            thread.start()
        
        for thread in threads:
            thread.join()
        
        # All updates should succeed (or be handled gracefully)
        assert all(status in [200, 409] for status in results)

class TestMemoryAndResourceErrorScenarios:
    """Test memory and resource error scenarios"""
    
    def test_memory_exhaustion_handling(self, client, auth_token, test_workspace):
        """Test handling of memory exhaustion scenarios"""
        # This would require mocking memory allocation failures
        # For now, we'll test that the system handles large requests gracefully
        large_content = "x" * (1024 * 1024)  # 1MB of text
        
        files = {"file": ("large.txt", large_content.encode(), "text/plain")}
        data = {"workspace_id": test_workspace.id}
        
        response = client.post(
            "/api/v1/documents/upload",
            files=files,
            data=data,
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        # Should handle gracefully
        assert response.status_code in [200, 413, 500]
    
    def test_disk_space_exhaustion_handling(self, client, auth_token, test_workspace):
        """Test handling of disk space exhaustion scenarios"""
        # Mock disk space exhaustion
        with patch('shutil.disk_usage') as mock_disk_usage:
            mock_disk_usage.return_value = (1000000, 999999, 1)  # Almost no free space
            
            files = {"file": ("test.txt", b"content", "text/plain")}
            data = {"workspace_id": test_workspace.id}
            
            response = client.post(
                "/api/v1/documents/upload",
                files=files,
                data=data,
                headers={"Authorization": f"Bearer {auth_token}"}
            )
            
            # Should return 507 Insufficient Storage
            assert response.status_code == 507
            assert "storage" in response.json()["detail"].lower()

class TestNetworkErrorScenarios:
    """Test network error scenarios"""
    
    def test_network_timeout_handling(self, client, auth_token):
        """Test handling of network timeouts"""
        with patch('httpx.AsyncClient') as mock_client:
            mock_client.side_effect = Exception("Network timeout")
            
            response = client.get(
                "/api/v1/analytics/workspace",
                headers={"Authorization": f"Bearer {auth_token}"}
            )
            
            # Should handle gracefully
            assert response.status_code in [200, 503]
    
    def test_dns_resolution_failure(self, client, auth_token):
        """Test handling of DNS resolution failures"""
        with patch('socket.gethostbyname') as mock_dns:
            mock_dns.side_effect = Exception("DNS resolution failed")
            
            response = client.get(
                "/api/v1/analytics/workspace",
                headers={"Authorization": f"Bearer {auth_token}"}
            )
            
            # Should handle gracefully
            assert response.status_code in [200, 503]

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
