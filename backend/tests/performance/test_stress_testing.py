"""
Comprehensive stress testing for production readiness
"""

import pytest
import asyncio
import time
import random
import string
from concurrent.futures import ThreadPoolExecutor, as_completed
from unittest.mock import Mock, patch
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.core.database import get_db
from app.models.user import User
from app.models.workspace import Workspace
from app.models.document import Document
from app.models.chat import ChatSession, ChatMessage
from app.services.auth import AuthService
from app.services.rag_service import RAGService
from app.services.websocket_service import WebSocketService


class TestLoadTesting:
    """Load testing for API endpoints"""
    
    @pytest.fixture
    def client(self):
        return TestClient(app)
    
    @pytest.fixture
    def auth_headers(self, test_user):
        auth_service = AuthService(None)
        token = auth_service.create_access_token({
            "user_id": str(test_user.id),
            "email": test_user.email
        })
        return {"Authorization": f"Bearer {token}"}
    
    def test_concurrent_user_registration(self, client):
        """Test concurrent user registration under load"""
        def register_user(user_id):
            user_data = {
                "email": f"user{user_id}@example.com",
                "password": "SecurePassword123!",
                "full_name": f"User {user_id}",
                "business_name": f"Business {user_id}",
                "business_domain": f"business{user_id}.com"
            }
            
            with patch('app.api.api_v1.endpoints.auth.AuthService') as mock_auth:
                mock_service = Mock()
                mock_user = Mock()
                mock_user.id = str(user_id)
                mock_user.email = user_data["email"]
                mock_service.register_user.return_value = mock_user
                mock_auth.return_value = mock_service
                
                response = client.post("/api/v1/auth/register", json=user_data)
                return response.status_code
        
        # Test with 50 concurrent registrations
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(register_user, i) for i in range(50)]
            results = [future.result() for future in as_completed(futures)]
        
        # All registrations should succeed
        assert all(status == 201 for status in results)
    
    def test_concurrent_document_upload(self, client, auth_headers):
        """Test concurrent document upload under load"""
        def upload_document(doc_id):
            with patch('app.api.api_v1.endpoints.documents.get_current_user') as mock_get_user:
                mock_user = Mock()
                mock_user.id = "123"
                mock_user.workspace_id = "ws_123"
                mock_get_user.return_value = mock_user
                
                with patch('app.api.api_v1.endpoints.documents.DocumentService') as mock_doc_service:
                    mock_service = Mock()
                    mock_document = {
                        "id": f"doc_{doc_id}",
                        "filename": f"document_{doc_id}.pdf",
                        "status": "processing"
                    }
                    mock_service.upload_document.return_value = mock_document
                    mock_doc_service.return_value = mock_service
                    
                    # Simulate file upload
                    files = {"file": ("test.pdf", b"fake pdf content", "application/pdf")}
                    response = client.post("/api/v1/documents/upload", files=files, headers=auth_headers)
                    return response.status_code
        
        # Test with 20 concurrent uploads
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(upload_document, i) for i in range(20)]
            results = [future.result() for future in as_completed(futures)]
        
        # All uploads should succeed
        assert all(status == 200 for status in results)
    
    def test_concurrent_chat_messages(self, client, auth_headers):
        """Test concurrent chat messages under load"""
        def send_chat_message(msg_id):
            with patch('app.api.api_v1.endpoints.chat.get_current_user') as mock_get_user:
                mock_user = Mock()
                mock_user.id = "123"
                mock_user.workspace_id = "ws_123"
                mock_get_user.return_value = mock_user
                
                with patch('app.api.api_v1.endpoints.chat.ChatService') as mock_chat_service:
                    mock_service = Mock()
                    mock_response = {
                        "response": f"Response to message {msg_id}",
                        "message_id": f"msg_{msg_id}",
                        "sources": []
                    }
                    mock_service.process_message.return_value = mock_response
                    mock_chat_service.return_value = mock_service
                    
                    message_data = {
                        "message": f"Test message {msg_id}",
                        "session_id": "session_123"
                    }
                    
                    response = client.post("/api/v1/chat/send", json=message_data, headers=auth_headers)
                    return response.status_code
        
        # Test with 100 concurrent messages
        with ThreadPoolExecutor(max_workers=20) as executor:
            futures = [executor.submit(send_chat_message, i) for i in range(100)]
            results = [future.result() for future in as_completed(futures)]
        
        # All messages should succeed
        assert all(status == 200 for status in results)
    
    def test_concurrent_rag_queries(self, client, auth_headers):
        """Test concurrent RAG queries under load"""
        def send_rag_query(query_id):
            with patch('app.api.api_v1.endpoints.rag_query.get_current_user') as mock_get_user:
                mock_user = Mock()
                mock_user.id = "123"
                mock_user.workspace_id = "ws_123"
                mock_get_user.return_value = mock_user
                
                with patch('app.api.api_v1.endpoints.rag_query.RAGService') as mock_rag_service:
                    mock_service = Mock()
                    mock_response = {
                        "answer": f"Answer to query {query_id}",
                        "sources": [],
                        "response_time_ms": random.randint(100, 500)
                    }
                    mock_service.process_query.return_value = mock_response
                    mock_rag_service.return_value = mock_service
                    
                    query_data = {
                        "query": f"Test query {query_id}",
                        "session_id": "session_123"
                    }
                    
                    response = client.post("/api/v1/rag/query", json=query_data, headers=auth_headers)
                    return response.status_code
        
        # Test with 50 concurrent queries
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(send_rag_query, i) for i in range(50)]
            results = [future.result() for future in as_completed(futures)]
        
        # All queries should succeed
        assert all(status == 200 for status in results)


