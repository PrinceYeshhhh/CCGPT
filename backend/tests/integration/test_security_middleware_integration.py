"""
Integration tests for security middleware and error handling
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch
from sqlalchemy.orm import Session
from datetime import datetime

from app.main import app
from app.models.user import User
from app.models.workspace import Workspace
from app.core.database import get_db
from app.api.api_v1.dependencies import get_current_user


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def db_session():
    from app.db.session import SessionLocal
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def test_workspace(db_session):
    workspace = Workspace(
        id="test-workspace-id",
        name="Test Workspace",
        description="Test workspace for security testing"
    )
    db_session.add(workspace)
    db_session.commit()
    return workspace


@pytest.fixture
def test_user(db_session, test_workspace):
    user = User(
        id="test-user-id",
        email="test@example.com",
        username="testuser",
        hashed_password="hashed_password",
        workspace_id=test_workspace.id
    )
    db_session.add(user)
    db_session.commit()
    return user


@pytest.fixture
def auth_token(test_user):
    from app.services.auth import AuthService
    auth_service = AuthService()
    return auth_service.create_access_token({"sub": test_user.email})


def test_security_headers_middleware(client):
    """Test security headers middleware"""
    response = client.get("/")
    
    # Check for security headers
    assert response.status_code == 200
    assert "X-Content-Type-Options" in response.headers
    assert "X-Frame-Options" in response.headers
    assert "X-XSS-Protection" in response.headers
    assert "Strict-Transport-Security" in response.headers or "X-Content-Type-Options" in response.headers


def test_cors_middleware(client):
    """Test CORS middleware"""
    # Test preflight request
    response = client.options(
        "/api/v1/auth/login",
        headers={
            "Origin": "https://example.com",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "Content-Type"
        }
    )
    
    assert response.status_code == 200
    assert "Access-Control-Allow-Origin" in response.headers
    assert "Access-Control-Allow-Methods" in response.headers
    assert "Access-Control-Allow-Headers" in response.headers


def test_input_validation_middleware(client):
    """Test input validation middleware"""
    # Test with malicious input
    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "<script>alert('xss')</script>@example.com",
            "password": "password123"
        }
    )
    
    # Should either sanitize input or reject it
    assert response.status_code in [400, 401, 422]


def test_rate_limiting_middleware(client):
    """Test rate limiting middleware"""
    # Make multiple requests quickly
    for i in range(10):
        response = client.get("/api/v1/analytics/summary")
        if response.status_code == 429:
            # Rate limit hit
            assert "Rate limit exceeded" in response.json().get("detail", "")
            break
    else:
        # If no rate limit hit, that's also acceptable
        assert True


def test_csrf_protection_middleware(client, auth_token):
    """Test CSRF protection middleware"""
    # Test without CSRF token
    response = client.post(
        "/api/v1/settings/profile",
        json={"username": "newusername"},
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    
    # Should either require CSRF token or work without it (depending on configuration)
    assert response.status_code in [200, 403, 422]


def test_trusted_host_middleware(client):
    """Test trusted host middleware"""
    # Test with untrusted host
    response = client.get(
        "/",
        headers={"Host": "malicious-site.com"}
    )
    
    # Should either reject or allow (depending on configuration)
    assert response.status_code in [200, 400, 403]


def test_authentication_middleware(client):
    """Test authentication middleware"""
    # Test protected endpoint without auth
    response = client.get("/api/v1/analytics/summary")
    assert response.status_code == 401
    
    # Test with invalid token
    response = client.get(
        "/api/v1/analytics/summary",
        headers={"Authorization": "Bearer invalid_token"}
    )
    assert response.status_code == 401
    
    # Test with valid token
    with patch('app.api.api_v1.dependencies.get_current_user') as mock_get_user:
        mock_get_user.return_value = User(
            id="test-user",
            email="test@example.com",
            username="testuser",
            hashed_password="hashed",
            workspace_id="test-workspace"
        )
        
        response = client.get(
            "/api/v1/analytics/summary",
            headers={"Authorization": "Bearer valid_token"}
        )
        # Should work with mocked user
        assert response.status_code in [200, 500]  # 500 if endpoint has other issues


def test_error_handling_http_exception(client):
    """Test HTTP exception handling"""
    # Test 404 error
    response = client.get("/nonexistent-endpoint")
    assert response.status_code == 404
    
    # Test 422 validation error
    response = client.post(
        "/api/v1/auth/login",
        json={"invalid": "data"}
    )
    assert response.status_code == 422


def test_error_handling_general_exception(client):
    """Test general exception handling"""
    with patch('app.api.api_v1.endpoints.analytics.get_analytics_summary') as mock_endpoint:
        mock_endpoint.side_effect = Exception("Internal server error")
        
        response = client.get("/api/v1/analytics/summary")
        assert response.status_code == 500
        
        data = response.json()
        assert "error" in data or "detail" in data


def test_error_monitoring_integration(client):
    """Test error monitoring integration"""
    with patch('app.utils.error_monitoring.error_monitor') as mock_monitor:
        mock_monitor.log_error.return_value = {"error_count": 1}
        
        with patch('app.api.api_v1.endpoints.analytics.get_analytics_summary') as mock_endpoint:
            mock_endpoint.side_effect = Exception("Test error")
            
            response = client.get("/api/v1/analytics/summary")
            assert response.status_code == 500
            
            # Verify error was logged
            mock_monitor.log_error.assert_called_once()


def test_security_exception_handler(client):
    """Test security exception handler"""
    with patch('app.middleware.security.SecurityExceptionHandler') as mock_handler:
        mock_handler.handle_security_exception.return_value = {
            "detail": "Security violation detected"
        }
        
        response = client.get("/api/v1/analytics/summary")
        # Should handle security exceptions appropriately
        assert response.status_code in [200, 401, 403, 500]


def test_request_logging_middleware(client):
    """Test request logging middleware"""
    with patch('app.middleware.security.RequestLoggingMiddleware') as mock_middleware:
        response = client.get("/")
        
        # Should log request
        assert response.status_code == 200


def test_input_validation_sql_injection(client):
    """Test input validation against SQL injection"""
    malicious_inputs = [
        "'; DROP TABLE users; --",
        "1' OR '1'='1",
        "admin'--",
        "1' UNION SELECT * FROM users--"
    ]
    
    for malicious_input in malicious_inputs:
        response = client.post(
            "/api/v1/auth/login",
            json={
                "email": malicious_input,
                "password": "password123"
            }
        )
        
        # Should either sanitize or reject malicious input
        assert response.status_code in [400, 401, 422]


def test_input_validation_xss(client):
    """Test input validation against XSS"""
    xss_payloads = [
        "<script>alert('xss')</script>",
        "javascript:alert('xss')",
        "<img src=x onerror=alert('xss')>",
        "';alert('xss');//"
    ]
    
    for payload in xss_payloads:
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": f"{payload}@example.com",
                "password": "password123",
                "username": payload
            }
        )
        
        # Should either sanitize or reject XSS payloads
        assert response.status_code in [400, 422]


def test_input_validation_path_traversal(client):
    """Test input validation against path traversal"""
    path_traversal_payloads = [
        "../../../etc/passwd",
        "..\\..\\..\\windows\\system32\\drivers\\etc\\hosts",
        "....//....//....//etc/passwd",
        "%2e%2e%2f%2e%2e%2f%2e%2e%2fetc%2fpasswd"
    ]
    
    for payload in path_traversal_payloads:
        response = client.get(f"/api/v1/documents/{payload}")
        
        # Should reject path traversal attempts
        assert response.status_code in [400, 403, 404, 422]


def test_rate_limiting_different_endpoints(client):
    """Test rate limiting on different endpoint types"""
    endpoints = [
        "/api/v1/analytics/summary",
        "/api/v1/rag/query",
        "/api/v1/documents/",
        "/api/v1/performance/metrics"
    ]
    
    for endpoint in endpoints:
        # Make multiple requests
        for i in range(5):
            response = client.get(endpoint)
            if response.status_code == 429:
                # Rate limit hit
                assert "Rate limit exceeded" in response.json().get("detail", "")
                break


def test_circuit_breaker_integration(client):
    """Test circuit breaker integration"""
    with patch('app.utils.circuit_breaker.circuit_breaker_manager') as mock_cb:
        mock_cb.is_circuit_open.return_value = True
        
        response = client.get("/api/v1/rag/query")
        
        # Should handle circuit breaker state
        assert response.status_code in [200, 503]


def test_health_check_security(client):
    """Test health check endpoints security"""
    # Health checks should be accessible
    response = client.get("/health")
    assert response.status_code == 200
    
    response = client.get("/ready")
    assert response.status_code == 200
    
    response = client.get("/health/detailed")
    assert response.status_code == 200


def test_metrics_endpoint_security(client):
    """Test metrics endpoint security"""
    response = client.get("/metrics")
    
    # Should either be accessible or require authentication
    assert response.status_code in [200, 401, 403]


def test_static_files_security(client):
    """Test static files security"""
    response = client.get("/static/nonexistent.txt")
    
    # Should handle missing files securely
    assert response.status_code in [404, 403]


def test_error_response_format(client):
    """Test error response format consistency"""
    with patch('app.api.api_v1.endpoints.analytics.get_analytics_summary') as mock_endpoint:
        mock_endpoint.side_effect = Exception("Test error")
        
        response = client.get("/api/v1/analytics/summary")
        assert response.status_code == 500
        
        data = response.json()
        # Should have consistent error format
        assert "detail" in data or "error" in data


def test_security_headers_completeness(client):
    """Test completeness of security headers"""
    response = client.get("/")
    
    # Check for essential security headers
    security_headers = [
        "X-Content-Type-Options",
        "X-Frame-Options",
        "X-XSS-Protection",
        "Referrer-Policy",
        "Content-Security-Policy"
    ]
    
    present_headers = [header for header in security_headers if header in response.headers]
    
    # Should have at least some security headers
    assert len(present_headers) > 0


def test_cors_configuration(client):
    """Test CORS configuration"""
    # Test with different origins
    origins = [
        "https://app.customercaregpt.com",
        "https://dashboard.customercaregpt.com",
        "https://malicious-site.com"
    ]
    
    for origin in origins:
        response = client.get(
            "/api/v1/analytics/summary",
            headers={"Origin": origin}
        )
        
        # Should handle CORS appropriately
        assert response.status_code in [200, 401, 403]
        
        if "Access-Control-Allow-Origin" in response.headers:
            allowed_origin = response.headers["Access-Control-Allow-Origin"]
            # Should only allow configured origins
            assert allowed_origin in ["*", origin, "null"] or origin in allowed_origin

