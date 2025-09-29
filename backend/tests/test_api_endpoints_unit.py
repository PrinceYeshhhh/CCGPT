"""
Comprehensive unit tests for all API endpoints
Tests each endpoint in isolation with proper mocking
"""

import pytest
import json
from unittest.mock import Mock, patch, MagicMock
from fastapi.testclient import TestClient
from fastapi import status

from app.main import app
from app.models.user import User
from app.models.workspace import Workspace
from app.models.document import Document
from app.models.chat import ChatSession, ChatMessage
from app.models.subscriptions import Subscription

client = TestClient(app)

class TestAuthEndpoints:
    """Unit tests for authentication endpoints"""
    
    def test_register_user_success(self):
        """Test successful user registration"""
        user_data = {
            "email": "test@example.com",
            "password": "TestPassword123!",
            "full_name": "Test User",
            "workspace_name": "Test Workspace"
        }
        
        with patch('app.api.api_v1.endpoints.auth.AuthService') as mock_auth:
            mock_service = Mock()
            mock_service.register_user.return_value = {
                "user_id": "123",
                "workspace_id": "ws_123",
                "email": "test@example.com"
            }
            mock_auth.return_value = mock_service
            
            response = client.post("/api/v1/auth/register", json=user_data)
            
            assert response.status_code == status.HTTP_201_CREATED
            data = response.json()
            assert "user_id" in data
            assert "workspace_id" in data
            assert data["email"] == "test@example.com"
    
    def test_register_user_invalid_email(self):
        """Test user registration with invalid email"""
        user_data = {
            "email": "invalid-email",
            "password": "TestPassword123!",
            "full_name": "Test User",
            "workspace_name": "Test Workspace"
        }
        
        response = client.post("/api/v1/auth/register", json=user_data)
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    def test_register_user_weak_password(self):
        """Test user registration with weak password"""
        user_data = {
            "email": "test@example.com",
            "password": "123",
            "full_name": "Test User",
            "workspace_name": "Test Workspace"
        }
        
        response = client.post("/api/v1/auth/register", json=user_data)
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    def test_login_success(self):
        """Test successful user login"""
        login_data = {
            "email": "test@example.com",
            "password": "TestPassword123!"
        }
        
        with patch('app.api.api_v1.endpoints.auth.AuthService') as mock_auth:
            mock_service = Mock()
            mock_service.authenticate_user.return_value = {
                "access_token": "test_token",
                "token_type": "bearer",
                "user": {
                    "id": "123",
                    "email": "test@example.com",
                    "full_name": "Test User"
                }
            }
            mock_auth.return_value = mock_service
            
            response = client.post("/api/v1/auth/login", json=login_data)
            
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert "access_token" in data
            assert data["token_type"] == "bearer"
    
    def test_login_invalid_credentials(self):
        """Test login with invalid credentials"""
        login_data = {
            "email": "test@example.com",
            "password": "wrong_password"
        }
        
        with patch('app.api.api_v1.endpoints.auth.AuthService') as mock_auth:
            mock_service = Mock()
            mock_service.authenticate_user.return_value = None
            mock_auth.return_value = mock_service
            
            response = client.post("/api/v1/auth/login", json=login_data)
            
            assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_get_current_user_success(self):
        """Test getting current user with valid token"""
        with patch('app.api.api_v1.endpoints.auth.get_current_user') as mock_get_user:
            mock_user = Mock()
            mock_user.id = "123"
            mock_user.email = "test@example.com"
            mock_user.full_name = "Test User"
            mock_get_user.return_value = mock_user
            
            headers = {"Authorization": "Bearer test_token"}
            response = client.get("/api/v1/auth/me", headers=headers)
            
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["id"] == "123"
            assert data["email"] == "test@example.com"
    
    def test_get_current_user_invalid_token(self):
        """Test getting current user with invalid token"""
        headers = {"Authorization": "Bearer invalid_token"}
        response = client.get("/api/v1/auth/me", headers=headers)
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

