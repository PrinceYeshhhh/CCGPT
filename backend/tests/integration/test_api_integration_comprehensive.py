"""
Comprehensive integration tests for API endpoints
Tests real database interactions, authentication, and end-to-end workflows
"""

import pytest
import asyncio
import json
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.core.database import get_db, Base
from app.models.user import User
from app.models.workspace import Workspace
from app.models.document import Document
from app.models.chat import ChatSession, ChatMessage
from app.models.subscriptions import Subscription
from app.services.auth import AuthService
from app.services.document_service import DocumentService
from app.services.chat import ChatService
from app.services.rag_service import RAGService

# Test database configuration
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_integration.db"

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

@pytest.fixture
def test_workspace(db_session):
    """Create a test workspace."""
    workspace = Workspace(
        id="test-workspace-id",
        name="Test Workspace",
        domain="test.example.com"
    )
    db_session.add(workspace)
    db_session.commit()
    db_session.refresh(workspace)
    return workspace

@pytest.fixture
def test_user(db_session, test_workspace):
    """Create a test user."""
    user = User(
        email="test@example.com",
        hashed_password="$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj4J/HS.s.2",  # "password"
        full_name="Test User",
        workspace_id=test_workspace.id,
        is_active=True
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user

@pytest.fixture
def auth_token(test_user):
    """Create an authentication token for the test user."""
    auth_service = AuthService(None)
    return auth_service.create_access_token({"user_id": str(test_user.id), "email": test_user.email})

class TestUserRegistrationWorkflow:
    """Test complete user registration workflow"""
    
    def test_user_registration_creates_workspace_and_user(self, client):
        """Test that user registration creates both user and workspace"""
        user_data = {
            "email": "newuser@example.com",
            "password": "SecurePassword123!",
            "full_name": "New User",
            "workspace_name": "New Workspace"
        }
        
        response = client.post("/api/v1/auth/register", json=user_data)
        
        assert response.status_code == 201
        data = response.json()
        assert "user_id" in data
        assert "workspace_id" in data
        assert data["email"] == user_data["email"]
        assert data["full_name"] == user_data["full_name"]
    
    def test_user_registration_creates_subscription(self, client):
        """Test that user registration creates a default subscription"""
        user_data = {
            "email": "newuser@example.com",
            "password": "SecurePassword123!",
            "full_name": "New User",
            "workspace_name": "New Workspace"
        }
        
        response = client.post("/api/v1/auth/register", json=user_data)
        
        assert response.status_code == 201
        data = response.json()
        
        # Check that subscription was created
        subscription_response = client.get(
            "/api/v1/billing/status",
            headers={"Authorization": f"Bearer {data['access_token']}"}
        )
        assert subscription_response.status_code == 200
        subscription_data = subscription_response.json()
        assert subscription_data["tier"] == "free"

class TestDocumentUploadWorkflow:
    """Test complete document upload and processing workflow"""
    
    def test_document_upload_workflow(self, client, auth_token, test_workspace):
        """Test complete document upload workflow"""
        # Upload document
        files = {"file": ("test_document.txt", b"This is a test document content.", "text/plain")}
        data = {"workspace_id": test_workspace.id}
        
        response = client.post(
            "/api/v1/documents/upload",
            files=files,
            data=data,
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        assert response.status_code == 201
        upload_data = response.json()
        assert "document_id" in upload_data
        assert "job_id" in upload_data
        
        # Check document status
        document_id = upload_data["document_id"]
        status_response = client.get(
            f"/api/v1/documents/{document_id}",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        assert status_response.status_code == 200
        document_data = status_response.json()
        assert document_data["filename"] == "test_document.txt"
        assert document_data["status"] in ["processing", "processed"]
    
    def test_document_processing_with_chunks(self, client, auth_token, test_workspace):
        """Test document processing creates chunks"""
        # Upload document
        files = {"file": ("test_document.txt", b"This is a test document with enough content to be chunked. " * 100, "text/plain")}
        data = {"workspace_id": test_workspace.id}
        
        response = client.post(
            "/api/v1/documents/upload",
            files=files,
            data=data,
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        assert response.status_code == 201
        upload_data = response.json()
        document_id = upload_data["document_id"]
        
        # Wait for processing (in real scenario, this would be async)
        # For test, we'll check that chunks endpoint exists
        chunks_response = client.get(
            f"/api/v1/documents/{document_id}/chunks",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        # Should return chunks (even if empty initially)
        assert chunks_response.status_code == 200
        chunks_data = chunks_response.json()
        assert isinstance(chunks_data, list)

class TestChatWorkflow:
    """Test complete chat workflow"""
    
    def test_chat_session_creation_and_messaging(self, client, auth_token, test_workspace):
        """Test creating chat session and sending messages"""
        # Create chat session
        session_data = {
            "workspace_id": test_workspace.id,
            "user_label": "Test Customer"
        }
        
        response = client.post(
            "/api/v1/chat/sessions",
            json=session_data,
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        assert response.status_code == 201
        session_data = response.json()
        session_id = session_data["session_id"]
        
        # Send a message
        message_data = {
            "content": "Hello, I need help with my order",
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
        assert "message_id" in message_response
    
    def test_chat_with_rag_integration(self, client, auth_token, test_workspace, test_user):
        """Test chat with RAG integration"""
        # First upload a document
        files = {"file": ("faq.txt", b"Q: What is your refund policy? A: We offer 30-day returns.", "text/plain")}
        data = {"workspace_id": test_workspace.id}
        
        upload_response = client.post(
            "/api/v1/documents/upload",
            files=files,
            data=data,
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        assert upload_response.status_code == 201
        
        # Create chat session
        session_data = {
            "workspace_id": test_workspace.id,
            "user_label": "Test Customer"
        }
        
        session_response = client.post(
            "/api/v1/chat/sessions",
            json=session_data,
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        session_id = session_response.json()["session_id"]
        
        # Send a RAG query
        rag_data = {
            "query": "What is your refund policy?",
            "session_id": session_id
        }
        
        response = client.post(
            "/api/v1/rag/query",
            json=rag_data,
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        assert response.status_code == 200
        rag_response = response.json()
        assert "answer" in rag_response
        assert "sources" in rag_response

class TestBillingWorkflow:
    """Test complete billing workflow"""
    
    def test_billing_status_and_quota(self, client, auth_token):
        """Test billing status and quota checking"""
        # Get billing status
        response = client.get(
            "/api/v1/billing/status",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        assert response.status_code == 200
        billing_data = response.json()
        assert "tier" in billing_data
        assert "status" in billing_data
        assert "quota_used" in billing_data
        assert "quota_limit" in billing_data
    
    def test_quota_enforcement(self, client, auth_token, test_workspace):
        """Test that quota is enforced correctly"""
        # This would require setting up a user with limited quota
        # and testing that requests are blocked when quota is exceeded
        pass

class TestAnalyticsWorkflow:
    """Test analytics data collection and retrieval"""
    
    def test_analytics_data_collection(self, client, auth_token, test_workspace):
        """Test that analytics data is collected during usage"""
        # Create some activity
        session_data = {
            "workspace_id": test_workspace.id,
            "user_label": "Test Customer"
        }
        
        response = client.post(
            "/api/v1/chat/sessions",
            json=session_data,
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        assert response.status_code == 201
        
        # Get analytics
        analytics_response = client.get(
            "/api/v1/analytics/workspace",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        assert analytics_response.status_code == 200
        analytics_data = analytics_response.json()
        assert "total_queries" in analytics_data
        assert "total_documents" in analytics_data

class TestErrorHandling:
    """Test error handling across the API"""
    
    def test_authentication_required(self, client):
        """Test that authentication is required for protected endpoints"""
        response = client.get("/api/v1/documents/")
        assert response.status_code == 401
    
    def test_invalid_token_rejected(self, client):
        """Test that invalid tokens are rejected"""
        response = client.get(
            "/api/v1/documents/",
            headers={"Authorization": "Bearer invalid_token"}
        )
        assert response.status_code == 401
    
    def test_workspace_access_control(self, client, auth_token):
        """Test that users can only access their own workspace data"""
        # Try to access another workspace's data
        response = client.get(
            "/api/v1/documents/",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        # Should only return documents from user's workspace
        assert response.status_code == 200
        documents = response.json()
        # All documents should belong to the user's workspace
        for doc in documents:
            assert doc["workspace_id"] == "test-workspace-id"
    
    def test_file_upload_validation(self, client, auth_token, test_workspace):
        """Test file upload validation"""
        # Try to upload invalid file type
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
    
    def test_rate_limiting(self, client, auth_token):
        """Test rate limiting functionality"""
        # Make many requests quickly
        for _ in range(100):
            response = client.get(
                "/api/v1/documents/",
                headers={"Authorization": f"Bearer {auth_token}"}
            )
            if response.status_code == 429:
                break
        
        # Should eventually hit rate limit
        assert response.status_code == 429

class TestDatabaseTransactions:
    """Test database transaction handling"""
    
    def test_document_upload_creates_database_records(self, client, auth_token, test_workspace, db_session):
        """Test that document upload creates proper database records"""
        files = {"file": ("test.txt", b"content", "text/plain")}
        data = {"workspace_id": test_workspace.id}
        
        response = client.post(
            "/api/v1/documents/upload",
            files=files,
            data=data,
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        assert response.status_code == 201
        document_id = response.json()["document_id"]
        
        # Check database record
        document = db_session.query(Document).filter(Document.id == document_id).first()
        assert document is not None
        assert document.filename == "test.txt"
        assert document.workspace_id == test_workspace.id
    
    def test_chat_message_creates_database_records(self, client, auth_token, test_workspace, db_session):
        """Test that chat messages create proper database records"""
        # Create session
        session_data = {
            "workspace_id": test_workspace.id,
            "user_label": "Test Customer"
        }
        
        response = client.post(
            "/api/v1/chat/sessions",
            json=session_data,
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        session_id = response.json()["session_id"]
        
        # Send message
        message_data = {
            "content": "Hello",
            "session_id": session_id
        }
        
        response = client.post(
            "/api/v1/chat/message",
            json=message_data,
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        assert response.status_code == 200
        
        # Check database records
        session = db_session.query(ChatSession).filter(ChatSession.id == session_id).first()
        assert session is not None
        
        messages = db_session.query(ChatMessage).filter(ChatMessage.session_id == session_id).all()
        assert len(messages) >= 1

class TestConcurrentOperations:
    """Test concurrent operations and race conditions"""
    
    def test_concurrent_document_uploads(self, client, auth_token, test_workspace):
        """Test handling multiple concurrent document uploads"""
        import threading
        import time
        
        results = []
        
        def upload_document(index):
            files = {"file": (f"test{index}.txt", f"content {index}".encode(), "text/plain")}
            data = {"workspace_id": test_workspace.id}
            
            response = client.post(
                "/api/v1/documents/upload",
                files=files,
                data=data,
                headers={"Authorization": f"Bearer {auth_token}"}
            )
            results.append(response.status_code)
        
        # Start multiple uploads concurrently
        threads = []
        for i in range(5):
            thread = threading.Thread(target=upload_document, args=(i,))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # All uploads should succeed
        assert all(status == 201 for status in results)
    
    def test_concurrent_chat_sessions(self, client, auth_token, test_workspace):
        """Test handling multiple concurrent chat sessions"""
        import threading
        
        results = []
        
        def create_session(index):
            session_data = {
                "workspace_id": test_workspace.id,
                "user_label": f"Customer {index}"
            }
            
            response = client.post(
                "/api/v1/chat/sessions",
                json=session_data,
                headers={"Authorization": f"Bearer {auth_token}"}
            )
            results.append(response.status_code)
        
        # Start multiple session creations concurrently
        threads = []
        for i in range(10):
            thread = threading.Thread(target=create_session, args=(i,))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # All sessions should be created successfully
        assert all(status == 201 for status in results)

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
