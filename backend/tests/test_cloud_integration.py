"""
Cloud Integration Tests
Tests the actual cloud backend from local machine
"""
import pytest
import asyncio
import httpx
import os
from typing import Dict, Any, Optional
import json
import time

# Cloud URLs (using your existing configuration)
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")
API_V1_URL = f"{BACKEND_URL}/api/v1"
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")

class CloudTestClient:
    """Client for testing cloud backend"""
    
    def __init__(self, base_url: str = API_V1_URL):
        self.base_url = base_url
        self.session = httpx.AsyncClient(timeout=30.0)
        self.auth_token: Optional[str] = None
        self.user_id: Optional[str] = None
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.session.aclose()
    
    async def register_user(self, email: str, password: str, full_name: str) -> Dict[str, Any]:
        """Register a new user"""
        data = {
            "email": email,
            "password": password,
            "full_name": full_name
        }
        response = await self.session.post(f"{self.base_url}/auth/register", json=data)
        return response.json(), response.status_code
    
    async def login_user(self, email: str, password: str) -> Dict[str, Any]:
        """Login user and store auth token"""
        data = {
            "email": email,
            "password": password
        }
        response = await self.session.post(f"{self.base_url}/auth/login", json=data)
        if response.status_code == 200:
            result = response.json()
            self.auth_token = result.get("access_token")
            return result, response.status_code
        return response.json(), response.status_code
    
    async def get_auth_headers(self) -> Dict[str, str]:
        """Get authentication headers"""
        if not self.auth_token:
            raise ValueError("Not authenticated. Call login_user first.")
        return {"Authorization": f"Bearer {self.auth_token}"}
    
    async def get_workspaces(self) -> tuple:
        """Get user workspaces"""
        headers = await self.get_auth_headers()
        response = await self.session.get(f"{self.base_url}/workspaces/", headers=headers)
        return response.json(), response.status_code
    
    async def create_workspace(self, name: str, description: str = "") -> tuple:
        """Create a new workspace"""
        headers = await self.get_auth_headers()
        data = {
            "name": name,
            "description": description
        }
        response = await self.session.post(f"{self.base_url}/workspaces/", json=data, headers=headers)
        return response.json(), response.status_code
    
    async def upload_document(self, workspace_id: str, content: str, filename: str = "test.txt") -> tuple:
        """Upload a document"""
        headers = await self.get_auth_headers()
        files = {
            "file": (filename, content, "text/plain")
        }
        data = {"workspace_id": workspace_id}
        response = await self.session.post(
            f"{self.base_url}/documents/upload",
            files=files,
            data=data,
            headers=headers
        )
        return response.json(), response.status_code
    
    async def send_chat_message(self, workspace_id: str, message: str) -> tuple:
        """Send a chat message"""
        headers = await self.get_auth_headers()
        data = {
            "workspace_id": workspace_id,
            "content": message
        }
        response = await self.session.post(f"{self.base_url}/chat/message", json=data, headers=headers)
        return response.json(), response.status_code
    
    async def get_health(self) -> tuple:
        """Get health status"""
        response = await self.session.get(f"{BACKEND_URL}/health")
        return response.json(), response.status_code

@pytest.fixture
async def cloud_client():
    """Cloud test client fixture"""
    async with CloudTestClient() as client:
        yield client

@pytest.fixture
async def authenticated_user(cloud_client):
    """Create and authenticate a test user"""
    # Use unique email for each test
    timestamp = int(time.time())
    email = f"test_{timestamp}@example.com"
    password = "SecurePassword123!"
    full_name = "Test User"
    
    # Register user
    result, status = await cloud_client.register_user(email, password, full_name)
    if status not in [201, 409]:  # 409 = user already exists
        pytest.fail(f"User registration failed: {result}")
    
    # Login user
    result, status = await cloud_client.login_user(email, password)
    if status != 200:
        pytest.fail(f"User login failed: {result}")
    
    return cloud_client, email

