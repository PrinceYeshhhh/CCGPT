"""
Comprehensive integration tests for production workflows
Tests complete end-to-end workflows and system integration
"""

import pytest
import sys
import os
import tempfile
import io
import json
from unittest.mock import Mock, patch, MagicMock
from fastapi.testclient import TestClient
from fastapi import status
import asyncio

# Add the backend directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from app.main import app
from app.models import User, Workspace, Document, DocumentChunk, ChatSession, ChatMessage, EmbedCode, Subscription
from app.core.database import get_db, Base
from app.services.auth import AuthService
from app.services.document_service import DocumentService
from app.services.chat import ChatService
from app.services.vector_service import VectorService
from app.services.gemini_service import GeminiService

client = TestClient(app)


class TestCompleteUserWorkflow:
    """Test complete user workflow from registration to document query"""
    
    def test_complete_user_journey(self, test_db):
        """Test complete user journey: registration -> login -> upload -> query"""
        # 1. User Registration
        user_data = {
            "email": "journey@example.com",
            "password": "SecurePassword123!",
            "mobile_phone": "+1234567890",
            "full_name": "Journey User"
        }
        
        response = client.post("/api/v1/auth/register", json=user_data)
        assert response.status_code == status.HTTP_201_CREATED
        user_response = response.json()
        assert user_response["user"]["email"] == user_data["email"]
        
        # 2. User Login
        login_data = {
            "identifier": user_data["email"],
            "password": user_data["password"]
        }
        
        response = client.post("/api/v1/auth/login", json=login_data)
        assert response.status_code == status.HTTP_200_OK
        login_response = response.json()
        auth_headers = {"Authorization": f"Bearer {login_response['access_token']}"}
        
        # 3. Verify User Profile
        response = client.get("/api/v1/auth/me", headers=auth_headers)
        assert response.status_code == status.HTTP_200_OK
        profile = response.json()
        assert profile["email"] == user_data["email"]
        
        # 4. Upload Document
        pdf_content = b"%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n/Pages 2 0 R\n>>\nendobj\n2 0 obj\n<<\n/Type /Pages\n/Kids [3 0 R]\n/Count 1\n>>\nendobj\n3 0 obj\n<<\n/Type /Page\n/Parent 2 0 R\n/MediaBox [0 0 612 792]\n/Contents 4 0 R\n>>\nendobj\n4 0 obj\n<<\n/Length 44\n>>\nstream\nBT\n/F1 12 Tf\n72 720 Td\n(Artificial Intelligence and Machine Learning) Tj\nET\nendstream\nendobj\nxref\n0 5\n0000000000 65535 f \n0000000009 00000 n \n0000000058 00000 n \n0000000115 00000 n \n0000000204 00000 n \ntrailer\n<<\n/Size 5\n/Root 1 0 R\n>>\nstartxref\n297\n%%EOF"
        
        files = {"file": ("ai_document.pdf", io.BytesIO(pdf_content), "application/pdf")}
        
        with patch('app.services.document_service.DocumentService.process_document') as mock_process:
            mock_process.return_value = {"job_id": "test_job_123", "status": "queued"}
            
            response = client.post("/api/v1/documents/upload", files=files, headers=auth_headers)
            assert response.status_code == status.HTTP_201_CREATED
            upload_response = response.json()
            document_id = upload_response["document_id"]
        
        # 5. Check Document Status
        with patch('app.services.document_service.DocumentService.get_job_status') as mock_status:
            mock_status.return_value = {
                "job_id": "test_job_123",
                "status": "finished",
                "result": {"document_id": document_id},
                "progress": 100
            }
            
            response = client.get("/api/v1/documents/jobs/test_job_123", headers=auth_headers)
            assert response.status_code == status.HTTP_200_OK
            job_status = response.json()
            assert job_status["status"] == "finished"
        
        # 6. List Documents
        response = client.get("/api/v1/documents/", headers=auth_headers)
        assert response.status_code == status.HTTP_200_OK
        documents = response.json()
        assert len(documents["documents"]) >= 1
        
        # 7. Create Chat Session
        session_data = {
            "visitor_ip": "127.0.0.1",
            "user_agent": "Mozilla/5.0 (Test Browser)"
        }
        
        response = client.post("/api/v1/chat/sessions", json=session_data, headers=auth_headers)
        assert response.status_code == status.HTTP_201_CREATED
        session_response = response.json()
        session_id = session_response["session_id"]
        
        # 8. Ask Question about Document
        query_data = {
            "message": "What is this document about?",
            "session_id": session_id,
            "context": {"document_ids": [document_id]}
        }
        
        with patch('app.services.vector_service.VectorService.search_similar_chunks') as mock_search, \
             patch('app.services.gemini_service.GeminiService.generate_response') as mock_gemini:
            
            mock_search.return_value = [
                {
                    "text": "This document is about artificial intelligence and machine learning.",
                    "metadata": {"document_id": document_id, "chunk_index": 0},
                    "distance": 0.1
                }
            ]
            
            mock_gemini.return_value = {
                "message": "This document is about artificial intelligence and machine learning, covering various topics in AI and ML.",
                "sources": [document_id],
                "confidence": "high"
            }
            
            response = client.post("/api/v1/chat/message", json=query_data, headers=auth_headers)
            assert response.status_code == status.HTTP_200_OK
            chat_response = response.json()
            assert "message" in chat_response
            assert "sources" in chat_response
            assert document_id in chat_response["sources"]
        
        # 9. Follow-up Question
        followup_data = {
            "message": "Can you tell me more about machine learning?",
            "session_id": session_id
        }
        
        with patch('app.services.gemini_service.GeminiService.generate_response') as mock_gemini:
            mock_gemini.return_value = {
                "message": "Machine learning is a subset of artificial intelligence that enables computers to learn without being explicitly programmed.",
                "sources": [document_id],
                "confidence": "high"
            }
            
            response = client.post("/api/v1/chat/message", json=followup_data, headers=auth_headers)
            assert response.status_code == status.HTTP_200_OK
        
        # 10. Get Chat History
        response = client.get(f"/api/v1/chat/sessions/{session_id}/messages", headers=auth_headers)
        assert response.status_code == status.HTTP_200_OK
        messages = response.json()
        assert len(messages["messages"]) >= 2  # At least 2 messages
        
        # 11. Logout
        response = client.post("/api/v1/auth/logout", headers=auth_headers)
        assert response.status_code == status.HTTP_200_OK


