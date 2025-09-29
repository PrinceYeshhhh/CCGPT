#!/usr/bin/env python3
"""
CustomerCareGPT Local Development Testing Script
Tests the local backend against the cloud frontend
"""

import requests
import asyncio
import httpx
import os
import time
import json
from typing import Dict, Any

# Configuration
LOCAL_BACKEND_URL = "http://localhost:8000"
CLOUD_FRONTEND_URL = "https://customercaregpt-frontend.vercel.app"
API_V1_URL = f"{LOCAL_BACKEND_URL}/api/v1"

def log_status(message: str, status: str = "INFO"):
    """Log status with colors"""
    color_map = {
        "INFO": "\033[94m",    # Blue
        "SUCCESS": "\033[92m", # Green
        "WARNING": "\033[93m", # Yellow
        "ERROR": "\033[91m",   # Red
        "RESET": "\033[0m"     # Reset
    }
    print(f"{color_map.get(status, color_map['INFO'])}[{status}] {message}{color_map['RESET']}")

def test_local_backend_health():
    """Test local backend health endpoints"""
    log_status("Testing Local Backend Health...", "INFO")
    
    endpoints = {
        "/health": "Basic Health Check",
        "/ready": "Readiness Check",
        "/debug/health": "Debug Health Check"
    }
    
    for endpoint, description in endpoints.items():
        try:
            response = requests.get(f"{LOCAL_BACKEND_URL}{endpoint}", timeout=10)
            if response.status_code == 200:
                log_status(f"✅ {description} ({endpoint}) is healthy", "SUCCESS")
            else:
                log_status(f"❌ {description} ({endpoint}) returned status {response.status_code}", "ERROR")
        except requests.RequestError as e:
            log_status(f"❌ {description} ({endpoint}) not accessible: {e}", "ERROR")

def test_cors_configuration():
    """Test CORS configuration for cloud frontend"""
    log_status("Testing CORS Configuration...", "INFO")
    
    try:
        response = requests.options(
            f"{API_V1_URL}/auth/login",
            headers={
                "Origin": CLOUD_FRONTEND_URL,
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "Content-Type"
            },
            timeout=10
        )
        
        if response.status_code == 200:
            cors_headers = {
                "access-control-allow-origin": response.headers.get("access-control-allow-origin"),
                "access-control-allow-methods": response.headers.get("access-control-allow-methods"),
                "access-control-allow-headers": response.headers.get("access-control-allow-headers")
            }
            
            if CLOUD_FRONTEND_URL in cors_headers.get("access-control-allow-origin", ""):
                log_status("✅ CORS configured correctly for cloud frontend", "SUCCESS")
            else:
                log_status(f"⚠️  CORS may not be configured for cloud frontend: {cors_headers}", "WARNING")
        else:
            log_status(f"❌ CORS preflight failed with status {response.status_code}", "ERROR")
            
    except requests.RequestError as e:
        log_status(f"❌ CORS test failed: {e}", "ERROR")

def test_api_endpoints():
    """Test core API endpoints"""
    log_status("Testing Core API Endpoints...", "INFO")
    
    # Test public endpoints that don't require authentication
    public_endpoints = [
        "/health",
        "/ready",
        "/debug/health",
        "/debug/test-connectivity"
    ]
    
    for endpoint in public_endpoints:
        try:
            response = requests.get(f"{LOCAL_BACKEND_URL}{endpoint}", timeout=10)
            if response.status_code == 200:
                log_status(f"✅ {endpoint} is accessible", "SUCCESS")
            else:
                log_status(f"⚠️  {endpoint} returned status {response.status_code}", "WARNING")
        except requests.RequestError as e:
            log_status(f"❌ {endpoint} not accessible: {e}", "ERROR")
    
    # Test protected endpoints (should return 401/403)
    protected_endpoints = [
        "/api/v1/users/me",
        "/api/v1/workspaces/",
        "/api/v1/documents/",
        "/api/v1/chat/sessions"
    ]
    
    for endpoint in protected_endpoints:
        try:
            response = requests.get(f"{LOCAL_BACKEND_URL}{endpoint}", timeout=10)
            if response.status_code in [401, 403]:
                log_status(f"✅ {endpoint} properly protected (status {response.status_code})", "SUCCESS")
            else:
                log_status(f"⚠️  {endpoint} returned unexpected status {response.status_code}", "WARNING")
        except requests.RequestError as e:
            log_status(f"❌ {endpoint} not accessible: {e}", "ERROR")

