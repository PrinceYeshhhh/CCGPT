"""
End-to-end tests for critical user journeys
Tests complete user workflows from start to finish
"""

import pytest
import asyncio
import time
import json
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.core.database import get_db, Base
from app.models import User, Workspace, Document, ChatSession, ChatMessage, Subscription
from app.services.auth import AuthService

# Test database configuration
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_e2e.db"

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

class TestNewUserOnboardingJourney:
    """Test complete new user onboarding journey"""
    
    def test_complete_user_onboarding_flow(self, client):
        """Test complete user onboarding from registration to first chat"""
        # Step 1: User visits landing page
        response = client.get("/")
        assert response.status_code == 200
        assert "CustomerCareGPT" in response.json()["message"]
        
        # Step 2: User registers
        user_data = {
            "email": "newuser@example.com",
            "password": "SecurePassword123!",
            "full_name": "New User",
            "workspace_name": "My Company"
        }
        
        response = client.post("/api/v1/auth/register", json=user_data)
        assert response.status_code == 201
        registration_data = response.json()
        
        auth_token = registration_data["access_token"]
        user_id = registration_data["user_id"]
        workspace_id = registration_data["workspace_id"]
        
        # Step 3: User logs in
        login_data = {
            "email": user_data["email"],
            "password": user_data["password"]
        }
        
        response = client.post("/api/v1/auth/login", json=login_data)
        assert response.status_code == 200
        login_data = response.json()
        assert "access_token" in login_data
        
        # Step 4: User uploads first document
        files = {"file": ("company_faq.txt", b"Q: What is your refund policy? A: 30 days", "text/plain")}
        data = {"workspace_id": workspace_id}
        
        response = client.post(
            "/api/v1/documents/upload",
            files=files,
            data=data,
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 201
        document_data = response.json()
        document_id = document_data["document_id"]
        
        # Step 5: User creates first chat session
        session_data = {
            "workspace_id": workspace_id,
            "user_label": "Customer Support"
        }
        
        response = client.post(
            "/api/v1/chat/sessions",
            json=session_data,
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 201
        session_data = response.json()
        session_id = session_data["session_id"]
        
        # Step 6: User asks first question
        message_data = {
            "content": "What is your refund policy?",
            "session_id": session_id
        }
        
        response = client.post(
            "/api/v1/chat/message",
            json=message_data,
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        message_response = response.json()
        assert "response" in message_response
        
        # Step 7: User checks analytics
        response = client.get(
            "/api/v1/analytics/workspace",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        analytics_data = response.json()
        assert "total_queries" in analytics_data
        
        # Step 8: User generates embed code
        embed_data = {
            "workspace_id": workspace_id,
            "config": {
                "theme": {"primary": "#4f46e5"},
                "welcomeMessage": "Hello! How can I help you?"
            }
        }
        
        response = client.post(
            "/api/v1/embed/generate",
            json=embed_data,
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 201
        embed_response = response.json()
        assert "embed_code_id" in embed_response
        assert "snippet" in embed_response

class TestCustomerSupportJourney:
    """Test complete customer support journey"""
    
    def test_customer_support_workflow(self, client, auth_token, test_workspace):
        """Test complete customer support workflow"""
        # Step 1: Upload knowledge base documents
        documents = [
            ("refund_policy.txt", b"Refund Policy: 30-day return window for all products"),
            ("shipping_info.txt", b"Shipping: Free shipping on orders over $50"),
            ("product_info.txt", b"Products: We sell high-quality widgets")
        ]
        
        uploaded_documents = []
        for filename, content, content_type in documents:
            files = {"file": (filename, content, "text/plain")}
            data = {"workspace_id": test_workspace.id}
            
            response = client.post(
                "/api/v1/documents/upload",
                files=files,
                data=data,
                headers={"Authorization": f"Bearer {auth_token}"}
            )
            assert response.status_code == 201
            uploaded_documents.append(response.json()["document_id"])
        
        # Step 2: Create multiple chat sessions for different customers
        customer_sessions = []
        for i in range(5):
            session_data = {
                "workspace_id": test_workspace.id,
                "user_label": f"Customer {i+1}"
            }
            
            response = client.post(
                "/api/v1/chat/sessions",
                json=session_data,
                headers={"Authorization": f"Bearer {auth_token}"}
            )
            assert response.status_code == 201
            customer_sessions.append(response.json()["session_id"])
        
        # Step 3: Handle various customer queries
        queries = [
            "What is your refund policy?",
            "How much does shipping cost?",
            "What products do you sell?",
            "How do I return an item?",
            "Do you offer international shipping?"
        ]
        
        for i, query in enumerate(queries):
            message_data = {
                "content": query,
                "session_id": customer_sessions[i % len(customer_sessions)]
            }
            
            response = client.post(
                "/api/v1/chat/message",
                json=message_data,
                headers={"Authorization": f"Bearer {auth_token}"}
            )
            assert response.status_code == 200
            message_response = response.json()
            assert "response" in message_response
            assert len(message_response["response"]) > 0
        
        # Step 4: Check chat history
        for session_id in customer_sessions:
            response = client.get(
                f"/api/v1/chat/sessions/{session_id}/messages",
                headers={"Authorization": f"Bearer {auth_token}"}
            )
            assert response.status_code == 200
            messages = response.json()
            assert len(messages) > 0
        
        # Step 5: Generate analytics report
        response = client.get(
            "/api/v1/analytics/workspace",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        analytics_data = response.json()
        assert analytics_data["total_queries"] >= len(queries)
        assert analytics_data["total_documents"] >= len(documents)

class TestDocumentManagementJourney:
    """Test complete document management journey"""
    
    def test_document_lifecycle_workflow(self, client, auth_token, test_workspace):
        """Test complete document lifecycle from upload to deletion"""
        # Step 1: Upload multiple documents
        documents = [
            ("manual_v1.pdf", b"PDF content", "application/pdf"),
            ("faq_v2.docx", b"Word content", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"),
            ("policies.txt", b"Text content", "text/plain"),
            ("spreadsheet.xlsx", b"Excel content", "application/vnd.openxmlxmlformats-officedocument.spreadsheetml.sheet")
        ]
        
        uploaded_documents = []
        for filename, content, content_type in documents:
            files = {"file": (filename, content, content_type)}
            data = {"workspace_id": test_workspace.id}
            
            response = client.post(
                "/api/v1/documents/upload",
                files=files,
                data=data,
                headers={"Authorization": f"Bearer {auth_token}"}
            )
            assert response.status_code == 201
            uploaded_documents.append(response.json()["document_id"])
        
        # Step 2: List all documents
        response = client.get(
            "/api/v1/documents/",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        documents_list = response.json()
        assert len(documents_list) == len(documents)
        
        # Step 3: Get document details
        for doc_id in uploaded_documents:
            response = client.get(
                f"/api/v1/documents/{doc_id}",
                headers={"Authorization": f"Bearer {auth_token}"}
            )
            assert response.status_code == 200
            doc_data = response.json()
            assert doc_data["id"] == doc_id
            assert doc_data["status"] in ["processing", "processed"]
        
        # Step 4: Get document chunks (if processed)
        for doc_id in uploaded_documents:
            response = client.get(
                f"/api/v1/documents/{doc_id}/chunks",
                headers={"Authorization": f"Bearer {auth_token}"}
            )
            assert response.status_code == 200
            chunks = response.json()
            assert isinstance(chunks, list)
        
        # Step 5: Test document search
        search_data = {
            "query": "refund policy",
            "workspace_id": test_workspace.id
        }
        
        response = client.post(
            "/api/v1/vector-search/search",
            json=search_data,
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        search_results = response.json()
        assert isinstance(search_results, list)
        
        # Step 6: Delete some documents
        for doc_id in uploaded_documents[:2]:  # Delete first two
            response = client.delete(
                f"/api/v1/documents/{doc_id}",
                headers={"Authorization": f"Bearer {auth_token}"}
            )
            assert response.status_code == 200
        
        # Step 7: Verify deletion
        response = client.get(
            "/api/v1/documents/",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        remaining_documents = response.json()
        assert len(remaining_documents) == len(documents) - 2

class TestBillingAndSubscriptionJourney:
    """Test complete billing and subscription journey"""
    
    def test_billing_workflow(self, client, auth_token):
        """Test complete billing workflow from free to paid"""
        # Step 1: Check initial billing status (free tier)
        response = client.get(
            "/api/v1/billing/status",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        billing_data = response.json()
        assert billing_data["tier"] == "free"
        
        # Step 2: Check quota usage
        response = client.get(
            "/api/v1/billing/quota",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        quota_data = response.json()
        assert "daily_usage" in quota_data
        assert "monthly_usage" in quota_data
        
        # Step 3: Create checkout session for upgrade
        checkout_data = {
            "plan_tier": "pro",
            "success_url": "http://localhost:3000/billing/success",
            "cancel_url": "http://localhost:3000/billing/cancel"
        }
        
        with patch('app.api.api_v1.endpoints.billing.StripeService') as mock_stripe:
            mock_service = Mock()
            mock_service.create_checkout_session.return_value = {
                "session_id": "cs_test_123",
                "checkout_url": "https://checkout.stripe.com/test"
            }
            mock_stripe.return_value = mock_service
            
            response = client.post(
                "/api/v1/billing/create-checkout-session",
                json=checkout_data,
                headers={"Authorization": f"Bearer {auth_token}"}
            )
            assert response.status_code == 200
            checkout_response = response.json()
            assert "session_id" in checkout_response
            assert "checkout_url" in checkout_response
        
        # Step 4: Simulate successful payment (webhook)
        webhook_payload = {
            "type": "checkout.session.completed",
            "data": {
                "object": {
                    "id": "cs_test_123",
                    "customer": "cus_test_123",
                    "subscription": "sub_test_123"
                }
            }
        }
        
        with patch('app.services.stripe_service.stripe.Webhook.construct_event') as mock_construct:
            mock_construct.return_value = webhook_payload
            
            response = client.post(
                "/api/v1/billing/webhook",
                data=json.dumps(webhook_payload),
                headers={
                    "Stripe-Signature": "test_signature",
                    "Content-Type": "application/json"
                }
            )
            assert response.status_code == 200
        
        # Step 5: Check updated billing status
        response = client.get(
            "/api/v1/billing/status",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        updated_billing = response.json()
        # Note: In real scenario, this would show pro tier after webhook processing

class TestAnalyticsAndReportingJourney:
    """Test complete analytics and reporting journey"""
    
    def test_analytics_workflow(self, client, auth_token, test_workspace):
        """Test complete analytics workflow"""
        # Step 1: Generate some activity
        # Upload documents
        files = {"file": ("analytics_test.txt", b"Test content for analytics", "text/plain")}
        data = {"workspace_id": test_workspace.id}
        
        response = client.post(
            "/api/v1/documents/upload",
            files=files,
            data=data,
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 201
        
        # Create chat sessions and send messages
        session_data = {
            "workspace_id": test_workspace.id,
            "user_label": "Analytics Test User"
        }
        
        response = client.post(
            "/api/v1/chat/sessions",
            json=session_data,
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 201
        session_id = response.json()["session_id"]
        
        # Send multiple messages
        for i in range(10):
            message_data = {
                "content": f"Test message {i+1}",
                "session_id": session_id
            }
            
            response = client.post(
                "/api/v1/chat/message",
                json=message_data,
                headers={"Authorization": f"Bearer {auth_token}"}
            )
            assert response.status_code == 200
        
        # Step 2: Get workspace analytics
        response = client.get(
            "/api/v1/analytics/workspace",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        workspace_analytics = response.json()
        assert "total_queries" in workspace_analytics
        assert "total_documents" in workspace_analytics
        assert "average_response_time" in workspace_analytics
        
        # Step 3: Get user analytics
        response = client.get(
            "/api/v1/analytics/user",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        user_analytics = response.json()
        assert "total_sessions" in user_analytics
        assert "total_documents" in user_analytics
        
        # Step 4: Get document analytics
        response = client.get(
            "/api/v1/analytics/documents",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        document_analytics = response.json()
        assert isinstance(document_analytics, list)
        
        # Step 5: Get usage statistics
        response = client.get(
            "/api/v1/analytics/usage?days=30",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        usage_stats = response.json()
        assert isinstance(usage_stats, list)

class TestEmbedWidgetJourney:
    """Test complete embed widget journey"""
    
    def test_embed_widget_workflow(self, client, auth_token, test_workspace):
        """Test complete embed widget workflow"""
        # Step 1: Generate embed code
        embed_data = {
            "workspace_id": test_workspace.id,
            "config": {
                "theme": {
                    "primary": "#4f46e5",
                    "secondary": "#6366f1"
                },
                "welcomeMessage": "Hello! How can I help you today?",
                "placeholder": "Type your question here...",
                "showSources": True
            }
        }
        
        response = client.post(
            "/api/v1/embed/generate",
            json=embed_data,
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 201
        embed_response = response.json()
        embed_code_id = embed_response["embed_code_id"]
        client_api_key = embed_response["client_api_key"]
        snippet = embed_response["snippet"]
        
        assert embed_code_id is not None
        assert client_api_key is not None
        assert snippet is not None
        assert "<script>" in snippet
        
        # Step 2: Test embed widget health check
        response = client.get(
            "/api/v1/embed/health",
            headers={"X-API-Key": client_api_key}
        )
        assert response.status_code == 200
        health_data = response.json()
        assert health_data["status"] == "healthy"
        
        # Step 3: Test embed widget query (simulate customer using widget)
        widget_query_data = {
            "query": "What is your refund policy?",
            "api_key": client_api_key
        }
        
        response = client.post(
            "/api/v1/embed/query",
            json=widget_query_data
        )
        assert response.status_code == 200
        query_response = response.json()
        assert "answer" in query_response
        assert "sources" in query_response
        
        # Step 4: Update embed configuration
        updated_config = {
            "theme": {
                "primary": "#10b981",
                "secondary": "#059669"
            },
            "welcomeMessage": "Welcome! I'm here to help.",
            "placeholder": "Ask me anything...",
            "showSources": False
        }
        
        response = client.put(
            f"/api/v1/embed/{embed_code_id}",
            json={"config": updated_config},
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        
        # Step 5: Get embed analytics
        response = client.get(
            f"/api/v1/embed/{embed_code_id}/analytics",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        analytics_data = response.json()
        assert "total_queries" in analytics_data
        assert "unique_visitors" in analytics_data

class TestErrorRecoveryJourney:
    """Test error recovery and resilience"""
    
    def test_error_recovery_workflow(self, client, auth_token, test_workspace):
        """Test system recovery from various error conditions"""
        # Step 1: Test graceful handling of invalid requests
        invalid_requests = [
            ("/api/v1/documents/", "GET", None, 401),  # No auth
            ("/api/v1/chat/sessions", "POST", {}, 422),  # Invalid data
            ("/api/v1/rag/query", "POST", {"query": ""}, 422),  # Empty query
        ]
        
        for endpoint, method, data, expected_status in invalid_requests:
            if method == "GET":
                response = client.get(endpoint)
            else:
                response = client.post(endpoint, json=data)
            
            assert response.status_code == expected_status
        
        # Step 2: Test recovery from service errors
        with patch('app.api.api_v1.endpoints.rag_query.RAGService') as mock_rag:
            mock_service = Mock()
            mock_service.process_query.side_effect = Exception("Service temporarily unavailable")
            mock_rag.return_value = mock_service
            
            query_data = {
                "query": "Test question",
                "session_id": "session_123"
            }
            
            response = client.post(
                "/api/v1/rag/query",
                json=query_data,
                headers={"Authorization": f"Bearer {auth_token}"}
            )
            assert response.status_code == 503  # Service unavailable
        
        # Step 3: Test system health after errors
        response = client.get("/health")
        assert response.status_code == 200
        health_data = response.json()
        assert health_data["status"] == "healthy"
        
        # Step 4: Test normal operation after errors
        response = client.get(
            "/api/v1/documents/",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