class TestDocumentEndpoints:
    """Unit tests for document endpoints"""
    
    def test_upload_document_success(self):
        """Test successful document upload"""
        with patch('app.api.api_v1.endpoints.documents.get_current_user') as mock_get_user:
            mock_user = Mock()
            mock_user.id = "123"
            mock_user.workspace_id = "ws_123"
            mock_get_user.return_value = mock_user
            
            with patch('app.api.api_v1.endpoints.documents.DocumentService') as mock_doc_service:
                mock_service = Mock()
                mock_service.upload_document.return_value = {
                    "document_id": "doc_123",
                    "job_id": "job_123",
                    "status": "processing"
                }
                mock_doc_service.return_value = mock_service
                
                files = {"file": ("test.pdf", b"PDF content", "application/pdf")}
                headers = {"Authorization": "Bearer test_token"}
                response = client.post("/api/v1/documents/upload", files=files, headers=headers)
                
                assert response.status_code == status.HTTP_200_OK
                data = response.json()
                assert "document_id" in data
                assert "job_id" in data
    
    def test_upload_document_invalid_file_type(self):
        """Test document upload with invalid file type"""
        with patch('app.api.api_v1.endpoints.documents.get_current_user') as mock_get_user:
            mock_user = Mock()
            mock_user.id = "123"
            mock_user.workspace_id = "ws_123"
            mock_get_user.return_value = mock_user
            
            files = {"file": ("test.jpg", b"Image content", "image/jpeg")}
            headers = {"Authorization": "Bearer test_token"}
            response = client.post("/api/v1/documents/upload", files=files, headers=headers)
            
            assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    def test_get_documents_success(self):
        """Test getting user documents"""
        with patch('app.api.api_v1.endpoints.documents.get_current_user') as mock_get_user:
            mock_user = Mock()
            mock_user.id = "123"
            mock_user.workspace_id = "ws_123"
            mock_get_user.return_value = mock_user
            
            with patch('app.api.api_v1.endpoints.documents.DocumentService') as mock_doc_service:
                mock_service = Mock()
                mock_service.get_user_documents.return_value = [
                    {
                        "id": "doc_123",
                        "filename": "test.pdf",
                        "status": "processed",
                        "created_at": "2024-01-01T00:00:00Z"
                    }
                ]
                mock_doc_service.return_value = mock_service
                
                headers = {"Authorization": "Bearer test_token"}
                response = client.get("/api/v1/documents/", headers=headers)
                
                assert response.status_code == status.HTTP_200_OK
                data = response.json()
                assert isinstance(data, list)
                assert len(data) == 1
                assert data[0]["filename"] == "test.pdf"
    
    def test_delete_document_success(self):
        """Test successful document deletion"""
        with patch('app.api.api_v1.endpoints.documents.get_current_user') as mock_get_user:
            mock_user = Mock()
            mock_user.id = "123"
            mock_user.workspace_id = "ws_123"
            mock_get_user.return_value = mock_user
            
            with patch('app.api.api_v1.endpoints.documents.DocumentService') as mock_doc_service:
                mock_service = Mock()
                mock_service.delete_document.return_value = True
                mock_doc_service.return_value = mock_service
                
                headers = {"Authorization": "Bearer test_token"}
                response = client.delete("/api/v1/documents/doc_123", headers=headers)
                
                assert response.status_code == status.HTTP_200_OK
                data = response.json()
                assert data["message"] == "Document deleted successfully"

class TestChatEndpoints:
    """Unit tests for chat endpoints"""
    
    def test_create_chat_session_success(self):
        """Test successful chat session creation"""
        with patch('app.api.api_v1.endpoints.chat.get_current_user') as mock_get_user:
            mock_user = Mock()
            mock_user.id = "123"
            mock_user.workspace_id = "ws_123"
            mock_get_user.return_value = mock_user
            
            with patch('app.api.api_v1.endpoints.chat.ChatService') as mock_chat_service:
                mock_service = Mock()
                mock_service.create_session.return_value = {
                    "session_id": "session_123",
                    "user_label": "Test Customer"
                }
                mock_chat_service.return_value = mock_service
                
                session_data = {"user_label": "Test Customer"}
                headers = {"Authorization": "Bearer test_token"}
                response = client.post("/api/v1/chat/sessions", json=session_data, headers=headers)
                
                assert response.status_code == status.HTTP_201_CREATED
                data = response.json()
                assert "session_id" in data
                assert data["user_label"] == "Test Customer"
    
    def test_get_chat_sessions_success(self):
        """Test getting user chat sessions"""
        with patch('app.api.api_v1.endpoints.chat.get_current_user') as mock_get_user:
            mock_user = Mock()
            mock_user.id = "123"
            mock_user.workspace_id = "ws_123"
            mock_get_user.return_value = mock_user
            
            with patch('app.api.api_v1.endpoints.chat.ChatService') as mock_chat_service:
                mock_service = Mock()
                mock_service.get_user_sessions.return_value = [
                    {
                        "session_id": "session_123",
                        "user_label": "Test Customer",
                        "created_at": "2024-01-01T00:00:00Z"
                    }
                ]
                mock_chat_service.return_value = mock_service
                
                headers = {"Authorization": "Bearer test_token"}
                response = client.get("/api/v1/chat/sessions", headers=headers)
                
                assert response.status_code == status.HTTP_200_OK
                data = response.json()
                assert isinstance(data, list)
                assert len(data) == 1
                assert data[0]["session_id"] == "session_123"
    
    def test_get_chat_messages_success(self):
        """Test getting chat messages"""
        with patch('app.api.api_v1.endpoints.chat.get_current_user') as mock_get_user:
            mock_user = Mock()
            mock_user.id = "123"
            mock_user.workspace_id = "ws_123"
            mock_get_user.return_value = mock_user
            
            with patch('app.api.api_v1.endpoints.chat.ChatService') as mock_chat_service:
                mock_service = Mock()
                mock_service.get_session_messages.return_value = [
                    {
                        "id": "msg_123",
                        "role": "user",
                        "content": "Hello",
                        "created_at": "2024-01-01T00:00:00Z"
                    },
                    {
                        "id": "msg_124",
                        "role": "assistant",
                        "content": "Hi there!",
                        "created_at": "2024-01-01T00:01:00Z"
                    }
                ]
                mock_chat_service.return_value = mock_service
                
                headers = {"Authorization": "Bearer test_token"}
                response = client.get("/api/v1/chat/sessions/session_123/messages", headers=headers)
                
                assert response.status_code == status.HTTP_200_OK
                data = response.json()
                assert isinstance(data, list)
                assert len(data) == 2
                assert data[0]["role"] == "user"
                assert data[1]["role"] == "assistant"