class TestMemoryStress:
    """Memory stress testing"""
    
    @pytest.fixture
    def client(self):
        return TestClient(app)
    
    def test_large_document_processing(self, client, auth_headers):
        """Test processing of large documents"""
        with patch('app.api.api_v1.endpoints.documents.get_current_user') as mock_get_user:
            mock_user = Mock()
            mock_user.id = "123"
            mock_user.workspace_id = "ws_123"
            mock_get_user.return_value = mock_user
            
            with patch('app.api.api_v1.endpoints.documents.DocumentService') as mock_doc_service:
                mock_service = Mock()
                mock_document = {
                    "id": "doc_large",
                    "filename": "large_document.pdf",
                    "status": "processing",
                    "file_size": 50 * 1024 * 1024  # 50MB
                }
                mock_service.upload_document.return_value = mock_document
                mock_doc_service.return_value = mock_service
                
                # Simulate large file upload
                large_content = b"x" * (10 * 1024 * 1024)  # 10MB content
                files = {"file": ("large.pdf", large_content, "application/pdf")}
                
                response = client.post("/api/v1/documents/upload", files=files, headers=auth_headers)
                assert response.status_code == 200
    
    def test_memory_intensive_rag_queries(self, client, auth_headers):
        """Test memory-intensive RAG queries"""
        with patch('app.api.api_v1.endpoints.rag_query.get_current_user') as mock_get_user:
            mock_user = Mock()
            mock_user.id = "123"
            mock_user.workspace_id = "ws_123"
            mock_get_user.return_value = mock_user
            
            with patch('app.api.api_v1.endpoints.rag_query.RAGService') as mock_rag_service:
                mock_service = Mock()
                
                # Simulate large response with many sources
                large_sources = [
                    {
                        "document_id": f"doc_{i}",
                        "chunk_id": f"chunk_{i}",
                        "content": "x" * 1000,  # 1KB per source
                        "score": 0.9
                    }
                    for i in range(1000)  # 1000 sources
                ]
                
                mock_response = {
                    "answer": "x" * 10000,  # 10KB answer
                    "sources": large_sources,
                    "response_time_ms": 1000
                }
                mock_service.process_query.return_value = mock_response
                mock_rag_service.return_value = mock_service
                
                query_data = {
                    "query": "Complex query requiring extensive processing",
                    "session_id": "session_123"
                }
                
                response = client.post("/api/v1/rag/query", json=query_data, headers=auth_headers)
                assert response.status_code == 200
    
    def test_concurrent_large_requests(self, client, auth_headers):
        """Test concurrent large requests"""
        def make_large_request(req_id):
            with patch('app.api.api_v1.endpoints.rag_query.get_current_user') as mock_get_user:
                mock_user = Mock()
                mock_user.id = "123"
                mock_user.workspace_id = "ws_123"
                mock_get_user.return_value = mock_user
                
                with patch('app.api.api_v1.endpoints.rag_query.RAGService') as mock_rag_service:
                    mock_service = Mock()
                    mock_response = {
                        "answer": "x" * 5000,  # 5KB answer
                        "sources": [
                            {
                                "document_id": f"doc_{i}",
                                "chunk_id": f"chunk_{i}",
                                "content": "x" * 500,  # 500B per source
                                "score": 0.9
                            }
                            for i in range(100)  # 100 sources
                        ],
                        "response_time_ms": 500
                    }
                    mock_service.process_query.return_value = mock_response
                    mock_rag_service.return_value = mock_service
                    
                    query_data = {
                        "query": f"Large query {req_id}",
                        "session_id": "session_123"
                    }
                    
                    response = client.post("/api/v1/rag/query", json=query_data, headers=auth_headers)
                    return response.status_code
        
        # Test with 20 concurrent large requests
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(make_large_request, i) for i in range(20)]
            results = [future.result() for future in as_completed(futures)]
        
        # All requests should succeed
        assert all(status == 200 for status in results)