def test_database_connectivity():
    """Test database connectivity through debug endpoint"""
    log_status("Testing Database Connectivity...", "INFO")
    
    try:
        response = requests.get(f"{LOCAL_BACKEND_URL}/debug/test-connectivity", timeout=10)
        if response.status_code == 200:
            data = response.json()
            
            # Check Redis
            if "redis" in data and data["redis"]["status"] == "connected":
                log_status("✅ Redis is connected", "SUCCESS")
            else:
                log_status(f"❌ Redis connection issue: {data.get('redis', {})}", "ERROR")
            
            # Check ChromaDB
            if "chromadb" in data and data["chromadb"]["status"] == "connected":
                log_status("✅ ChromaDB is connected", "SUCCESS")
            else:
                log_status(f"❌ ChromaDB connection issue: {data.get('chromadb', {})}", "ERROR")
                
        else:
            log_status(f"❌ Debug connectivity test failed with status {response.status_code}", "ERROR")
            
    except requests.RequestError as e:
        log_status(f"❌ Database connectivity test failed: {e}", "ERROR")

def test_frontend_connectivity():
    """Test if cloud frontend can reach local backend"""
    log_status("Testing Frontend to Backend Connectivity...", "INFO")
    
    # This is a simulation - in reality, the frontend would make requests
    # We can test if our CORS configuration allows the frontend to make requests
    
    try:
        # Simulate a request from the frontend
        response = requests.get(
            f"{LOCAL_BACKEND_URL}/health",
            headers={"Origin": CLOUD_FRONTEND_URL},
            timeout=10
        )
        
        if response.status_code == 200:
            cors_origin = response.headers.get("access-control-allow-origin")
            if CLOUD_FRONTEND_URL in (cors_origin or ""):
                log_status("✅ Frontend can reach backend with proper CORS", "SUCCESS")
            else:
                log_status(f"⚠️  CORS may not be properly configured: {cors_origin}", "WARNING")
        else:
            log_status(f"❌ Backend not reachable from frontend simulation: {response.status_code}", "ERROR")
            
    except requests.RequestError as e:
        log_status(f"❌ Frontend connectivity test failed: {e}", "ERROR")

def main():
    """Main testing function"""
    log_status("Starting CustomerCareGPT Local Development Tests...", "INFO")
    log_status("=" * 60, "INFO")
    
    # Test local backend
    test_local_backend_health()
    test_database_connectivity()
    test_api_endpoints()
    test_cors_configuration()
    test_frontend_connectivity()
    
    log_status("=" * 60, "INFO")
    log_status("Local development testing complete!", "INFO")
    log_status("", "INFO")
    log_status("🌐 Access Points:", "INFO")
    log_status(f"   - Local Backend: {LOCAL_BACKEND_URL}", "INFO")
    log_status(f"   - API Docs: {LOCAL_BACKEND_URL}/docs", "INFO")
    log_status(f"   - Health Check: {LOCAL_BACKEND_URL}/health", "INFO")
    log_status(f"   - Cloud Frontend: {CLOUD_FRONTEND_URL}", "INFO")
    log_status("", "INFO")
    log_status("📊 To view backend logs:", "INFO")
    log_status("   docker-compose -f docker-compose.local.yml logs -f backend", "INFO")
    log_status("", "INFO")
    log_status("🛑 To stop local services:", "INFO")
    log_status("   docker-compose -f docker-compose.local.yml down", "INFO")

if __name__ == "__main__":
    main()