class TestRAGEndpoints:
    """Unit tests for RAG query endpoints"""
    
    def test_rag_query_success(self):
        """Test successful RAG query"""
        with patch('app.api.api_v1.endpoints.rag_query.get_current_user') as mock_get_user:
            mock_user = Mock()
            mock_user.id = "123"
            mock_user.workspace_id = "ws_123"
            mock_get_user.return_value = mock_user
            
            with patch('app.api.api_v1.endpoints.rag_query.RAGService') as mock_rag_service:
                mock_service = Mock()
                mock_service.process_query.return_value = {
                    "answer": "This is a test answer",
                    "sources": [{"chunk_id": "123", "document_id": "doc1"}],
                    "response_time_ms": 150,
                    "tokens_used": 100
                }
                mock_rag_service.return_value = mock_service
                
                query_data = {
                    "query": "Test question",
                    "session_id": "session_123"
                }
                headers = {"Authorization": "Bearer test_token"}
                response = client.post("/api/v1/rag/query", json=query_data, headers=headers)
                
                assert response.status_code == status.HTTP_200_OK
                data = response.json()
                assert "answer" in data
                assert "sources" in data
                assert "response_time_ms" in data
    
    def test_rag_query_missing_session(self):
        """Test RAG query without session ID"""
        with patch('app.api.api_v1.endpoints.rag_query.get_current_user') as mock_get_user:
            mock_user = Mock()
            mock_user.id = "123"
            mock_user.workspace_id = "ws_123"
            mock_get_user.return_value = mock_user
            
            query_data = {"query": "Test question"}
            headers = {"Authorization": "Bearer test_token"}
            response = client.post("/api/v1/rag/query", json=query_data, headers=headers)
            
            assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    def test_rag_query_empty_query(self):
        """Test RAG query with empty query"""
        with patch('app.api.api_v1.endpoints.rag_query.get_current_user') as mock_get_user:
            mock_user = Mock()
            mock_user.id = "123"
            mock_user.workspace_id = "ws_123"
            mock_get_user.return_value = mock_user
            
            query_data = {
                "query": "",
                "session_id": "session_123"
            }
            headers = {"Authorization": "Bearer test_token"}
            response = client.post("/api/v1/rag/query", json=query_data, headers=headers)
            
            assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