class TestMultiTenantWorkflow:
    """Test multi-tenant workflow with workspace isolation"""
    
    def test_workspace_isolation(self, test_db):
        """Test that users can only access their own workspace data"""
        # Create two workspaces and users
        workspace1 = Workspace(name="Workspace 1")
        workspace2 = Workspace(name="Workspace 2")
        test_db.add_all([workspace1, workspace2])
        test_db.commit()
        
        user1 = User(
            email="user1@example.com",
            hashed_password="hashed1",
            mobile_phone="+1111111111",
            full_name="User 1",
            workspace_id=workspace1.id
        )
        user2 = User(
            email="user2@example.com",
            hashed_password="hashed2",
            mobile_phone="+2222222222",
            full_name="User 2",
            workspace_id=workspace2.id
        )
        test_db.add_all([user1, user2])
        test_db.commit()
        
        # Create documents for each user
        doc1 = Document(
            filename="doc1.pdf",
            content_type="application/pdf",
            size=1024,
            status="done",
            workspace_id=workspace1.id,
            uploaded_by=user1.id
        )
        doc2 = Document(
            filename="doc2.pdf",
            content_type="application/pdf",
            size=2048,
            status="done",
            workspace_id=workspace2.id,
            uploaded_by=user2.id
        )
        test_db.add_all([doc1, doc2])
        test_db.commit()
        
        # Login as user1
        login_data = {"identifier": user1.email, "password": "test_password_123"}
        response = client.post("/api/v1/auth/login", json=login_data)
        user1_headers = {"Authorization": f"Bearer {response.json()['access_token']}"}
        
        # Login as user2
        login_data = {"identifier": user2.email, "password": "test_password_123"}
        response = client.post("/api/v1/auth/login", json=login_data)
        user2_headers = {"Authorization": f"Bearer {response.json()['access_token']}"}
        
        # User1 should only see their own documents
        response = client.get("/api/v1/documents/", headers=user1_headers)
        assert response.status_code == status.HTTP_200_OK
        documents = response.json()
        assert len(documents["documents"]) == 1
        assert documents["documents"][0]["filename"] == "doc1.pdf"
        
        # User2 should only see their own documents
        response = client.get("/api/v1/documents/", headers=user2_headers)
        assert response.status_code == status.HTTP_200_OK
        documents = response.json()
        assert len(documents["documents"]) == 1
        assert documents["documents"][0]["filename"] == "doc2.pdf"
        
        # User1 should not be able to access user2's document
        response = client.get(f"/api/v1/documents/{doc2.id}", headers=user1_headers)
        assert response.status_code in [status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND]
        
        # User2 should not be able to access user1's document
        response = client.get(f"/api/v1/documents/{doc1.id}", headers=user2_headers)
        assert response.status_code in [status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND]


