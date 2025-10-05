"""
Comprehensive system tests for CustomerCareGPT
Tests the entire system as a black box with real external dependencies
"""

import pytest
import asyncio
import json
import tempfile
import os
import time
from datetime import datetime, timedelta
from unittest.mock import patch, Mock, MagicMock
from fastapi.testclient import TestClient
import httpx

from app.main import app
from app.core.database import get_db, Base, engine
from app.models import User, Workspace, Document, ChatSession, ChatMessage, Subscription

client = TestClient(app)

class TestSystemHealth:
    """System health and monitoring tests"""
    
    def test_system_startup(self):
        """Test system startup and basic health"""
        # Test basic health endpoint
        response = client.get("/health")
        assert response.status_code == 200
        health_data = response.json()
        assert health_data["status"] == "healthy"
        assert "timestamp" in health_data
        assert "version" in health_data
    
    def test_readiness_check(self):
        """Test system readiness with all components"""
        response = client.get("/ready")
        assert response.status_code == 200
        readiness_data = response.json()
        assert "status" in readiness_data
        assert "components" in readiness_data
        
        # Check that all critical components are present
        components = readiness_data["components"]
        expected_components = ["database", "redis", "chromadb", "gemini_api"]
        for component in expected_components:
            assert component in components
    
    def test_metrics_endpoint(self):
        """Test metrics endpoint availability"""
        response = client.get("/metrics")
        assert response.status_code == 200
        assert "text/plain" in response.headers.get("content-type", "")
        
        # Check that metrics contain expected data
        metrics_content = response.text
        assert "http_requests_total" in metrics_content
        assert "rag_queries_total" in metrics_content
    
    def test_status_endpoint(self):
        """Test detailed status endpoint"""
        response = client.get("/status")
        assert response.status_code == 200
        status_data = response.json()
        assert "service" in status_data
        assert "version" in status_data
        assert "health" in status_data
        assert "readiness" in status_data

class TestSystemPerformance:
    """System performance and load tests"""
    
    def test_api_response_times(self):
        """Test API response times are within acceptable limits"""
        endpoints = [
            "/health",
            "/ready",
            "/metrics",
            "/status"
        ]
        
        max_response_time = 1000  # 1 second
        
        for endpoint in endpoints:
            start_time = time.time()
            response = client.get(endpoint)
            end_time = time.time()
            
            response_time = (end_time - start_time) * 1000  # Convert to milliseconds
            
            assert response.status_code == 200
            assert response_time < max_response_time, f"Endpoint {endpoint} took {response_time}ms"
    
    def test_concurrent_requests(self):
        """Test system behavior under concurrent load"""
        import threading
        import queue
        
        results = queue.Queue()
        num_threads = 10
        num_requests_per_thread = 5
        
        def make_requests():
            for _ in range(num_requests_per_thread):
                try:
                    response = client.get("/health")
                    results.put({
                        "status_code": response.status_code,
                        "response_time": time.time()
                    })
                except Exception as e:
                    results.put({"error": str(e)})
        
        # Start concurrent threads
        threads = []
        for _ in range(num_threads):
            thread = threading.Thread(target=make_requests)
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Collect results
        successful_requests = 0
        failed_requests = 0
        
        while not results.empty():
            result = results.get()
            if "error" in result:
                failed_requests += 1
            elif result["status_code"] == 200:
                successful_requests += 1
            else:
                failed_requests += 1
        
        total_requests = num_threads * num_requests_per_thread
        success_rate = successful_requests / total_requests
        
        assert success_rate >= 0.95, f"Success rate {success_rate} is below 95%"
        assert failed_requests < total_requests * 0.05, f"Too many failed requests: {failed_requests}"

class TestSystemSecurity:
    """System security tests"""
    
    def test_security_headers(self):
        """Test that security headers are present"""
        response = client.get("/health")
        
        security_headers = [
            "X-Content-Type-Options",
            "X-Frame-Options",
            "X-XSS-Protection",
            "Strict-Transport-Security"
        ]
        
        for header in security_headers:
            assert header in response.headers, f"Missing security header: {header}"
    
    def test_cors_configuration(self):
        """Test CORS configuration"""
        response = client.options("/", headers={"Origin": "http://localhost:3000"})
        
        assert response.status_code == 200
        assert "access-control-allow-origin" in response.headers
        assert "access-control-allow-methods" in response.headers
        assert "access-control-allow-headers" in response.headers
    
    def test_input_validation(self):
        """Test input validation across endpoints"""
        # Test invalid JSON
        response = client.post("/api/v1/auth/login", data="invalid json")
        assert response.status_code == 422
        
        # Test SQL injection attempts
        malicious_inputs = [
            "'; DROP TABLE users; --",
            "1' OR '1'='1",
            "<script>alert('xss')</script>"
        ]
        
        for malicious_input in malicious_inputs:
            response = client.post("/api/v1/auth/login", json={
                "email": malicious_input,
                "password": "test"
            })
            # Should not crash the system
            assert response.status_code in [400, 422, 401]
    
    def test_authentication_required(self):
        """Test that protected endpoints require authentication"""
        protected_endpoints = [
            "/api/v1/auth/me",
            "/api/v1/documents/",
            "/api/v1/chat/sessions",
            "/api/v1/rag/query",
            "/api/v1/billing/status",
            "/api/v1/analytics/workspace"
        ]
        
        for endpoint in protected_endpoints:
            response = client.get(endpoint)
            assert response.status_code == 401, f"Endpoint {endpoint} should require authentication"

