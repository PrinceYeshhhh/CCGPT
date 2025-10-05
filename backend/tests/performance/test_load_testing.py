"""
Comprehensive load testing for CustomerCareGPT
Tests system performance under various load conditions
"""

import pytest
import asyncio
import time
import statistics
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.core.database import get_db, Base
from app.models import User, Workspace, Document, ChatSession, ChatMessage, Subscription
from app.services.auth import AuthService

# Test database configuration
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_load.db"

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
        hashed_password="$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj4J/HS.s.2",
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

class TestConcurrentUserLoad:
    """Test system performance under concurrent user load"""
    
    def test_concurrent_user_registration(self, client):
        """Test concurrent user registration performance"""
        def register_user(user_id):
            user_data = {
                "email": f"user{user_id}@example.com",
                "password": "SecurePassword123!",
                "full_name": f"User {user_id}",
                "workspace_name": f"Workspace {user_id}"
            }
            
            start_time = time.time()
            response = client.post("/api/v1/auth/register", json=user_data)
            end_time = time.time()
            
            return {
                "status_code": response.status_code,
                "response_time": end_time - start_time,
                "user_id": user_id
            }
        
        # Test with 50 concurrent users
        with ThreadPoolExecutor(max_workers=50) as executor:
            futures = [executor.submit(register_user, i) for i in range(50)]
            results = [future.result() for future in as_completed(futures)]
        
        # Analyze results
        successful_registrations = [r for r in results if r["status_code"] == 201]
        response_times = [r["response_time"] for r in successful_registrations]
        
        assert len(successful_registrations) >= 45  # At least 90% success rate
        assert statistics.mean(response_times) < 2.0  # Average response time < 2 seconds
        assert max(response_times) < 5.0  # Max response time < 5 seconds
    
    def test_concurrent_document_uploads(self, client, auth_token, test_workspace):
        """Test concurrent document upload performance"""
        def upload_document(doc_id):
            files = {"file": (f"test{doc_id}.txt", f"Content for document {doc_id}".encode(), "text/plain")}
            data = {"workspace_id": test_workspace.id}
            
            start_time = time.time()
            response = client.post(
                "/api/v1/documents/upload",
                files=files,
                data=data,
                headers={"Authorization": f"Bearer {auth_token}"}
            )
            end_time = time.time()
            
            return {
                "status_code": response.status_code,
                "response_time": end_time - start_time,
                "doc_id": doc_id
            }
        
        # Test with 100 concurrent uploads
        with ThreadPoolExecutor(max_workers=100) as executor:
            futures = [executor.submit(upload_document, i) for i in range(100)]
            results = [future.result() for future in as_completed(futures)]
        
        # Analyze results
        successful_uploads = [r for r in results if r["status_code"] == 201]
        response_times = [r["response_time"] for r in successful_uploads]
        
        assert len(successful_uploads) >= 90  # At least 90% success rate
        assert statistics.mean(response_times) < 3.0  # Average response time < 3 seconds
        assert max(response_times) < 10.0  # Max response time < 10 seconds
    
    def test_concurrent_chat_sessions(self, client, auth_token, test_workspace):
        """Test concurrent chat session creation performance"""
        def create_chat_session(session_id):
            session_data = {
                "workspace_id": test_workspace.id,
                "user_label": f"Customer {session_id}"
            }
            
            start_time = time.time()
            response = client.post(
                "/api/v1/chat/sessions",
                json=session_data,
                headers={"Authorization": f"Bearer {auth_token}"}
            )
            end_time = time.time()
            
            return {
                "status_code": response.status_code,
                "response_time": end_time - start_time,
                "session_id": session_id
            }
        
        # Test with 200 concurrent sessions
        with ThreadPoolExecutor(max_workers=200) as executor:
            futures = [executor.submit(create_chat_session, i) for i in range(200)]
            results = [future.result() for future in as_completed(futures)]
        
        # Analyze results
        successful_sessions = [r for r in results if r["status_code"] == 201]
        response_times = [r["response_time"] for r in successful_sessions]
        
        assert len(successful_sessions) >= 180  # At least 90% success rate
        assert statistics.mean(response_times) < 1.0  # Average response time < 1 second
        assert max(response_times) < 3.0  # Max response time < 3 seconds