class TestEmbedWidgetWorkflow:
    """Test embed widget workflow"""
    
    def test_embed_widget_creation_and_usage(self, test_user, auth_headers):
        """Test creating and using embed widget"""
        # 1. Create Embed Code
        embed_data = {
            "title": "Customer Support",
            "primary_color": "#007bff",
            "position": "bottom-right",
            "welcome_message": "Hello! How can I help you?"
        }
        
        response = client.post("/api/v1/embed/codes", json=embed_data, headers=auth_headers)
        assert response.status_code == status.HTTP_201_CREATED
        embed_response = response.json()
        embed_code_id = embed_response["code_id"]
        api_key = embed_response["api_key"]
        
        # 2. Get Embed Code
        response = client.get(f"/api/v1/embed/codes/{embed_code_id}", headers=auth_headers)
        assert response.status_code == status.HTTP_200_OK
        embed_code = response.json()
        assert embed_code["title"] == embed_data["title"]
        
        # 3. Test Widget Chat (using API key)
        widget_headers = {"X-Client-API-Key": api_key}
        chat_data = {
            "message": "Hello, I need help",
            "session_id": None
        }
        
        with patch('app.services.gemini_service.GeminiService.generate_response') as mock_gemini:
            mock_gemini.return_value = {
                "message": "Hello! I'm here to help you. What do you need assistance with?",
                "sources": [],
                "confidence": "high"
            }
            
            response = client.post("/api/v1/embed/chat", json=chat_data, headers=widget_headers)
            assert response.status_code == status.HTTP_200_OK
            chat_response = response.json()
            assert "message" in chat_response
        
        # 4. Update Embed Code
        update_data = {
            "title": "Updated Support",
            "primary_color": "#28a745"
        }
        
        response = client.put(f"/api/v1/embed/codes/{embed_code_id}", json=update_data, headers=auth_headers)
        assert response.status_code == status.HTTP_200_OK
        updated_embed = response.json()
        assert updated_embed["title"] == update_data["title"]
        
        # 5. List Embed Codes
        response = client.get("/api/v1/embed/codes", headers=auth_headers)
        assert response.status_code == status.HTTP_200_OK
        embed_codes = response.json()
        assert len(embed_codes["embed_codes"]) >= 1
        
        # 6. Delete Embed Code
        response = client.delete(f"/api/v1/embed/codes/{embed_code_id}", headers=auth_headers)
        assert response.status_code == status.HTTP_200_OK