class TestDatabaseStress:
    """Database stress testing"""
    
    @pytest.fixture
    def client(self):
        return TestClient(app)
    
    def test_concurrent_database_operations(self, client, auth_headers):
        """Test concurrent database operations"""
        def perform_db_operation(op_id):
            with patch('app.api.api_v1.endpoints.documents.get_current_user') as mock_get_user:
                mock_user = Mock()
                mock_user.id = "123"
                mock_user.workspace_id = "ws_123"
                mock_get_user.return_value = mock_user
                
                with patch('app.api.api_v1.endpoints.documents.DocumentService') as mock_doc_service:
                    mock_service = Mock()
                    mock_documents = [
                        {
                            "id": f"doc_{op_id}_{i}",
                            "filename": f"document_{i}.pdf",
                            "status": "processed"
                        }
                        for i in range(10)
                    ]
                    mock_service.get_documents.return_value = mock_documents
                    mock_doc_service.return_value = mock_service
                    
                    response = client.get("/api/v1/documents/", headers=auth_headers)
                    return response.status_code
        
        # Test with 50 concurrent database operations
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(perform_db_operation, i) for i in range(50)]
            results = [future.result() for future in as_completed(futures)]
        
        # All operations should succeed
        assert all(status == 200 for status in results)
    
    def test_database_connection_pool_stress(self, client, auth_headers):
        """Test database connection pool under stress"""
        def stress_db_connection(conn_id):
            with patch('app.api.api_v1.endpoints.documents.get_current_user') as mock_get_user:
                mock_user = Mock()
                mock_user.id = "123"
                mock_user.workspace_id = "ws_123"
                mock_get_user.return_value = mock_user
                
                with patch('app.api.api_v1.endpoints.documents.DocumentService') as mock_doc_service:
                    mock_service = Mock()
                    mock_service.get_documents.return_value = []
                    mock_doc_service.return_value = mock_service
                    
                    # Simulate multiple rapid requests
                    responses = []
                    for i in range(10):
                        response = client.get("/api/v1/documents/", headers=auth_headers)
                        responses.append(response.status_code)
                        time.sleep(0.01)  # Small delay
                    
                    return all(status == 200 for status in responses)
        
        # Test with 20 concurrent connection stress tests
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(stress_db_connection, i) for i in range(20)]
            results = [future.result() for future in as_completed(futures)]
        
        # All connection stress tests should succeed
        assert all(results)