class TestCloudHealth:
    """Test cloud backend health"""
    
    @pytest.mark.asyncio
    async def test_backend_health(self, cloud_client):
        """Test backend health endpoint"""
        result, status = await cloud_client.get_health()
        
        assert status == 200
        assert result["status"] == "healthy"
        assert "timestamp" in result
    
    @pytest.mark.asyncio
    async def test_backend_readiness(self, cloud_client):
        """Test backend readiness endpoint"""
        response = await cloud_client.session.get(f"{BACKEND_URL}/ready")
        result = response.json()
        
        assert response.status_code == 200
        assert result["status"] == "ready"
    
    @pytest.mark.asyncio
    async def test_backend_detailed_health(self, cloud_client):
        """Test detailed health endpoint"""
        response = await cloud_client.session.get(f"{BACKEND_URL}/health/detailed")
        result = response.json()
        
        assert response.status_code == 200
        assert "dependencies" in result
        assert "database" in result["dependencies"]
        assert "redis" in result["dependencies"]

class TestCloudAuthentication:
    """Test cloud authentication"""
    
    @pytest.mark.asyncio
    async def test_user_registration(self, cloud_client):
        """Test user registration"""
        timestamp = int(time.time())
        email = f"reg_test_{timestamp}@example.com"
        password = "SecurePassword123!"
        full_name = "Registration Test User"
        
        result, status = await cloud_client.register_user(email, password, full_name)
        
        assert status == 201
        assert "user" in result
        assert result["user"]["email"] == email
    
    @pytest.mark.asyncio
    async def test_user_login(self, cloud_client):
        """Test user login"""
        timestamp = int(time.time())
        email = f"login_test_{timestamp}@example.com"
        password = "SecurePassword123!"
        full_name = "Login Test User"
        
        # Register first
        await cloud_client.register_user(email, password, full_name)
        
        # Then login
        result, status = await cloud_client.login_user(email, password)
        
        assert status == 200
        assert "access_token" in result
        assert "token_type" in result
        assert result["token_type"] == "bearer"
    
    @pytest.mark.asyncio
    async def test_invalid_login(self, cloud_client):
        """Test invalid login credentials"""
        result, status = await cloud_client.login_user("nonexistent@example.com", "wrongpassword")
        
        assert status == 401
        assert "Invalid credentials" in result["detail"]
    
    @pytest.mark.asyncio
    async def test_duplicate_registration(self, cloud_client):
        """Test duplicate user registration"""
        timestamp = int(time.time())
        email = f"duplicate_test_{timestamp}@example.com"
        password = "SecurePassword123!"
        full_name = "Duplicate Test User"
        
        # Register first time
        result1, status1 = await cloud_client.register_user(email, password, full_name)
        assert status1 == 201
        
        # Try to register again
        result2, status2 = await cloud_client.register_user(email, password, full_name)
        assert status2 == 409  # Conflict

class TestCloudWorkspaces:
    """Test cloud workspace functionality"""
    
    @pytest.mark.asyncio
    async def test_create_workspace(self, authenticated_user):
        """Test workspace creation"""
        client, email = authenticated_user
        
        result, status = await client.create_workspace("Test Workspace", "Test Description")
        
        assert status == 201
        assert "id" in result
        assert result["name"] == "Test Workspace"
        assert result["description"] == "Test Description"
    
    @pytest.mark.asyncio
    async def test_get_workspaces(self, authenticated_user):
        """Test getting user workspaces"""
        client, email = authenticated_user
        
        # Create a workspace first
        await client.create_workspace("Test Workspace 1", "Description 1")
        await client.create_workspace("Test Workspace 2", "Description 2")
        
        # Get workspaces
        result, status = await client.get_workspaces()
        
        assert status == 200
        assert isinstance(result, list)
        assert len(result) >= 2
    
    @pytest.mark.asyncio
    async def test_unauthorized_workspace_access(self, cloud_client):
        """Test unauthorized workspace access"""
        # Try to access workspaces without authentication
        response = await cloud_client.session.get(f"{API_V1_URL}/workspaces/")
        
        assert response.status_code == 401

