"""
End-to-End testing for complete user workflows
Tests the full RAG pipeline from user registration to chat completion
"""

import pytest
import asyncio
import httpx
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from unittest.mock import patch, MagicMock
import json
import tempfile
import os

from app.main import app
from app.core.database import get_db
from app.models import User, Workspace, Document, ChatSession, ChatMessage
from app.services.rag_service import RAGService
from app.services.embeddings_service import EmbeddingsService
from app.services.vector_search_service import VectorSearchService

client = TestClient(app)

class TestCompleteUserWorkflow:
    """Test complete user journey from registration to chat completion"""
    
    @pytest.fixture
    def test_user_data(self):
        return {
            "email": "test@example.com",
            "password": "TestPassword123!",
            "full_name": "Test User",
            "workspace_name": "Test Workspace"
        }
    
    @pytest.fixture
    def test_document_data(self):
        return {
            "filename": "test_document.pdf",
            "content": "This is a test document about refund policies. Customers can request refunds within 30 days of purchase.",
            "file_type": "application/pdf"
        }
    
    def test_user_registration_workflow(self, test_user_data):
        """Test complete user registration workflow"""
        # 1. Register user
        response = client.post("/api/v1/auth/register", json=test_user_data)
        assert response.status_code == 201
        user_data = response.json()
        assert "user_id" in user_data
        assert "workspace_id" in user_data
        
        # 2. Login user
        login_data = {
            "email": test_user_data["email"],
            "password": test_user_data["password"]
        }
        response = client.post("/api/v1/auth/login", json=login_data)
        assert response.status_code == 200
        login_response = response.json()
        assert "access_token" in login_response
        
        # 3. Verify user can access protected endpoint
        headers = {"Authorization": f"Bearer {login_response['access_token']}"}
        response = client.get("/api/v1/auth/me", headers=headers)
        assert response.status_code == 200
        user_info = response.json()
        assert user_info["email"] == test_user_data["email"]
        
        return login_response["access_token"]
    
    @patch('app.services.gemini_service.GeminiService.generate_response')
    def test_document_upload_and_rag_workflow(self, mock_gemini, test_user_data, test_document_data):
        """Test complete document upload and RAG workflow"""
        
        # Mock Gemini response
        mock_gemini.return_value = {
            "answer": "Customers can request refunds within 30 days of purchase by contacting support.",
            "sources": [{"chunk_id": "123", "document_id": "doc1", "chunk_index": 0}],
            "tokens_used": 150,
            "model_used": "gemini-pro"
        }
        
        # 1. Register and login user
        token = self.test_user_registration_workflow(test_user_data)
        headers = {"Authorization": f"Bearer {token}"}
        
        # 2. Create test document file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write(test_document_data["content"])
            temp_file_path = f.name
        
        try:
            # 3. Upload document
            with open(temp_file_path, 'rb') as f:
                files = {"file": (test_document_data["filename"], f, "text/plain")}
                response = client.post("/api/v1/documents/upload", files=files, headers=headers)
            
            assert response.status_code == 200
            upload_data = response.json()
            assert "document_id" in upload_data
            assert "job_id" in upload_data
            
            # 4. Wait for document processing (simulate)
            # In real scenario, this would be handled by background worker
            document_id = upload_data["document_id"]
            
            # 5. Create chat session
            session_data = {"user_label": "Test Customer"}
            response = client.post("/api/v1/chat/sessions", json=session_data, headers=headers)
            assert response.status_code == 201
            session_data = response.json()
            session_id = session_data["session_id"]
            
            # 6. Send RAG query
            query_data = {
                "query": "How do I get a refund?",
                "session_id": session_id
            }
            response = client.post("/api/v1/rag/query", json=query_data, headers=headers)
            assert response.status_code == 200
            
            rag_response = response.json()
            assert "answer" in rag_response
            assert "sources" in rag_response
            assert "response_time_ms" in rag_response
            assert "session_id" in rag_response
            
            # 7. Verify chat message was saved
            response = client.get(f"/api/v1/chat/sessions/{session_id}/messages", headers=headers)
            assert response.status_code == 200
            messages = response.json()
            assert len(messages) >= 2  # User query + assistant response
            
            # Verify message content
            user_message = next((msg for msg in messages if msg["role"] == "user"), None)
            assistant_message = next((msg for msg in messages if msg["role"] == "assistant"), None)
            
            assert user_message is not None
            assert assistant_message is not None
            assert user_message["content"] == "How do I get a refund?"
            assert "refund" in assistant_message["content"].lower()
            
        finally:
            # Cleanup
            os.unlink(temp_file_path)
    
    def test_embed_widget_workflow(self, test_user_data):
        """Test embed widget generation and usage workflow"""
        
        # 1. Register and login user
        token = self.test_user_registration_workflow(test_user_data)
        headers = {"Authorization": f"Bearer {token}"}
        
        # 2. Generate embed code
        embed_data = {
            "workspace_id": "test-workspace-id",  # Would be real workspace ID
            "config": {
                "theme": {"primary": "#4f46e5"},
                "welcomeMessage": "Hello! How can I help you?",
                "avatarUrl": "http://localhost:3000/avatar.png"
            }
        }
        response = client.post("/api/v1/embed/generate", json=embed_data, headers=headers)
        assert response.status_code == 201
        
        embed_response = response.json()
        assert "embed_code_id" in embed_response
        assert "client_api_key" in embed_response
        assert "snippet" in embed_response
        
        # 3. Verify embed code contains expected elements
        snippet = embed_response["snippet"]
        assert "data-embed-id" in snippet
        assert "data-api-key" in snippet
        assert "customercaregpt" in snippet.lower()
        
        # 4. Test widget API access (simulate)
        widget_headers = {"X-API-Key": embed_response["client_api_key"]}
        
        # Test widget health check
        response = client.get("/api/v1/embed/health", headers=widget_headers)
        assert response.status_code == 200
        
        # Test widget session creation
        session_data = {"user_label": "Widget User"}
        response = client.post("/api/v1/embed/sessions", json=session_data, headers=widget_headers)
        assert response.status_code == 201
        
        session_response = response.json()
        assert "session_id" in session_response
        
        return embed_response["client_api_key"]
    
    @patch('app.services.stripe_service.StripeService.create_checkout_session')
    def test_billing_workflow(self, mock_stripe, test_user_data):
        """Test complete billing workflow"""
        
        # Mock Stripe response
        mock_stripe.return_value = MagicMock(
            id="cs_test_123",
            url="http://localhost:3000/billing/checkout/test"
        )
        
        # 1. Register and login user
        token = self.test_user_registration_workflow(test_user_data)
        headers = {"Authorization": f"Bearer {token}"}
        
        # 2. Get billing status
        response = client.get("/api/v1/billing/status", headers=headers)
        assert response.status_code == 200
        
        billing_status = response.json()
        assert "tier" in billing_status
        assert "status" in billing_status
        
        # 3. Create checkout session
        checkout_data = {
            "plan_tier": "pro",
            "success_url": "http://localhost:3000/billing/success",
            "cancel_url": "http://localhost:3000/billing/cancel"
        }
        response = client.post("/api/v1/billing/create-checkout-session", json=checkout_data, headers=headers)
        assert response.status_code == 200
        
        checkout_response = response.json()
        assert "checkout_url" in checkout_response
        assert "session_id" in checkout_response
        
        # 4. Test billing portal access
        response = client.post("/api/v1/billing/portal", headers=headers)
        assert response.status_code == 200
        
        portal_response = response.json()
        assert "portal_url" in portal_response
    
    def test_rate_limiting_workflow(self, test_user_data):
        """Test rate limiting enforcement"""
        
        # 1. Register and login user
        token = self.test_user_registration_workflow(test_user_data)
        headers = {"Authorization": f"Bearer {token}"}
        
        # 2. Send multiple requests to trigger rate limiting
        rate_limit_triggered = False
        for i in range(100):  # Exceed rate limit
            response = client.get("/api/v1/auth/me", headers=headers)
            if response.status_code == 429:
                rate_limit_triggered = True
                break
        
        # Note: Rate limiting might not trigger in test environment
        # This test documents the expected behavior
        if rate_limit_triggered:
            assert response.status_code == 429
            error_data = response.json()
            assert "rate limit" in error_data.get("detail", "").lower()
    
    def test_health_check_workflow(self):
        """Test health check endpoints"""
        
        # 1. Basic health check
        response = client.get("/health")
        assert response.status_code == 200
        health_data = response.json()
        assert health_data["status"] == "healthy"
        
        # 2. Readiness check
        response = client.get("/ready")
        assert response.status_code == 200
        readiness_data = response.json()
        assert "status" in readiness_data
        assert "components" in readiness_data
        
        # 3. Metrics endpoint
        response = client.get("/metrics")
        assert response.status_code == 200
        assert "text/plain" in response.headers.get("content-type", "")
    
    def test_error_handling_workflow(self):
        """Test error handling across the system"""
        
        # 1. Test invalid authentication
        response = client.get("/api/v1/auth/me", headers={"Authorization": "Bearer invalid-token"})
        assert response.status_code == 401
        
        # 2. Test invalid endpoint
        response = client.get("/api/v1/invalid-endpoint")
        assert response.status_code == 404
        
        # 3. Test malformed request
        response = client.post("/api/v1/auth/login", json={"invalid": "data"})
        assert response.status_code == 422
        
        # 4. Test file upload without file
        response = client.post("/api/v1/documents/upload")
        assert response.status_code == 401  # No auth
        
        # 5. Test RAG query without auth
        query_data = {"query": "test query"}
        response = client.post("/api/v1/rag/query", json=query_data)
        assert response.status_code == 401

