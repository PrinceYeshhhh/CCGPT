"""
Unit tests for all middleware components
Tests security, rate limiting, input validation, and error handling
"""

import pytest
import json
from unittest.mock import Mock, patch, MagicMock
from fastapi import FastAPI, Request, HTTPException
from fastapi.testclient import TestClient
from fastapi.responses import JSONResponse

from app.middleware.security import (
    InputValidationMiddleware,
    RateLimitMiddleware,
    RequestLoggingMiddleware,
    SecurityExceptionHandler,
    CSRFProtectionMiddleware
)
from app.middleware.security_headers import SecurityHeadersMiddleware
from app.middleware.rate_limit import RateLimiter
from app.middleware.quota_middleware import QuotaMiddleware

class TestInputValidationMiddleware:
    """Test input validation middleware"""
    
    def test_valid_json_request(self):
        """Test middleware allows valid JSON requests"""
        app = FastAPI()
        app.add_middleware(InputValidationMiddleware)
        
        @app.post("/test")
        async def test_endpoint(request: Request):
            return {"status": "success"}
        
        client = TestClient(app)
        response = client.post("/test", json={"valid": "data"})
        
        assert response.status_code == 200
        assert response.json() == {"status": "success"}
    
    def test_invalid_json_request(self):
        """Test middleware blocks invalid JSON requests"""
        app = FastAPI()
        app.add_middleware(InputValidationMiddleware)
        
        @app.post("/test")
        async def test_endpoint(request: Request):
            return {"status": "success"}
        
        client = TestClient(app)
        response = client.post("/test", data="invalid json")
        
        assert response.status_code == 400
        assert "Invalid JSON" in response.json()["detail"]
    
    def test_sql_injection_attempt(self):
        """Test middleware blocks SQL injection attempts"""
        app = FastAPI()
        app.add_middleware(InputValidationMiddleware)
        
        @app.post("/test")
        async def test_endpoint(request: Request):
            return {"status": "success"}
        
        client = TestClient(app)
        malicious_data = {"query": "'; DROP TABLE users; --"}
        response = client.post("/test", json=malicious_data)
        
        assert response.status_code == 400
        assert "Invalid input" in response.json()["detail"]
    
    def test_xss_attempt(self):
        """Test middleware blocks XSS attempts"""
        app = FastAPI()
        app.add_middleware(InputValidationMiddleware)
        
        @app.post("/test")
        async def test_endpoint(request: Request):
            return {"status": "success"}
        
        client = TestClient(app)
        malicious_data = {"content": "<script>alert('xss')</script>"}
        response = client.post("/test", json=malicious_data)
        
        assert response.status_code == 400
        assert "Invalid input" in response.json()["detail"]

class TestRateLimitMiddleware:
    """Test rate limiting middleware"""
    
    def test_rate_limit_allows_normal_requests(self):
        """Test middleware allows normal request rates"""
        app = FastAPI()
        app.add_middleware(RateLimitMiddleware)
        
        @app.get("/test")
        async def test_endpoint():
            return {"status": "success"}
        
        client = TestClient(app)
        
        # Make several requests within limit
        for _ in range(5):
            response = client.get("/test")
            assert response.status_code == 200
    
    def test_rate_limit_blocks_excessive_requests(self):
        """Test middleware blocks excessive requests"""
        app = FastAPI()
        app.add_middleware(RateLimitMiddleware)
        
        @app.get("/test")
        async def test_endpoint():
            return {"status": "success"}
        
        client = TestClient(app)
        
        # Make many requests quickly
        responses = []
        for _ in range(100):
            response = client.get("/test")
            responses.append(response.status_code)
        
        # Should have some 429 responses
        assert 429 in responses
    
    def test_rate_limit_resets_after_window(self):
        """Test rate limit resets after time window"""
        app = FastAPI()
        app.add_middleware(RateLimitMiddleware)
        
        @app.get("/test")
        async def test_endpoint():
            return {"status": "success"}
        
        client = TestClient(app)
        
        # Exceed rate limit
        for _ in range(100):
            client.get("/test")
        
        # Wait for rate limit to reset (mocked)
        with patch('time.time', return_value=3600):  # 1 hour later
            response = client.get("/test")
            assert response.status_code == 200

class TestSecurityHeadersMiddleware:
    """Test security headers middleware"""
    
    def test_security_headers_added(self):
        """Test that security headers are added to responses"""
        app = FastAPI()
        app.add_middleware(SecurityHeadersMiddleware)
        
        @app.get("/test")
        async def test_endpoint():
            return {"status": "success"}
        
        client = TestClient(app)
        response = client.get("/test")
        
        assert response.status_code == 200
        assert "X-Content-Type-Options" in response.headers
        assert "X-Frame-Options" in response.headers
        assert "X-XSS-Protection" in response.headers
        assert "Strict-Transport-Security" in response.headers
    
    def test_csp_header_added(self):
        """Test that Content Security Policy header is added"""
        app = FastAPI()
        app.add_middleware(SecurityHeadersMiddleware)
        
        @app.get("/test")
        async def test_endpoint():
            return {"status": "success"}
        
        client = TestClient(app)
        response = client.get("/test")
        
        assert response.status_code == 200
        assert "Content-Security-Policy" in response.headers