class TestDatabasePerformance:
    """Test database performance under load"""
    
    def test_database_query_performance(self, client, auth_token, test_workspace, db_session):
        """Test database query performance with large datasets"""
        # Create many documents
        documents = []
        for i in range(1000):
            doc = Document(
                filename=f"document_{i}.txt",
                file_path=f"/tmp/document_{i}.txt",
                file_size=1024,
                file_type="text/plain",
                status="processed",
                user_id="test-user-id",
                workspace_id=test_workspace.id
            )
            documents.append(doc)
        
        db_session.add_all(documents)
        db_session.commit()
        
        # Test query performance
        start_time = time.time()
        response = client.get(
            "/api/v1/documents/",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        end_time = time.time()
        
        query_time = end_time - start_time
        
        assert response.status_code == 200
        assert query_time < 2.0  # Query should complete in < 2 seconds
        assert len(response.json()) == 1000
    
    def test_database_write_performance(self, client, auth_token, test_workspace, db_session):
        """Test database write performance"""
        def create_document(doc_id):
            doc = Document(
                filename=f"perf_doc_{doc_id}.txt",
                file_path=f"/tmp/perf_doc_{doc_id}.txt",
                file_size=1024,
                file_type="text/plain",
                status="processing",
                user_id="test-user-id",
                workspace_id=test_workspace.id
            )
            
            start_time = time.time()
            db_session.add(doc)
            db_session.commit()
            end_time = time.time()
            
            return end_time - start_time
        
        # Test with 500 concurrent writes
        with ThreadPoolExecutor(max_workers=50) as executor:
            futures = [executor.submit(create_document, i) for i in range(500)]
            write_times = [future.result() for future in as_completed(futures)]
        
        # Analyze results
        assert statistics.mean(write_times) < 0.1  # Average write time < 100ms
        assert max(write_times) < 0.5  # Max write time < 500ms

class TestMemoryUsage:
    """Test memory usage under load"""
    
    def test_memory_usage_during_heavy_load(self, client, auth_token, test_workspace):
        """Test memory usage during heavy load"""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        def heavy_operation(operation_id):
            # Simulate heavy operation
            files = {"file": (f"heavy_{operation_id}.txt", b"x" * 10000, "text/plain")}
            data = {"workspace_id": test_workspace.id}
            
            response = client.post(
                "/api/v1/documents/upload",
                files=files,
                data=data,
                headers={"Authorization": f"Bearer {auth_token}"}
            )
            return response.status_code
        
        # Run heavy operations
        with ThreadPoolExecutor(max_workers=100) as executor:
            futures = [executor.submit(heavy_operation, i) for i in range(1000)]
            results = [future.result() for future in as_completed(futures)]
        
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory
        
        # Memory increase should be reasonable (< 500MB)
        assert memory_increase < 500
        assert len([r for r in results if r == 201]) >= 900  # At least 90% success

class TestResponseTimeConsistency:
    """Test response time consistency under load"""
    
    def test_response_time_consistency(self, client, auth_token):
        """Test that response times remain consistent under load"""
        response_times = []
        
        def make_request():
            start_time = time.time()
            response = client.get(
                "/api/v1/documents/",
                headers={"Authorization": f"Bearer {auth_token}"}
            )
            end_time = time.time()
            return end_time - start_time
        
        # Make 1000 requests
        with ThreadPoolExecutor(max_workers=50) as executor:
            futures = [executor.submit(make_request) for _ in range(1000)]
            response_times = [future.result() for future in as_completed(futures)]
        
        # Analyze consistency
        mean_time = statistics.mean(response_times)
        std_dev = statistics.stdev(response_times)
        coefficient_of_variation = std_dev / mean_time
        
        # Response times should be consistent (low coefficient of variation)
        assert coefficient_of_variation < 0.5  # CV < 50%
        assert mean_time < 1.0  # Average < 1 second
        assert max(response_times) < 5.0  # Max < 5 seconds

class TestStressTesting:
    """Test system behavior under extreme stress"""
    
    def test_extreme_concurrent_load(self, client, auth_token, test_workspace):
        """Test system behavior under extreme concurrent load"""
        def stress_operation(operation_id):
            try:
                # Mix of different operations
                if operation_id % 3 == 0:
                    # Document upload
                    files = {"file": (f"stress_{operation_id}.txt", b"stress content", "text/plain")}
                    data = {"workspace_id": test_workspace.id}
                    response = client.post(
                        "/api/v1/documents/upload",
                        files=files,
                        data=data,
                        headers={"Authorization": f"Bearer {auth_token}"}
                    )
                elif operation_id % 3 == 1:
                    # Chat session creation
                    session_data = {
                        "workspace_id": test_workspace.id,
                        "user_label": f"Stress Customer {operation_id}"
                    }
                    response = client.post(
                        "/api/v1/chat/sessions",
                        json=session_data,
                        headers={"Authorization": f"Bearer {auth_token}"}
                    )
                else:
                    # Document listing
                    response = client.get(
                        "/api/v1/documents/",
                        headers={"Authorization": f"Bearer {auth_token}"}
                    )
                
                return response.status_code
            except Exception as e:
                return f"Error: {str(e)}"
        
        # Run 2000 concurrent operations
        with ThreadPoolExecutor(max_workers=200) as executor:
            futures = [executor.submit(stress_operation, i) for i in range(2000)]
            results = [future.result() for future in as_completed(futures)]
        
        # Analyze results
        successful_operations = [r for r in results if isinstance(r, int) and r in [200, 201]]
        error_operations = [r for r in results if isinstance(r, str) and r.startswith("Error")]
        
        # Should handle most operations successfully
        success_rate = len(successful_operations) / len(results)
        assert success_rate >= 0.8  # At least 80% success rate
        
        # Error rate should be reasonable
        error_rate = len(error_operations) / len(results)
        assert error_rate < 0.2  # Less than 20% error rate
    
    def test_memory_leak_detection(self, client, auth_token, test_workspace):
        """Test for memory leaks during extended operation"""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        def memory_intensive_operation(cycle):
            # Perform memory-intensive operations
            for i in range(100):
                files = {"file": (f"leak_test_{cycle}_{i}.txt", b"x" * 1000, "text/plain")}
                data = {"workspace_id": test_workspace.id}
                
                response = client.post(
                    "/api/v1/documents/upload",
                    files=files,
                    data=data,
                    headers={"Authorization": f"Bearer {auth_token}"}
                )
                
                # Clean up
                if response.status_code == 201:
                    doc_id = response.json()["document_id"]
                    client.delete(
                        f"/api/v1/documents/{doc_id}",
                        headers={"Authorization": f"Bearer {auth_token}"}
                    )
        
        # Run multiple cycles
        for cycle in range(10):
            memory_intensive_operation(cycle)
            
            # Check memory usage
            current_memory = process.memory_info().rss / 1024 / 1024  # MB
            memory_increase = current_memory - initial_memory
            
            # Memory increase should not grow unbounded
            assert memory_increase < 1000  # Less than 1GB increase

class TestScalabilityLimits:
    """Test system scalability limits"""
    
    def test_max_concurrent_connections(self, client, auth_token):
        """Test maximum concurrent connections the system can handle"""
        def connection_test(connection_id):
            try:
                response = client.get(
                    "/api/v1/documents/",
                    headers={"Authorization": f"Bearer {auth_token}"}
                )
                return response.status_code
            except Exception as e:
                return f"Connection error: {str(e)}"
        
        # Gradually increase concurrent connections
        max_connections = 0
        for num_connections in range(10, 1000, 50):
            with ThreadPoolExecutor(max_workers=num_connections) as executor:
                futures = [executor.submit(connection_test, i) for i in range(num_connections)]
                results = [future.result() for future in as_completed(futures)]
            
            successful_connections = [r for r in results if r == 200]
            success_rate = len(successful_connections) / len(results)
            
            if success_rate >= 0.9:  # 90% success rate
                max_connections = num_connections
            else:
                break
        
        # Should handle at least 500 concurrent connections
        assert max_connections >= 500
    
    def test_throughput_limits(self, client, auth_token, test_workspace):
        """Test maximum throughput the system can handle"""
        def throughput_test(operation_id):
            files = {"file": (f"throughput_{operation_id}.txt", b"throughput test", "text/plain")}
            data = {"workspace_id": test_workspace.id}
            
            start_time = time.time()
            response = client.post(
                "/api/v1/documents/upload",
                files=files,
                data=data,
                headers={"Authorization": f"Bearer {auth_token}"}
            )
            end_time = time.time()
            
            return {
                "status_code": response.status_code,
                "response_time": end_time - start_time
            }
        
        # Test throughput with increasing load
        max_throughput = 0
        for num_operations in range(100, 2000, 100):
            start_time = time.time()
            
            with ThreadPoolExecutor(max_workers=100) as executor:
                futures = [executor.submit(throughput_test, i) for i in range(num_operations)]
                results = [future.result() for future in as_completed(futures)]
            
            end_time = time.time()
            total_time = end_time - start_time
            throughput = num_operations / total_time  # operations per second
            
            successful_operations = [r for r in results if r["status_code"] == 201]
            success_rate = len(successful_operations) / len(results)
            
            if success_rate >= 0.9:  # 90% success rate
                max_throughput = throughput
            else:
                break
        
        # Should handle at least 50 operations per second
        assert max_throughput >= 50

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