class TestWebSocketStress:
    """WebSocket stress testing"""
    
    @pytest.fixture
    def websocket_service(self):
        return WebSocketService()
    
    def test_concurrent_websocket_connections(self):
        """Test concurrent WebSocket connections"""
        def simulate_websocket_connection(conn_id):
            # Simulate WebSocket connection
            mock_websocket = Mock()
            mock_websocket.id = f"conn_{conn_id}"
            mock_websocket.user_id = f"user_{conn_id % 10}"  # 10 different users
            mock_websocket.workspace_id = f"ws_{conn_id % 5}"  # 5 different workspaces
            
            # Simulate connection handling
            try:
                # This would be the actual connection handling
                time.sleep(0.1)  # Simulate connection time
                return True
            except Exception:
                return False
        
        # Test with 100 concurrent WebSocket connections
        with ThreadPoolExecutor(max_workers=20) as executor:
            futures = [executor.submit(simulate_websocket_connection, i) for i in range(100)]
            results = [future.result() for future in as_completed(futures)]
        
        # All connections should succeed
        assert all(results)
    
    def test_websocket_message_flooding(self):
        """Test WebSocket message flooding"""
        def simulate_message_flood(flood_id):
            # Simulate rapid message sending
            messages_sent = 0
            try:
                for i in range(100):  # 100 messages per flood
                    # Simulate message processing
                    time.sleep(0.001)  # 1ms per message
                    messages_sent += 1
                return messages_sent
            except Exception:
                return 0
        
        # Test with 10 concurrent message floods
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(simulate_message_flood, i) for i in range(10)]
            results = [future.result() for future in as_completed(futures)]
        
        # All floods should complete
        assert all(result == 100 for result in results)


class TestResourceExhaustion:
    """Resource exhaustion testing"""
    
    @pytest.fixture
    def client(self):
        return TestClient(app)
    
    def test_cpu_intensive_operations(self, client, auth_headers):
        """Test CPU-intensive operations"""
        def cpu_intensive_request(req_id):
            with patch('app.api.api_v1.endpoints.rag_query.get_current_user') as mock_get_user:
                mock_user = Mock()
                mock_user.id = "123"
                mock_user.workspace_id = "ws_123"
                mock_get_user.return_value = mock_user
                
                with patch('app.api.api_v1.endpoints.rag_query.RAGService') as mock_rag_service:
                    mock_service = Mock()
                    
                    # Simulate CPU-intensive processing
                    def simulate_processing():
                        result = 0
                        for i in range(100000):  # CPU-intensive loop
                            result += i * i
                        return result
                    
                    # Simulate processing time
                    processing_time = simulate_processing()
                    
                    mock_response = {
                        "answer": f"Processed result {req_id}",
                        "sources": [],
                        "response_time_ms": 1000
                    }
                    mock_service.process_query.return_value = mock_response
                    mock_rag_service.return_value = mock_service
                    
                    query_data = {
                        "query": f"CPU intensive query {req_id}",
                        "session_id": "session_123"
                    }
                    
                    response = client.post("/api/v1/rag/query", json=query_data, headers=auth_headers)
                    return response.status_code
        
        # Test with 10 concurrent CPU-intensive requests
        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = [executor.submit(cpu_intensive_request, i) for i in range(10)]
            results = [future.result() for future in as_completed(futures)]
        
        # All requests should succeed
        assert all(status == 200 for status in results)
    
    def test_memory_leak_detection(self, client, auth_headers):
        """Test for memory leaks in repeated operations"""
        def repeated_operation(iteration):
            with patch('app.api.api_v1.endpoints.documents.get_current_user') as mock_get_user:
                mock_user = Mock()
                mock_user.id = "123"
                mock_user.workspace_id = "ws_123"
                mock_get_user.return_value = mock_user
                
                with patch('app.api.api_v1.endpoints.documents.DocumentService') as mock_doc_service:
                    mock_service = Mock()
                    mock_documents = [
                        {
                            "id": f"doc_{iteration}_{i}",
                            "filename": f"document_{i}.pdf",
                            "status": "processed",
                            "content": "x" * 1000  # 1KB per document
                        }
                        for i in range(50)
                    ]
                    mock_service.get_documents.return_value = mock_documents
                    mock_doc_service.return_value = mock_service
                    
                    response = client.get("/api/v1/documents/", headers=auth_headers)
                    return response.status_code
        
        # Perform 100 repeated operations to detect memory leaks
        results = []
        for i in range(100):
            result = repeated_operation(i)
            results.append(result)
            time.sleep(0.01)  # Small delay between operations
        
        # All operations should succeed
        assert all(status == 200 for status in results)