class TestCSRFProtectionMiddleware:
    """Test CSRF protection middleware"""
    
    def test_csrf_token_required_for_post(self):
        """Test that CSRF token is required for POST requests"""
        app = FastAPI()
        app.add_middleware(CSRFProtectionMiddleware)
        
        @app.post("/test")
        async def test_endpoint():
            return {"status": "success"}
        
        client = TestClient(app)
        response = client.post("/test", json={"data": "test"})
        
        assert response.status_code == 403
        assert "CSRF token" in response.json()["detail"]
    
    def test_csrf_token_validates_correctly(self):
        """Test that valid CSRF token is accepted"""
        app = FastAPI()
        app.add_middleware(CSRFProtectionMiddleware)
        
        @app.get("/csrf-token")
        async def get_csrf_token():
            return {"csrf_token": "valid-token"}
        
        @app.post("/test")
        async def test_endpoint():
            return {"status": "success"}
        
        client = TestClient(app)
        
        # Get CSRF token
        token_response = client.get("/csrf-token")
        csrf_token = token_response.json()["csrf_token"]
        
        # Use CSRF token in POST request
        response = client.post(
            "/test", 
            json={"data": "test"},
            headers={"X-CSRF-Token": csrf_token}
        )
        
        assert response.status_code == 200

class TestQuotaMiddleware:
    """Test quota middleware"""
    
    def test_quota_check_passes(self):
        """Test that requests within quota are allowed"""
        app = FastAPI()
        app.add_middleware(QuotaMiddleware)
        
        @app.get("/test")
        async def test_endpoint():
            return {"status": "success"}
        
        client = TestClient(app)
        response = client.get("/test")
        
        assert response.status_code == 200
    
    def test_quota_exceeded_blocks_request(self):
        """Test that requests exceeding quota are blocked"""
        app = FastAPI()
        app.add_middleware(QuotaMiddleware)
        
        @app.get("/test")
        async def test_endpoint():
            return {"status": "success"}
        
        client = TestClient(app)
        
        # Mock quota exceeded
        with patch('app.middleware.quota_middleware.QuotaMiddleware.check_quota', return_value=False):
            response = client.get("/test")
            assert response.status_code == 429
            assert "quota exceeded" in response.json()["detail"].lower()

class TestRequestLoggingMiddleware:
    """Test request logging middleware"""
    
    def test_request_logged(self):
        """Test that requests are logged"""
        app = FastAPI()
        app.add_middleware(RequestLoggingMiddleware)
        
        @app.get("/test")
        async def test_endpoint():
            return {"status": "success"}
        
        client = TestClient(app)
        
        with patch('app.middleware.security.RequestLoggingMiddleware.log_request') as mock_log:
            response = client.get("/test")
            
            assert response.status_code == 200
            mock_log.assert_called_once()
    
    def test_error_logged(self):
        """Test that errors are logged"""
        app = FastAPI()
        app.add_middleware(RequestLoggingMiddleware)
        
        @app.get("/test")
        async def test_endpoint():
            raise HTTPException(status_code=500, detail="Test error")
        
        client = TestClient(app)
        
        with patch('app.middleware.security.RequestLoggingMiddleware.log_error') as mock_log:
            response = client.get("/test")
            
            assert response.status_code == 500
            mock_log.assert_called_once()

class TestSecurityExceptionHandler:
    """Test security exception handler"""
    
    def test_http_exception_handled(self):
        """Test that HTTP exceptions are handled securely"""
        app = FastAPI()
        
        @app.exception_handler(HTTPException)
        async def http_exception_handler(request: Request, exc: HTTPException):
            return SecurityExceptionHandler.handle_security_exception(request, exc)
        
        @app.get("/test")
        async def test_endpoint():
            raise HTTPException(status_code=404, detail="Not found")
        
        client = TestClient(app)
        response = client.get("/test")
        
        assert response.status_code == 404
        # Should not expose internal details
        assert "traceback" not in response.json()
    
    def test_sensitive_data_not_exposed(self):
        """Test that sensitive data is not exposed in error responses"""
        app = FastAPI()
        
        @app.exception_handler(HTTPException)
        async def http_exception_handler(request: Request, exc: HTTPException):
            return SecurityExceptionHandler.handle_security_exception(request, exc)
        
        @app.get("/test")
        async def test_endpoint():
            raise HTTPException(status_code=500, detail="Database connection failed: password=secret")
        
        client = TestClient(app)
        response = client.get("/test")
        
        assert response.status_code == 500
        # Should not expose password
        assert "password=secret" not in response.json()["detail"]

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
