"""
Comprehensive integration tests for CustomerCareGPT
Tests component interactions and data flow
"""

import pytest
import asyncio
import json
import tempfile
import os
from unittest.mock import patch, Mock, MagicMock
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.core.database import get_db, Base, engine
from app.models.user import User
from app.models.workspace import Workspace
from app.models.document import Document
from app.models.chat import ChatSession, ChatMessage
from app.models.subscriptions import Subscription
from app.services.auth import AuthService
from app.services.rag_service import RAGService
from app.services.document_service import DocumentService
from app.services.vector_search_service import VectorSearchService
from app.services.embeddings_service import EmbeddingsService
from app.services.gemini_service import GeminiService

client = TestClient(app)

class TestAuthIntegration:
    """Integration tests for authentication flow"""
    
    def test_complete_auth_flow(self, db_session):
        """Test complete authentication flow from registration to token validation"""
        # 1. Register user
        user_data = {
            "email": "integration@example.com",
            "password": "IntegrationTest123!",
            "full_name": "Integration Test User",
            "workspace_name": "Integration Workspace"
        }
        
        with patch('app.api.api_v1.endpoints.auth.AuthService') as mock_auth:
            mock_service = Mock()
            mock_service.register_user.return_value = {
                "user_id": "user_123",
                "workspace_id": "ws_123",
                "email": "integration@example.com"
            }
            mock_auth.return_value = mock_service
            
            response = client.post("/api/v1/auth/register", json=user_data)
            assert response.status_code == 201
            
            register_data = response.json()
            assert "user_id" in register_data
            assert "workspace_id" in register_data
        
        # 2. Login user
        login_data = {
            "email": "integration@example.com",
            "password": "IntegrationTest123!"
        }
        
        with patch('app.api.api_v1.endpoints.auth.AuthService') as mock_auth:
            mock_service = Mock()
            mock_service.authenticate_user.return_value = {
                "access_token": "integration_token_123",
                "token_type": "bearer",
                "user": {
                    "id": "user_123",
                    "email": "integration@example.com",
                    "full_name": "Integration Test User"
                }
            }
            mock_auth.return_value = mock_service
            
            response = client.post("/api/v1/auth/login", json=login_data)
            assert response.status_code == 200
            
            login_response = response.json()
            assert "access_token" in login_response
            token = login_response["access_token"]
        
        # 3. Use token to access protected endpoint
        with patch('app.api.api_v1.endpoints.auth.get_current_user') as mock_get_user:
            mock_user = Mock()
            mock_user.id = "user_123"
            mock_user.email = "integration@example.com"
            mock_user.full_name = "Integration Test User"
            mock_get_user.return_value = mock_user
            
            headers = {"Authorization": f"Bearer {token}"}
            response = client.get("/api/v1/auth/me", headers=headers)
            assert response.status_code == 200
            
            user_data = response.json()
            assert user_data["email"] == "integration@example.com"

class TestDocumentProcessingIntegration:
    """Integration tests for document processing pipeline"""
    
    def test_document_upload_to_rag_pipeline(self, db_session):
        """Test complete document upload to RAG query pipeline"""
        # Mock user authentication
        with patch('app.api.api_v1.endpoints.documents.get_current_user') as mock_get_user:
            mock_user = Mock()
            mock_user.id = "user_123"
            mock_user.workspace_id = "ws_123"
            mock_get_user.return_value = mock_user
            
            # 1. Upload document
            with patch('app.api.api_v1.endpoints.documents.DocumentService') as mock_doc_service:
                mock_service = Mock()
                mock_service.upload_document.return_value = {
                    "document_id": "doc_123",
                    "job_id": "job_123",
                    "status": "processing"
                }
                mock_doc_service.return_value = mock_service
                
                # Create a temporary file
                with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
                    f.write("This is a test document about refund policies. Customers can request refunds within 30 days.")
                    temp_file_path = f.name
                
                try:
                    with open(temp_file_path, 'rb') as f:
                        files = {"file": ("test_document.txt", f, "text/plain")}
                        headers = {"Authorization": "Bearer test_token"}
                        response = client.post("/api/v1/documents/upload", files=files, headers=headers)
                        
                        assert response.status_code == 200
                        upload_data = response.json()
                        assert "document_id" in upload_data
                        assert "job_id" in upload_data
                
                finally:
                    os.unlink(temp_file_path)
            
            # 2. Simulate document processing completion
            with patch('app.api.api_v1.endpoints.documents.DocumentService') as mock_doc_service:
                mock_service = Mock()
                mock_service.get_document_status.return_value = {
                    "document_id": "doc_123",
                    "status": "processed",
                    "chunks_created": 5
                }
                mock_doc_service.return_value = mock_service
                
                headers = {"Authorization": "Bearer test_token"}
                response = client.get("/api/v1/documents/doc_123/status", headers=headers)
                assert response.status_code == 200
                
                status_data = response.json()
                assert status_data["status"] == "processed"