class TestBillingWorkflow:
    """Test billing and subscription workflow"""
    
    def test_subscription_workflow(self, test_user, auth_headers):
        """Test subscription management workflow"""
        # 1. Get Current Billing Status
        response = client.get("/api/v1/billing/status", headers=auth_headers)
        assert response.status_code == status.HTTP_200_OK
        billing_status = response.json()
        assert "subscription" in billing_status
        assert "usage" in billing_status
        
        # 2. Get Available Plans
        response = client.get("/api/v1/billing/plans", headers=auth_headers)
        assert response.status_code == status.HTTP_200_OK
        plans = response.json()
        assert "plans" in plans
        assert len(plans["plans"]) > 0
        
        # 3. Create Checkout Session (mock)
        checkout_data = {
            "price_id": "price_test_123",
            "success_url": "https://example.com/success",
            "cancel_url": "https://example.com/cancel"
        }
        
        with patch('app.services.billing_service.BillingService.create_checkout_session') as mock_checkout:
            mock_checkout.return_value = {
                "session_id": "cs_test_123",
                "url": "https://checkout.stripe.com/test"
            }
            
            response = client.post("/api/v1/billing/checkout", json=checkout_data, headers=auth_headers)
            assert response.status_code == status.HTTP_200_OK
            checkout_response = response.json()
            assert "session_id" in checkout_response
            assert "url" in checkout_response
        
        # 4. Get Usage Statistics
        response = client.get("/api/v1/billing/usage", headers=auth_headers)
        assert response.status_code == status.HTTP_200_OK
        usage = response.json()
        assert "current_period" in usage
        assert "queries_used" in usage
        assert "queries_limit" in usage


class TestAnalyticsWorkflow:
    """Test analytics and reporting workflow"""
    
    def test_analytics_workflow(self, test_user, auth_headers, test_document, test_chat_session):
        """Test analytics data collection and retrieval"""
        # 1. Get Overview Analytics
        response = client.get("/api/v1/analytics/overview", headers=auth_headers)
        assert response.status_code == status.HTTP_200_OK
        overview = response.json()
        assert "total_documents" in overview
        assert "total_messages" in overview
        assert "active_sessions" in overview
        
        # 2. Get Usage Statistics
        response = client.get("/api/v1/analytics/usage-stats?days=7", headers=auth_headers)
        assert response.status_code == status.HTTP_200_OK
        usage_stats = response.json()
        assert "period" in usage_stats
        assert "queries" in usage_stats
        
        # 3. Get Document Analytics
        response = client.get(f"/api/v1/analytics/documents/{test_document.id}", headers=auth_headers)
        assert response.status_code == status.HTTP_200_OK
        doc_analytics = response.json()
        assert "document_id" in doc_analytics
        assert "queries_count" in doc_analytics
        
        # 4. Get Chat Session Analytics
        response = client.get(f"/api/v1/analytics/sessions/{test_chat_session.id}", headers=auth_headers)
        assert response.status_code == status.HTTP_200_OK
        session_analytics = response.json()
        assert "session_id" in session_analytics
        assert "message_count" in session_analytics
        
        # 5. Get KPIs
        response = client.get("/api/v1/analytics/kpis?days=30", headers=auth_headers)
        assert response.status_code == status.HTTP_200_OK
        kpis = response.json()
        assert "response_time" in kpis
        assert "satisfaction_score" in kpis
        assert "conversion_rate" in kpis


class TestErrorRecoveryWorkflow:
    """Test error recovery and resilience workflows"""
    
    def test_database_connection_recovery(self, test_user, auth_headers):
        """Test recovery from database connection failures"""
        # Simulate database connection failure
        with patch('app.core.database.get_db') as mock_db:
            mock_db.side_effect = Exception("Database connection failed")
            
            response = client.get("/api/v1/auth/me", headers=auth_headers)
            assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
            
            # Verify error response format
            data = response.json()
            assert "error" in data
            assert "error_id" in data
    
    def test_redis_connection_recovery(self, test_user, auth_headers):
        """Test recovery from Redis connection failures"""
        # Simulate Redis connection failure
        with patch('app.core.database.redis_manager.get') as mock_redis:
            mock_redis.side_effect = Exception("Redis connection failed")
            
            # This should fall back to in-memory rate limiting
            response = client.get("/api/v1/auth/me", headers=auth_headers)
            assert response.status_code == status.HTTP_200_OK
    
    def test_external_api_failure_recovery(self, test_user, auth_headers):
        """Test recovery from external API failures"""
        query_data = {
            "message": "Test query",
            "session_id": None
        }
        
        # Simulate Gemini API failure
        with patch('app.services.gemini_service.GeminiService.generate_response') as mock_gemini:
            mock_gemini.side_effect = Exception("Gemini API unavailable")
            
            response = client.post("/api/v1/chat/message", json=query_data, headers=auth_headers)
            assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
            
            # Verify error response format
            data = response.json()
            assert "error" in data
            assert "service" in data["error"].lower()