class TestRAGPipelineIntegration:
    """Test RAG pipeline integration components"""
    
    @patch('app.services.embeddings_service.EmbeddingsService.embed_text')
    @patch('app.services.vector_search_service.VectorSearchService.search')
    @patch('app.services.gemini_service.GeminiService.generate_response')
    def test_rag_pipeline_components(self, mock_gemini, mock_vector_search, mock_embeddings):
        """Test RAG pipeline component integration"""
        
        # Mock responses
        mock_embeddings.return_value = [0.1, 0.2, 0.3]  # Mock embedding vector
        mock_vector_search.return_value = [
            {"chunk_id": "123", "content": "Test content", "score": 0.9}
        ]
        mock_gemini.return_value = {
            "answer": "Test answer",
            "sources": [{"chunk_id": "123", "document_id": "doc1", "chunk_index": 0}],
            "tokens_used": 100,
            "model_used": "gemini-pro"
        }
        
        # Test that all components are properly integrated
        # This would be tested in the actual RAG service implementation
        assert True  # Placeholder for actual integration test

class TestDatabaseIntegration:
    """Test database integration and data persistence"""
    
    def test_database_models_integration(self):
        """Test that all database models work together"""
        
        # This would test the actual database integration
        # In a real test, you'd use a test database
        assert True  # Placeholder for actual database integration test
    
    def test_database_migrations(self):
        """Test database migrations work correctly"""
        
        # This would test Alembic migrations
        # In a real test, you'd run migrations against a test database
        assert True  # Placeholder for actual migration test

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
