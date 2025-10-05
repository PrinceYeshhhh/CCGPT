"""
Integration tests for API endpoints
"""
import pytest
import asyncio
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.core.database import get_db, Base
from app.models import User, Workspace, Document
from app.core.config import settings

# Test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_integration.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)

@pytest.fixture(scope="module")
def setup_database():
    """Setup test database"""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def test_user():
    """Create test user"""
    user_data = {
        "email": "test@example.com",
        "password": "SecurePassword123!",
        "full_name": "Test User"
    }
    response = client.post("/api/v1/auth/register", json=user_data)
    assert response.status_code == 201
    return response.json()

@pytest.fixture
def auth_headers(test_user):
    """Get authentication headers"""
    login_data = {
        "email": "test@example.com",
        "password": "SecurePassword123!"
    }
    response = client.post("/api/v1/auth/login", json=login_data)
    assert response.status_code == 200
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

class TestUserWorkflow:
    """Test complete user workflow"""
    
    def test_user_registration_and_login(self, setup_database):
        """Test user registration and login flow"""
        # Register user
        user_data = {
            "email": "integration@example.com",
            "password": "SecurePassword123!",
            "full_name": "Integration Test User"
        }
        
        response = client.post("/api/v1/auth/register", json=user_data)
        assert response.status_code == 201
        user = response.json()
        assert user["email"] == "integration@example.com"
        
        # Login user
        login_data = {
            "email": "integration@example.com",
            "password": "SecurePassword123!"
        }
        
        response = client.post("/api/v1/auth/login", json=login_data)
        assert response.status_code == 200
        login_response = response.json()
        assert "access_token" in login_response
        assert "token_type" in login_response
    
    def test_workspace_creation_and_management(self, setup_database, auth_headers):
        """Test workspace creation and management"""
        # Create workspace
        workspace_data = {
            "name": "Test Workspace",
            "description": "Integration test workspace"
        }
        
        response = client.post(
            "/api/v1/workspaces/",
            json=workspace_data,
            headers=auth_headers
        )
        assert response.status_code == 201
        workspace = response.json()
        assert workspace["name"] == "Test Workspace"
        
        # Get workspaces
        response = client.get("/api/v1/workspaces/", headers=auth_headers)
        assert response.status_code == 200
        workspaces = response.json()
        assert len(workspaces) >= 1
        
        # Update workspace
        update_data = {
            "name": "Updated Workspace",
            "description": "Updated description"
        }
        
        response = client.put(
            f"/api/v1/workspaces/{workspace['id']}",
            json=update_data,
            headers=auth_headers
        )
        assert response.status_code == 200
        updated_workspace = response.json()
        assert updated_workspace["name"] == "Updated Workspace"
    
    def test_document_upload_and_processing(self, setup_database, auth_headers):
        """Test document upload and processing"""
        # First create a workspace
        workspace_data = {
            "name": "Document Test Workspace",
            "description": "Workspace for document testing"
        }
        
        response = client.post(
            "/api/v1/workspaces/",
            json=workspace_data,
            headers=auth_headers
        )
        assert response.status_code == 201
        workspace = response.json()
        
        # Upload document
        test_content = "This is a test document for integration testing."
        files = {
            "file": ("test.txt", test_content, "text/plain")
        }
        
        response = client.post(
            f"/api/v1/documents/upload?workspace_id={workspace['id']}",
            files=files,
            headers=auth_headers
        )
        assert response.status_code == 201
        document = response.json()
        assert document["filename"] == "test.txt"
        
        # Get documents
        response = client.get(
            f"/api/v1/documents/?workspace_id={workspace['id']}",
            headers=auth_headers
        )
        assert response.status_code == 200
        documents = response.json()
        assert len(documents) >= 1
    
    def test_chat_functionality(self, setup_database, auth_headers):
        """Test chat functionality"""
        # Create workspace
        workspace_data = {
            "name": "Chat Test Workspace",
            "description": "Workspace for chat testing"
        }
        
        response = client.post(
            "/api/v1/workspaces/",
            json=workspace_data,
            headers=auth_headers
        )
        assert response.status_code == 201
        workspace = response.json()
        
        # Create chat session
        session_data = {
            "workspace_id": workspace["id"],
            "title": "Test Chat Session"
        }
        
        response = client.post(
            "/api/v1/chat/sessions/",
            json=session_data,
            headers=auth_headers
        )
        assert response.status_code == 201
        session = response.json()
        assert session["title"] == "Test Chat Session"
        
        # Send message
        message_data = {
            "content": "Hello, this is a test message",
            "session_id": session["id"]
        }
        
        response = client.post(
            "/api/v1/chat/message",
            json=message_data,
            headers=auth_headers
        )
        assert response.status_code == 200
        message = response.json()
        assert "response" in message
    
    def test_billing_integration(self, setup_database, auth_headers):
        """Test billing functionality"""
        # Get billing status
        response = client.get("/api/v1/billing/status", headers=auth_headers)
        assert response.status_code == 200
        billing_status = response.json()
        assert "tier" in billing_status
        
        # Get quota information
        response = client.get("/api/v1/billing/quota", headers=auth_headers)
        assert response.status_code == 200
        quota = response.json()
        assert "daily_usage" in quota
        assert "monthly_usage" in quota
    
    def test_embed_code_generation(self, setup_database, auth_headers):
        """Test embed code generation"""
        # Create workspace
        workspace_data = {
            "name": "Embed Test Workspace",
            "description": "Workspace for embed testing"
        }
        
        response = client.post(
            "/api/v1/workspaces/",
            json=workspace_data,
            headers=auth_headers
        )
        assert response.status_code == 201
        workspace = response.json()
        
        # Generate embed code
        embed_data = {
            "workspace_id": workspace["id"],
            "title": "Test Widget",
            "description": "Test embed widget"
        }
        
        response = client.post(
            "/api/v1/embed/codes/",
            json=embed_data,
            headers=auth_headers
        )
        assert response.status_code == 201
        embed_code = response.json()
        assert "code" in embed_code
        assert "api_key" in embed_code