class TestPerformanceWorkflow:
    """Test performance and scalability workflows"""
    
    def test_concurrent_document_uploads(self, test_user, auth_headers):
        """Test concurrent document uploads"""
        import asyncio
        
        async def upload_document(doc_num):
            pdf_content = b"%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n/Pages 2 0 R\n>>\nendobj\n2 0 obj\n<<\n/Type /Pages\n/Kids [3 0 R]\n/Count 1\n>>\nendobj\n3 0 obj\n<<\n/Type /Page\n/Parent 2 0 R\n/MediaBox [0 0 612 792]\n/Contents 4 0 R\n>>\nendobj\n4 0 obj\n<<\n/Length 44\n>>\nstream\nBT\n/F1 12 Tf\n72 720 Td\n(Document " + str(doc_num).encode() + b") Tj\nET\nendstream\nendobj\nxref\n0 5\n0000000000 65535 f \n0000000009 00000 n \n0000000058 00000 n \n0000000115 00000 n \n0000000204 00000 n \ntrailer\n<<\n/Size 5\n/Root 1 0 R\n>>\nstartxref\n297\n%%EOF"
            
            files = {"file": (f"doc{doc_num}.pdf", io.BytesIO(pdf_content), "application/pdf")}
            
            with patch('app.services.document_service.DocumentService.process_document') as mock_process:
                mock_process.return_value = {"job_id": f"job_{doc_num}", "status": "queued"}
                
                response = client.post("/api/v1/documents/upload", files=files, headers=auth_headers)
                return response.status_code
        
        # Upload multiple documents concurrently
        async def run_concurrent_uploads():
            tasks = [upload_document(i) for i in range(5)]
            results = await asyncio.gather(*tasks)
            return results
        
        results = asyncio.run(run_concurrent_uploads())
        
        # All should succeed
        for status_code in results:
            assert status_code == status.HTTP_201_CREATED
    
    def test_concurrent_chat_queries(self, test_user, auth_headers):
        """Test concurrent chat queries"""
        import asyncio
        
        async def make_chat_query(query_num):
            query_data = {
                "message": f"Test query {query_num}",
                "session_id": None
            }
            
            with patch('app.services.gemini_service.GeminiService.generate_response') as mock_gemini:
                mock_gemini.return_value = {
                    "message": f"Response to query {query_num}",
                    "sources": [],
                    "confidence": "medium"
                }
                
                response = client.post("/api/v1/chat/message", json=query_data, headers=auth_headers)
                return response.status_code
        
        # Make multiple concurrent queries
        async def run_concurrent_queries():
            tasks = [make_chat_query(i) for i in range(10)]
            results = await asyncio.gather(*tasks)
            return results
        
        results = asyncio.run(run_concurrent_queries())
        
        # All should succeed
        for status_code in results:
            assert status_code == status.HTTP_200_OK
    
    def test_large_document_processing(self, test_user, auth_headers):
        """Test processing of large documents"""
        # Create a large document (simulate)
        large_content = b"Large document content. " * 10000  # ~250KB
        
        files = {"file": ("large_document.txt", io.BytesIO(large_content), "text/plain")}
        
        with patch('app.services.document_service.DocumentService.process_document') as mock_process:
            mock_process.return_value = {"job_id": "large_job_123", "status": "queued"}
            
            response = client.post("/api/v1/documents/upload", files=files, headers=auth_headers)
            assert response.status_code == status.HTTP_201_CREATED
            
            upload_response = response.json()
            assert "job_id" in upload_response
            assert upload_response["status"] == "queued"