class TestBillingEndpoints:
    """Unit tests for billing endpoints"""
    
    def test_get_billing_status_success(self):
        """Test getting billing status"""
        with patch('app.api.api_v1.endpoints.billing.get_current_user') as mock_get_user:
            mock_user = Mock()
            mock_user.id = "123"
            mock_user.workspace_id = "ws_123"
            mock_get_user.return_value = mock_user
            
            with patch('app.api.api_v1.endpoints.billing.BillingService') as mock_billing_service:
                mock_service = Mock()
                mock_service.get_billing_status.return_value = {
                    "tier": "pro",
                    "status": "active",
                    "quota_used": 500,
                    "quota_limit": 1000
                }
                mock_billing_service.return_value = mock_service
                
                headers = {"Authorization": "Bearer test_token"}
                response = client.get("/api/v1/billing/status", headers=headers)
                
                assert response.status_code == status.HTTP_200_OK
                data = response.json()
                assert "tier" in data
                assert "status" in data
                assert "quota_used" in data
    
    def test_create_checkout_session_success(self):
        """Test creating checkout session"""
        with patch('app.api.api_v1.endpoints.billing.get_current_user') as mock_get_user:
            mock_user = Mock()
            mock_user.id = "123"
            mock_user.workspace_id = "ws_123"
            mock_get_user.return_value = mock_user
            
            with patch('app.api.api_v1.endpoints.billing.StripeService') as mock_stripe_service:
                mock_service = Mock()
                mock_service.create_checkout_session.return_value = {
                    "session_id": "cs_test_123",
                    "checkout_url": "http://localhost:3000/billing/checkout/test"
                }
                mock_stripe_service.return_value = mock_service
                
                checkout_data = {
                    "plan_tier": "pro",
                    "success_url": "http://localhost:3000/billing/success",
                    "cancel_url": "http://localhost:3000/billing/cancel"
                }
                headers = {"Authorization": "Bearer test_token"}
                response = client.post("/api/v1/billing/create-checkout-session", json=checkout_data, headers=headers)
                
                assert response.status_code == status.HTTP_200_OK
                data = response.json()
                assert "session_id" in data
                assert "checkout_url" in data

class TestEmbedEndpoints:
    """Unit tests for embed widget endpoints"""
    
    def test_generate_embed_code_success(self):
        """Test successful embed code generation"""
        with patch('app.api.api_v1.endpoints.embed.get_current_user') as mock_get_user:
            mock_user = Mock()
            mock_user.id = "123"
            mock_user.workspace_id = "ws_123"
            mock_get_user.return_value = mock_user
            
            with patch('app.api.api_v1.endpoints.embed.EmbedService') as mock_embed_service:
                mock_service = Mock()
                mock_service.generate_embed_code.return_value = {
                    "embed_code_id": "embed_123",
                    "client_api_key": "api_key_123",
                    "snippet": "<script>console.log('test')</script>"
                }
                mock_embed_service.return_value = mock_service
                
                embed_data = {
                    "workspace_id": "ws_123",
                    "config": {
                        "theme": {"primary": "#4f46e5"},
                        "welcomeMessage": "Hello!"
                    }
                }
                headers = {"Authorization": "Bearer test_token"}
                response = client.post("/api/v1/embed/generate", json=embed_data, headers=headers)
                
                assert response.status_code == status.HTTP_201_CREATED
                data = response.json()
                assert "embed_code_id" in data
                assert "client_api_key" in data
                assert "snippet" in data
    
    def test_embed_health_check(self):
        """Test embed widget health check"""
        headers = {"X-API-Key": "test_api_key"}
        response = client.get("/api/v1/embed/health", headers=headers)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "healthy"

class TestAnalyticsEndpoints:
    """Unit tests for analytics endpoints"""
    
    def test_get_workspace_analytics_success(self):
        """Test getting workspace analytics"""
        with patch('app.api.api_v1.endpoints.analytics.get_current_user') as mock_get_user:
            mock_user = Mock()
            mock_user.id = "123"
            mock_user.workspace_id = "ws_123"
            mock_get_user.return_value = mock_user
            
            with patch('app.api.api_v1.endpoints.analytics.AnalyticsService') as mock_analytics_service:
                mock_service = Mock()
                mock_service.get_workspace_analytics.return_value = {
                    "total_queries": 100,
                    "total_documents": 10,
                    "average_response_time": 150,
                    "quota_usage": 0.5
                }
                mock_analytics_service.return_value = mock_service
                
                headers = {"Authorization": "Bearer test_token"}
                response = client.get("/api/v1/analytics/workspace", headers=headers)
                
                assert response.status_code == status.HTTP_200_OK
                data = response.json()
                assert "total_queries" in data
                assert "total_documents" in data
                assert "average_response_time" in data

class TestHealthEndpoints:
    """Unit tests for health check endpoints"""
    
    def test_health_endpoint(self):
        """Test basic health check"""
        response = client.get("/health")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "healthy"
    
    def test_ready_endpoint(self):
        """Test readiness check"""
        with patch('app.api.api_v1.endpoints.health.get_readiness_status') as mock_readiness:
            mock_readiness.return_value = {
                "status": "healthy",
                "components": {
                    "database": {"status": "healthy"},
                    "redis": {"status": "healthy"}
                }
            }
            
            response = client.get("/ready")
            
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["status"] == "healthy"
    
    def test_metrics_endpoint(self):
        """Test metrics endpoint"""
        response = client.get("/metrics")
        
        assert response.status_code == status.HTTP_200_OK
        assert "text/plain" in response.headers.get("content-type", "")

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