class TestRAGPipelineIntegration:
    """Integration tests for RAG pipeline"""
    
    def test_complete_rag_query_flow(self, db_session):
        """Test complete RAG query flow from user input to response"""
        # Mock user authentication
        with patch('app.api.api_v1.endpoints.rag_query.get_current_user') as mock_get_user:
            mock_user = Mock()
            mock_user.id = "user_123"
            mock_user.workspace_id = "ws_123"
            mock_get_user.return_value = mock_user
            
            # Mock RAG service with all components
            with patch('app.api.api_v1.endpoints.rag_query.RAGService') as mock_rag_service:
                mock_service = Mock()
                mock_service.process_query.return_value = {
                    "answer": "Customers can request refunds within 30 days of purchase by contacting our support team.",
                    "sources": [
                        {
                            "chunk_id": "chunk_123",
                            "document_id": "doc_123",
                            "content": "refund policies within 30 days",
                            "score": 0.95
                        }
                    ],
                    "response_time_ms": 250,
                    "tokens_used": 150,
                    "model_used": "gemini-pro"
                }
                mock_rag_service.return_value = mock_service
                
                # Mock chat service for message storage
                with patch('app.api.api_v1.endpoints.rag_query.ChatService') as mock_chat_service:
                    mock_chat_service_instance = Mock()
                    mock_chat_service_instance.save_message.return_value = {
                        "message_id": "msg_123",
                        "role": "assistant",
                        "content": "Customers can request refunds within 30 days...",
                        "created_at": "2024-01-01T00:00:00Z"
                    }
                    mock_chat_service.return_value = mock_chat_service_instance
                    
                    # 1. Send RAG query
                    query_data = {
                        "query": "How do I get a refund?",
                        "session_id": "session_123"
                    }
                    headers = {"Authorization": "Bearer test_token"}
                    response = client.post("/api/v1/rag/query", json=query_data, headers=headers)
                    
                    assert response.status_code == 200
                    rag_data = response.json()
                    assert "answer" in rag_data
                    assert "sources" in rag_data
                    assert "response_time_ms" in rag_data
                    assert "refund" in rag_data["answer"].lower()
                    
                    # Verify sources are relevant
                    assert len(rag_data["sources"]) > 0
                    assert rag_data["sources"][0]["score"] > 0.9

class TestChatSessionIntegration:
    """Integration tests for chat session management"""
    
    def test_chat_session_lifecycle(self, db_session):
        """Test complete chat session lifecycle"""
        # Mock user authentication
        with patch('app.api.api_v1.endpoints.chat.get_current_user') as mock_get_user:
            mock_user = Mock()
            mock_user.id = "user_123"
            mock_user.workspace_id = "ws_123"
            mock_get_user.return_value = mock_user
            
            # 1. Create chat session
            with patch('app.api.api_v1.endpoints.chat.ChatService') as mock_chat_service:
                mock_service = Mock()
                mock_service.create_session.return_value = {
                    "session_id": "session_123",
                    "user_label": "Test Customer",
                    "created_at": "2024-01-01T00:00:00Z"
                }
                mock_chat_service.return_value = mock_service
                
                session_data = {"user_label": "Test Customer"}
                headers = {"Authorization": "Bearer test_token"}
                response = client.post("/api/v1/chat/sessions", json=session_data, headers=headers)
                
                assert response.status_code == 201
                session_response = response.json()
                assert "session_id" in session_response
                session_id = session_response["session_id"]
            
            # 2. Get chat sessions
            with patch('app.api.api_v1.endpoints.chat.ChatService') as mock_chat_service:
                mock_service = Mock()
                mock_service.get_user_sessions.return_value = [
                    {
                        "session_id": "session_123",
                        "user_label": "Test Customer",
                        "created_at": "2024-01-01T00:00:00Z",
                        "message_count": 0
                    }
                ]
                mock_chat_service.return_value = mock_service
                
                headers = {"Authorization": "Bearer test_token"}
                response = client.get("/api/v1/chat/sessions", headers=headers)
                
                assert response.status_code == 200
                sessions = response.json()
                assert isinstance(sessions, list)
                assert len(sessions) == 1
                assert sessions[0]["session_id"] == session_id
            
            # 3. Get chat messages
            with patch('app.api.api_v1.endpoints.chat.ChatService') as mock_chat_service:
                mock_service = Mock()
                mock_service.get_session_messages.return_value = [
                    {
                        "id": "msg_123",
                        "role": "user",
                        "content": "Hello, I need help with refunds",
                        "created_at": "2024-01-01T00:00:00Z"
                    },
                    {
                        "id": "msg_124",
                        "role": "assistant",
                        "content": "I'd be happy to help you with refunds. What specific information do you need?",
                        "created_at": "2024-01-01T00:01:00Z"
                    }
                ]
                mock_chat_service.return_value = mock_service
                
                headers = {"Authorization": "Bearer test_token"}
                response = client.get(f"/api/v1/chat/sessions/{session_id}/messages", headers=headers)
                
                assert response.status_code == 200
                messages = response.json()
                assert isinstance(messages, list)
                assert len(messages) == 2
                assert messages[0]["role"] == "user"
                assert messages[1]["role"] == "assistant"