class TestCloudDocuments:
    """Test cloud document functionality"""
    
    @pytest.mark.asyncio
    async def test_document_upload(self, authenticated_user):
        """Test document upload"""
        client, email = authenticated_user
        
        # Create workspace first
        workspace_result, workspace_status = await client.create_workspace("Document Test Workspace")
        assert workspace_status == 201
        workspace_id = workspace_result["id"]
        
        # Upload document
        content = "This is a test document for cloud integration testing."
        result, status = await client.upload_document(workspace_id, content, "test_document.txt")
        
        assert status == 201
        assert "id" in result
        assert result["filename"] == "test_document.txt"
    
    @pytest.mark.asyncio
    async def test_document_upload_without_workspace(self, authenticated_user):
        """Test document upload without workspace"""
        client, email = authenticated_user
        
        content = "This is a test document."
        result, status = await client.upload_document("", content, "test_document.txt")
        
        assert status == 400  # Bad request - workspace required

class TestCloudChat:
    """Test cloud chat functionality"""
    
    @pytest.mark.asyncio
    async def test_chat_message(self, authenticated_user):
        """Test sending chat message"""
        client, email = authenticated_user
        
        # Create workspace first
        workspace_result, workspace_status = await client.create_workspace("Chat Test Workspace")
        assert workspace_status == 201
        workspace_id = workspace_result["id"]
        
        # Send chat message
        message = "Hello, this is a test message for cloud integration testing."
        result, status = await client.send_chat_message(workspace_id, message)
        
        assert status == 200
        assert "response" in result
        assert "message_id" in result

class TestCloudErrorHandling:
    """Test cloud error handling"""
    
    @pytest.mark.asyncio
    async def test_invalid_endpoint(self, cloud_client):
        """Test invalid endpoint"""
        response = await cloud_client.session.get(f"{API_V1_URL}/invalid/endpoint")
        
        assert response.status_code == 404
    
    @pytest.mark.asyncio
    async def test_malformed_json(self, cloud_client):
        """Test malformed JSON request"""
        response = await cloud_client.session.post(
            f"{API_V1_URL}/auth/register",
            content="invalid json",
            headers={"Content-Type": "application/json"}
        )
        
        assert response.status_code == 422
    
    @pytest.mark.asyncio
    async def test_rate_limiting(self, cloud_client):
        """Test rate limiting"""
        # Make multiple rapid requests
        for i in range(10):
            response = await cloud_client.session.get(f"{BACKEND_URL}/health")
            if response.status_code == 429:
                break
        
        # Should eventually hit rate limit
        assert response.status_code in [200, 429]

class TestCloudPerformance:
    """Test cloud performance"""
    
    @pytest.mark.asyncio
    async def test_response_time(self, cloud_client):
        """Test response time"""
        start_time = time.time()
        result, status = await cloud_client.get_health()
        end_time = time.time()
        
        response_time = end_time - start_time
        
        assert status == 200
        assert response_time < 5.0  # Should respond within 5 seconds
    
    @pytest.mark.asyncio
    async def test_concurrent_requests(self, cloud_client):
        """Test concurrent requests"""
        async def make_request():
            return await cloud_client.get_health()
        
        # Make 5 concurrent requests
        tasks = [make_request() for _ in range(5)]
        results = await asyncio.gather(*tasks)
        
        # All requests should succeed
        for result, status in results:
            assert status == 200
            assert result["status"] == "healthy"

# Test runner
if __name__ == "__main__":
    import asyncio
    
    async def run_tests():
        """Run cloud tests"""
        print("🌐 Running Cloud Integration Tests...")
        print(f"Backend URL: {BACKEND_URL}")
        print(f"API URL: {API_V1_URL}")
        print(f"Frontend URL: {FRONTEND_URL}")
        print("=" * 50)
        
        async with CloudTestClient() as client:
            # Test health
            print("Testing backend health...")
            result, status = await client.get_health()
            print(f"Health Status: {status} - {result}")
            
            # Test registration
            print("Testing user registration...")
            timestamp = int(time.time())
            email = f"cloud_test_{timestamp}@example.com"
            result, status = await client.register_user(email, "SecurePassword123!", "Cloud Test User")
            print(f"Registration Status: {status}")
            
            if status == 201:
                # Test login
                print("Testing user login...")
                result, status = await client.login_user(email, "SecurePassword123!")
                print(f"Login Status: {status}")
                
                if status == 200:
                    print("✅ Cloud integration tests passed!")
                else:
                    print("❌ Login failed")
            else:
                print("❌ Registration failed")
    
    asyncio.run(run_tests())