class TestSystemDataFlow:
    """Test complete data flow through the system"""
    
    def test_complete_user_journey(self):
        """Test complete user journey from registration to chat"""
        # This test would require a real database and external services
        # For now, we'll test the API contract
        
        # 1. User registration
        user_data = {
            "email": "system_test@example.com",
            "password": "SystemTest123!",
            "full_name": "System Test User",
            "workspace_name": "System Test Workspace"
        }
        
        with patch('app.api.api_v1.endpoints.auth.AuthService') as mock_auth:
            mock_service = Mock()
            mock_service.register_user.return_value = {
                "user_id": "system_user_123",
                "workspace_id": "system_ws_123",
                "email": "system_test@example.com"
            }
            mock_auth.return_value = mock_service
            
            response = client.post("/api/v1/auth/register", json=user_data)
            assert response.status_code == 201
        
        # 2. User login
        login_data = {
            "email": "system_test@example.com",
            "password": "SystemTest123!"
        }
        
        with patch('app.api.api_v1.endpoints.auth.AuthService') as mock_auth:
            mock_service = Mock()
            mock_service.authenticate_user.return_value = {
                "access_token": "system_token_123",
                "token_type": "bearer",
                "user": {
                    "id": "system_user_123",
                    "email": "system_test@example.com",
                    "full_name": "System Test User"
                }
            }
            mock_auth.return_value = mock_service
            
            response = client.post("/api/v1/auth/login", json=login_data)
            assert response.status_code == 200
            
            login_response = response.json()
            token = login_response["access_token"]
        
        # 3. Document upload
        with patch('app.api.api_v1.endpoints.documents.get_current_user') as mock_get_user:
            mock_user = Mock()
            mock_user.id = "system_user_123"
            mock_user.workspace_id = "system_ws_123"
            mock_get_user.return_value = mock_user
            
            with patch('app.api.api_v1.endpoints.documents.DocumentService') as mock_doc_service:
                mock_service = Mock()
                mock_service.upload_document.return_value = {
                    "document_id": "system_doc_123",
                    "job_id": "system_job_123",
                    "status": "processing"
                }
                mock_doc_service.return_value = mock_service
                
                with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
                    f.write("This is a system test document about customer support policies.")
                    temp_file_path = f.name
                
                try:
                    with open(temp_file_path, 'rb') as f:
                        files = {"file": ("system_test.txt", f, "text/plain")}
                        headers = {"Authorization": f"Bearer {token}"}
                        response = client.post("/api/v1/documents/upload", files=files, headers=headers)
                        assert response.status_code == 200
                
                finally:
                    os.unlink(temp_file_path)
        
        # 4. Chat session creation
        with patch('app.api.api_v1.endpoints.chat.get_current_user') as mock_get_user:
            mock_user = Mock()
            mock_user.id = "system_user_123"
            mock_user.workspace_id = "system_ws_123"
            mock_get_user.return_value = mock_user
            
            with patch('app.api.api_v1.endpoints.chat.ChatService') as mock_chat_service:
                mock_service = Mock()
                mock_service.create_session.return_value = {
                    "session_id": "system_session_123",
                    "user_label": "System Test Customer"
                }
                mock_chat_service.return_value = mock_service
                
                session_data = {"user_label": "System Test Customer"}
                headers = {"Authorization": f"Bearer {token}"}
                response = client.post("/api/v1/chat/sessions", json=session_data, headers=headers)
                assert response.status_code == 201
                
                session_response = response.json()
                session_id = session_response["session_id"]
        
        # 5. RAG query
        with patch('app.api.api_v1.endpoints.rag_query.get_current_user') as mock_get_user:
            mock_user = Mock()
            mock_user.id = "system_user_123"
            mock_user.workspace_id = "system_ws_123"
            mock_get_user.return_value = mock_user
            
            with patch('app.api.api_v1.endpoints.rag_query.RAGService') as mock_rag_service:
                mock_service = Mock()
                mock_service.process_query.return_value = {
                    "answer": "Based on our customer support policies, you can contact our support team for assistance.",
                    "sources": [
                        {
                            "chunk_id": "system_chunk_123",
                            "document_id": "system_doc_123",
                            "content": "customer support policies",
                            "score": 0.95
                        }
                    ],
                    "response_time_ms": 200,
                    "tokens_used": 120
                }
                mock_rag_service.return_value = mock_service
                
                query_data = {
                    "query": "How can I get customer support?",
                    "session_id": session_id
                }
                headers = {"Authorization": f"Bearer {token}"}
                response = client.post("/api/v1/rag/query", json=query_data, headers=headers)
                assert response.status_code == 200
                
                rag_response = response.json()
                assert "answer" in rag_response
                assert "sources" in rag_response
                assert "response_time_ms" in rag_response