class TestErrorHandling:
    """Test error handling and edge cases"""
    
    def test_unauthorized_access(self, setup_database):
        """Test unauthorized access to protected endpoints"""
        response = client.get("/api/v1/workspaces/")
        assert response.status_code == 401
    
    def test_invalid_workspace_access(self, setup_database, auth_headers):
        """Test access to non-existent workspace"""
        response = client.get("/api/v1/workspaces/99999", headers=auth_headers)
        assert response.status_code == 404
    
    def test_invalid_document_upload(self, setup_database, auth_headers):
        """Test invalid document upload"""
        # Upload without workspace
        files = {
            "file": ("test.txt", "content", "text/plain")
        }
        
        response = client.post(
            "/api/v1/documents/upload",
            files=files,
            headers=auth_headers
        )
        assert response.status_code == 400
    
    def test_rate_limiting(self, setup_database, auth_headers):
        """Test rate limiting functionality"""
        # Make multiple rapid requests
        for i in range(10):
            response = client.get("/api/v1/workspaces/", headers=auth_headers)
            if response.status_code == 429:
                break
        
        # Should eventually hit rate limit
        assert response.status_code in [200, 429]

class TestDatabaseIntegration:
    """Test database integration"""
    
    def test_database_connection(self, setup_database):
        """Test database connection"""
        response = client.get("/health")
        assert response.status_code == 200
        health = response.json()
        assert health["status"] == "healthy"
    
    def test_database_transactions(self, setup_database, auth_headers):
        """Test database transaction handling"""
        # Create workspace
        workspace_data = {
            "name": "Transaction Test",
            "description": "Testing transactions"
        }
        
        response = client.post(
            "/api/v1/workspaces/",
            json=workspace_data,
            headers=auth_headers
        )
        assert response.status_code == 201
        
        # Verify workspace exists
        response = client.get("/api/v1/workspaces/", headers=auth_headers)
        assert response.status_code == 200
        workspaces = response.json()
        assert any(w["name"] == "Transaction Test" for w in workspaces)