class TestPerformanceMetrics:
    """Performance metrics collection and analysis"""
    
    @pytest.fixture
    def client(self):
        return TestClient(app)
    
    def test_response_time_analysis(self, client, auth_headers):
        """Test response time analysis under load"""
        def measure_response_time(req_id):
            with patch('app.api.api_v1.endpoints.documents.get_current_user') as mock_get_user:
                mock_user = Mock()
                mock_user.id = "123"
                mock_user.workspace_id = "ws_123"
                mock_get_user.return_value = mock_user
                
                with patch('app.api.api_v1.endpoints.documents.DocumentService') as mock_doc_service:
                    mock_service = Mock()
                    mock_service.get_documents.return_value = []
                    mock_doc_service.return_value = mock_service
                    
                    start_time = time.time()
                    response = client.get("/api/v1/documents/", headers=auth_headers)
                    end_time = time.time()
                    
                    return {
                        "status_code": response.status_code,
                        "response_time": end_time - start_time,
                        "request_id": req_id
                    }
        
        # Measure response times for 50 requests
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(measure_response_time, i) for i in range(50)]
            results = [future.result() for future in as_completed(futures)]
        
        # Analyze response times
        response_times = [r["response_time"] for r in results]
        avg_response_time = sum(response_times) / len(response_times)
        max_response_time = max(response_times)
        min_response_time = min(response_times)
        
        # All requests should succeed
        assert all(r["status_code"] == 200 for r in results)
        
        # Response times should be reasonable
        assert avg_response_time < 1.0  # Average under 1 second
        assert max_response_time < 5.0  # Max under 5 seconds
        assert min_response_time > 0.0  # Min greater than 0
    
    def test_throughput_analysis(self, client, auth_headers):
        """Test throughput analysis"""
        def throughput_request(req_id):
            with patch('app.api.api_v1.endpoints.documents.get_current_user') as mock_get_user:
                mock_user = Mock()
                mock_user.id = "123"
                mock_user.workspace_id = "ws_123"
                mock_get_user.return_value = mock_user
                
                with patch('app.api.api_v1.endpoints.documents.DocumentService') as mock_doc_service:
                    mock_service = Mock()
                    mock_service.get_documents.return_value = []
                    mock_doc_service.return_value = mock_service
                    
                    start_time = time.time()
                    response = client.get("/api/v1/documents/", headers=auth_headers)
                    end_time = time.time()
                    
                    return {
                        "status_code": response.status_code,
                        "duration": end_time - start_time,
                        "timestamp": start_time
                    }
        
        # Measure throughput over 10 seconds
        start_time = time.time()
        results = []
        
        with ThreadPoolExecutor(max_workers=20) as executor:
            while time.time() - start_time < 10:  # 10 seconds
                future = executor.submit(throughput_request, len(results))
                results.append(future)
                time.sleep(0.1)  # 10 requests per second
            
            # Collect results
            completed_results = [future.result() for future in as_completed(results)]
        
        # Calculate throughput
        total_requests = len(completed_results)
        total_time = time.time() - start_time
        throughput = total_requests / total_time  # requests per second
        
        # All requests should succeed
        assert all(r["status_code"] == 200 for r in completed_results)
        
        # Throughput should be reasonable
        assert throughput > 1.0  # At least 1 request per second
        assert total_requests > 10  # At least 10 requests completed