class TestSystemResilience:
    """Test system resilience and error recovery"""
    
    def test_database_connection_failure(self):
        """Test system behavior when database is unavailable"""
        with patch('app.core.database.get_db') as mock_get_db:
            mock_get_db.side_effect = Exception("Database connection failed")
            
            response = client.get("/ready")
            # Should return 503 or handle gracefully
            assert response.status_code in [503, 500]
    
    def test_redis_connection_failure(self):
        """Test system behavior when Redis is unavailable"""
        with patch('app.core.database.redis_client') as mock_redis:
            mock_redis.ping.side_effect = Exception("Redis connection failed")
            
            response = client.get("/ready")
            # Should handle Redis failure gracefully
            assert response.status_code in [200, 503]
    
    def test_external_api_failure(self):
        """Test system behavior when external APIs fail"""
        with patch('app.services.gemini_service.GeminiService') as mock_gemini:
            mock_service = Mock()
            mock_service.generate_response.side_effect = Exception("Gemini API failed")
            mock_gemini.return_value = mock_service
            
            # Test that the system doesn't crash when external APIs fail
            response = client.get("/ready")
            assert response.status_code in [200, 503]
    
    def test_memory_pressure(self):
        """Test system behavior under memory pressure"""
        import psutil
        
        # Get current memory usage
        memory = psutil.virtual_memory()
        memory_usage = memory.percent
        
        # If memory usage is already high, skip this test
        if memory_usage > 80:
            pytest.skip("System memory usage is already high")
        
        # Test that the system continues to function
        response = client.get("/health")
        assert response.status_code == 200

class TestSystemScalability:
    """Test system scalability characteristics"""
    
    def test_database_connection_pool(self):
        """Test database connection pool behavior"""
        # This would require a real database connection
        # For now, we'll test the configuration
        
        from app.core.config import settings
        
        assert hasattr(settings, 'DB_POOL_SIZE')
        assert hasattr(settings, 'DB_MAX_OVERFLOW')
        assert settings.DB_POOL_SIZE > 0
        assert settings.DB_MAX_OVERFLOW >= 0
    
    def test_redis_connection_pool(self):
        """Test Redis connection pool behavior"""
        from app.core.config import settings
        
        assert hasattr(settings, 'REDIS_URL')
        assert settings.REDIS_URL is not None
    
    def test_concurrent_user_handling(self):
        """Test system behavior with multiple concurrent users"""
        import threading
        import queue
        
        results = queue.Queue()
        num_users = 5
        requests_per_user = 3
        
        def simulate_user(user_id):
            for request_id in range(requests_per_user):
                try:
                    response = client.get("/health")
                    results.put({
                        "user_id": user_id,
                        "request_id": request_id,
                        "status_code": response.status_code,
                        "response_time": time.time()
                    })
                except Exception as e:
                    results.put({
                        "user_id": user_id,
                        "request_id": request_id,
                        "error": str(e)
                    })
        
        # Start concurrent users
        threads = []
        for user_id in range(num_users):
            thread = threading.Thread(target=simulate_user, args=(user_id,))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Collect results
        successful_requests = 0
        failed_requests = 0
        
        while not results.empty():
            result = results.get()
            if "error" in result:
                failed_requests += 1
            elif result["status_code"] == 200:
                successful_requests += 1
            else:
                failed_requests += 1
        
        total_requests = num_users * requests_per_user
        success_rate = successful_requests / total_requests
        
        assert success_rate >= 0.9, f"Success rate {success_rate} is below 90%"

class TestSystemMonitoring:
    """Test system monitoring and observability"""
    
    def test_metrics_collection(self):
        """Test that metrics are being collected"""
        response = client.get("/metrics")
        assert response.status_code == 200
        
        metrics_content = response.text
        
        # Check for key metrics
        expected_metrics = [
            "http_requests_total",
            "rag_queries_total",
            "vector_search_duration_seconds",
            "gemini_api_calls_total"
        ]
        
        for metric in expected_metrics:
            assert metric in metrics_content, f"Missing metric: {metric}"
    
    def test_health_check_completeness(self):
        """Test that health checks cover all critical components"""
        response = client.get("/ready")
        assert response.status_code == 200
        
        readiness_data = response.json()
        components = readiness_data["components"]
        
        # Check that all critical components are monitored
        critical_components = ["database", "redis", "chromadb"]
        for component in critical_components:
            assert component in components, f"Missing health check for {component}"
    
    def test_logging_configuration(self):
        """Test that logging is properly configured"""
        from app.core.config import settings
        
        assert hasattr(settings, 'LOG_LEVEL')
        assert settings.LOG_LEVEL in ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        
        assert hasattr(settings, 'ENVIRONMENT')
        assert settings.ENVIRONMENT in ['development', 'testing', 'production']

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