class TestSecurityWorkflow:
    """Test security workflows and protections"""
    
    def test_rate_limiting_workflow(self, test_user, auth_headers):
        """Test rate limiting across different endpoints"""
        # Test login rate limiting
        login_data = {
            "identifier": test_user.email,
            "password": "wrong_password"
        }
        
        # Make multiple failed login attempts
        for i in range(10):
            response = client.post("/api/v1/auth/login", json=login_data)
            if i < 5:
                assert response.status_code == status.HTTP_401_UNAUTHORIZED
            else:
                assert response.status_code == status.HTTP_429_TOO_MANY_REQUESTS
        
        # Test API rate limiting
        query_data = {"message": "Test query", "session_id": None}
        
        with patch('app.services.gemini_service.GeminiService.generate_response') as mock_gemini:
            mock_gemini.return_value = {
                "message": "Test response",
                "sources": [],
                "confidence": "medium"
            }
            
            # Make many rapid API requests
            for i in range(20):
                response = client.post("/api/v1/chat/message", json=query_data, headers=auth_headers)
                if i < 10:
                    assert response.status_code == status.HTTP_200_OK
                else:
                    assert response.status_code == status.HTTP_429_TOO_MANY_REQUESTS
    
    def test_input_validation_workflow(self, test_user, auth_headers):
        """Test input validation across different endpoints"""
        # Test malicious input in document upload
        malicious_files = [
            ("malicious.pdf", b"<script>alert('xss')</script>", "application/pdf"),
            ("malicious.txt", b"'; DROP TABLE documents; --", "text/plain"),
        ]
        
        for filename, content, content_type in malicious_files:
            files = {"file": (filename, io.BytesIO(content), content_type)}
            
            with patch('app.services.document_service.FileValidator.scan_file') as mock_scan:
                mock_scan.return_value = {"is_safe": False, "threats": ["XSS", "SQL Injection"]}
                
                response = client.post("/api/v1/documents/upload", files=files, headers=auth_headers)
                assert response.status_code == status.HTTP_400_BAD_REQUEST
        
        # Test malicious input in chat queries
        malicious_queries = [
            "<script>alert('xss')</script>",
            "'; DROP TABLE chat_messages; --",
            "{{7*7}}",
            "{{config.items()}}",
        ]
        
        for malicious_query in malicious_queries:
            query_data = {
                "message": malicious_query,
                "session_id": None
            }
            
            with patch('app.services.gemini_service.GeminiService.generate_response') as mock_gemini:
                mock_gemini.return_value = {
                    "message": "I cannot process that request.",
                    "sources": [],
                    "confidence": "low"
                }
                
                response = client.post("/api/v1/chat/message", json=query_data, headers=auth_headers)
                # Should either succeed with sanitized response or fail validation
                assert response.status_code in [200, 400, 422]
    
    def test_authentication_workflow(self, test_user):
        """Test authentication workflow and token management"""
        # Test login with correct credentials
        login_data = {
            "identifier": test_user.email,
            "password": "test_password_123"
        }
        
        response = client.post("/api/v1/auth/login", json=login_data)
        assert response.status_code == status.HTTP_200_OK
        login_response = response.json()
        
        # Test token usage
        auth_headers = {"Authorization": f"Bearer {login_response['access_token']}"}
        response = client.get("/api/v1/auth/me", headers=auth_headers)
        assert response.status_code == status.HTTP_200_OK
        
        # Test token refresh
        refresh_data = {"refresh_token": login_response["refresh_token"]}
        response = client.post("/api/v1/auth/refresh", json=refresh_data)
        assert response.status_code == status.HTTP_200_OK
        
        # Test logout
        response = client.post("/api/v1/auth/logout", headers=auth_headers)
        assert response.status_code == status.HTTP_200_OK
        
        # Test that token is invalidated after logout
        response = client.get("/api/v1/auth/me", headers=auth_headers)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