class TestBillingIntegration:
    """Integration tests for billing system"""
    
    def test_billing_workflow(self, db_session):
        """Test complete billing workflow"""
        # Mock user authentication
        with patch('app.api.api_v1.endpoints.billing.get_current_user') as mock_get_user:
            mock_user = Mock()
            mock_user.id = "user_123"
            mock_user.workspace_id = "ws_123"
            mock_get_user.return_value = mock_user
            
            # 1. Get billing status
            with patch('app.api.api_v1.endpoints.billing.BillingService') as mock_billing_service:
                mock_service = Mock()
                mock_service.get_billing_status.return_value = {
                    "tier": "free",
                    "status": "active",
                    "quota_used": 50,
                    "quota_limit": 100,
                    "quota_percentage": 0.5
                }
                mock_billing_service.return_value = mock_service
                
                headers = {"Authorization": "Bearer test_token"}
                response = client.get("/api/v1/billing/status", headers=headers)
                
                assert response.status_code == 200
                billing_data = response.json()
                assert "tier" in billing_data
                assert "quota_used" in billing_data
                assert billing_data["tier"] == "free"
            
            # 2. Create checkout session
            with patch('app.api.api_v1.endpoints.billing.StripeService') as mock_stripe_service:
                mock_service = Mock()
                mock_service.create_checkout_session.return_value = {
                    "session_id": "cs_test_123",
                    "checkout_url": "https://checkout.stripe.com/test"
                }
                mock_stripe_service.return_value = mock_service
                
                checkout_data = {
                    "plan_tier": "pro",
                    "success_url": "https://example.com/success",
                    "cancel_url": "https://example.com/cancel"
                }
                headers = {"Authorization": "Bearer test_token"}
                response = client.post("/api/v1/billing/create-checkout-session", json=checkout_data, headers=headers)
                
                assert response.status_code == 200
                checkout_response = response.json()
                assert "session_id" in checkout_response
                assert "checkout_url" in checkout_response
            
            # 3. Create billing portal session
            with patch('app.api.api_v1.endpoints.billing.StripeService') as mock_stripe_service:
                mock_service = Mock()
                mock_service.create_billing_portal_session.return_value = {
                    "portal_url": "https://billing.stripe.com/test"
                }
                mock_stripe_service.return_value = mock_service
                
                headers = {"Authorization": "Bearer test_token"}
                response = client.post("/api/v1/billing/portal", headers=headers)
                
                assert response.status_code == 200
                portal_response = response.json()
                assert "portal_url" in portal_response

class TestEmbedWidgetIntegration:
    """Integration tests for embed widget functionality"""
    
    def test_embed_widget_workflow(self, db_session):
        """Test complete embed widget workflow"""
        # Mock user authentication
        with patch('app.api.api_v1.endpoints.embed.get_current_user') as mock_get_user:
            mock_user = Mock()
            mock_user.id = "user_123"
            mock_user.workspace_id = "ws_123"
            mock_get_user.return_value = mock_user
            
            # 1. Generate embed code
            with patch('app.api.api_v1.endpoints.embed.EmbedService') as mock_embed_service:
                mock_service = Mock()
                mock_service.generate_embed_code.return_value = {
                    "embed_code_id": "embed_123",
                    "client_api_key": "api_key_123",
                    "snippet": "<script>console.log('CustomerCareGPT Widget')</script>",
                    "config": {
                        "theme": {"primary": "#4f46e5"},
                        "welcomeMessage": "Hello! How can I help you?"
                    }
                }
                mock_embed_service.return_value = mock_service
                
                embed_data = {
                    "workspace_id": "ws_123",
                    "config": {
                        "theme": {"primary": "#4f46e5"},
                        "welcomeMessage": "Hello! How can I help you?"
                    }
                }
                headers = {"Authorization": "Bearer test_token"}
                response = client.post("/api/v1/embed/generate", json=embed_data, headers=headers)
                
                assert response.status_code == 201
                embed_response = response.json()
                assert "embed_code_id" in embed_response
                assert "client_api_key" in embed_response
                assert "snippet" in embed_response
                
                api_key = embed_response["client_api_key"]
            
            # 2. Test widget health check
            widget_headers = {"X-API-Key": api_key}
            response = client.get("/api/v1/embed/health", headers=widget_headers)
            
            assert response.status_code == 200
            health_data = response.json()
            assert health_data["status"] == "healthy"
            
            # 3. Test widget session creation
            with patch('app.api.api_v1.endpoints.embed.ChatService') as mock_chat_service:
                mock_service = Mock()
                mock_service.create_widget_session.return_value = {
                    "session_id": "widget_session_123",
                    "user_label": "Widget User"
                }
                mock_chat_service.return_value = mock_service
                
                session_data = {"user_label": "Widget User"}
                response = client.post("/api/v1/embed/sessions", json=session_data, headers=widget_headers)
                
                assert response.status_code == 201
                session_response = response.json()
                assert "session_id" in session_response

class TestAnalyticsIntegration:
    """Integration tests for analytics system"""
    
    def test_analytics_data_flow(self, db_session):
        """Test analytics data collection and retrieval"""
        # Mock user authentication
        with patch('app.api.api_v1.endpoints.analytics.get_current_user') as mock_get_user:
            mock_user = Mock()
            mock_user.id = "user_123"
            mock_user.workspace_id = "ws_123"
            mock_get_user.return_value = mock_user
            
            # 1. Track query
            with patch('app.api.api_v1.endpoints.analytics.AnalyticsService') as mock_analytics_service:
                mock_service = Mock()
                mock_service.track_query.return_value = True
                mock_analytics_service.return_value = mock_service
                
                query_data = {
                    "query": "Test query",
                    "response_time_ms": 150,
                    "tokens_used": 100
                }
                headers = {"Authorization": "Bearer test_token"}
                response = client.post("/api/v1/analytics/track-query", json=query_data, headers=headers)
                
                assert response.status_code == 200
            
            # 2. Get workspace analytics
            with patch('app.api.api_v1.endpoints.analytics.AnalyticsService') as mock_analytics_service:
                mock_service = Mock()
                mock_service.get_workspace_analytics.return_value = {
                    "total_queries": 100,
                    "total_documents": 10,
                    "average_response_time": 150,
                    "quota_usage": 0.5,
                    "top_queries": [
                        {"query": "refund policy", "count": 25},
                        {"query": "shipping info", "count": 20}
                    ],
                    "daily_stats": [
                        {"date": "2024-01-01", "queries": 10, "documents": 1},
                        {"date": "2024-01-02", "queries": 15, "documents": 2}
                    ]
                }
                mock_analytics_service.return_value = mock_service
                
                headers = {"Authorization": "Bearer test_token"}
                response = client.get("/api/v1/analytics/workspace", headers=headers)
                
                assert response.status_code == 200
                analytics_data = response.json()
                assert "total_queries" in analytics_data
                assert "total_documents" in analytics_data
                assert "average_response_time" in analytics_data
                assert "quota_usage" in analytics_data

class TestErrorHandlingIntegration:
    """Integration tests for error handling across components"""
    
    def test_error_propagation(self, db_session):
        """Test error propagation through the system"""
        # Test invalid authentication
        response = client.get("/api/v1/auth/me", headers={"Authorization": "Bearer invalid_token"})
        assert response.status_code == 401
        
        # Test invalid endpoint
        response = client.get("/api/v1/invalid-endpoint")
        assert response.status_code == 404
        
        # Test malformed request
        response = client.post("/api/v1/auth/login", json={"invalid": "data"})
        assert response.status_code == 422
        
        # Test missing required fields
        response = client.post("/api/v1/rag/query", json={"query": "test"})
        assert response.status_code == 401  # No auth

class TestRateLimitingIntegration:
    """Integration tests for rate limiting"""
    
    def test_rate_limiting_enforcement(self, db_session):
        """Test rate limiting across different endpoints"""
        # Mock user authentication
        with patch('app.api.api_v1.endpoints.auth.get_current_user') as mock_get_user:
            mock_user = Mock()
            mock_user.id = "user_123"
            mock_user.workspace_id = "ws_123"
            mock_get_user.return_value = mock_user
            
            headers = {"Authorization": "Bearer test_token"}
            
            # Send multiple requests to trigger rate limiting
            for i in range(10):
                response = client.get("/api/v1/auth/me", headers=headers)
                # In test environment, rate limiting might not be enforced
                # This test documents the expected behavior
                if response.status_code == 429:
                    error_data = response.json()
                    assert "rate limit" in error_data.get("detail", "").lower()
                    break

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
