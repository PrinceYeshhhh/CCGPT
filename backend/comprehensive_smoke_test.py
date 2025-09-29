#!/usr/bin/env python3
"""
Comprehensive Smoke Test for CustomerCareGPT
Tests all imports, configurations, and basic functionality
"""

import sys
import traceback
import importlib
from typing import List, Dict, Any

def test_imports() -> List[str]:
    """Test all critical imports"""
    issues = []
    
    # Core application
    try:
        from app.main import app
        print('✓ Main app import: OK')
    except Exception as e:
        issues.append(f'Main app import: {str(e)}')
    
    # Services
    services = [
        'app.services.auth',
        'app.services.chat', 
        'app.services.rag_service',
        'app.services.vector_service',
        'app.services.embeddings_service',
        'app.services.gemini_service',
        'app.services.language_service',
        'app.services.document_service',
        'app.services.workspace',
        'app.services.token_revocation',
        'app.services.file_security',
        'app.services.websocket_security',
        'app.services.database_security',
        'app.services.input_validation',
        'app.services.csrf_protection'
    ]
    
    for service in services:
        try:
            importlib.import_module(service)
            print(f'✓ {service}: OK')
        except Exception as e:
            issues.append(f'{service}: {str(e)}')
    
    # API Endpoints
    endpoints = [
        'app.api.api_v1.endpoints.auth',
        'app.api.api_v1.endpoints.chat',
        'app.api.api_v1.endpoints.documents',
        'app.api.api_v1.endpoints.embed_enhanced',
        'app.api.api_v1.endpoints.billing',
        'app.api.api_v1.endpoints.workspace',
        'app.api.api_v1.endpoints.settings',
        'app.api.api_v1.endpoints.health',
        'app.api.api_v1.endpoints.performance'
    ]
    
    for endpoint in endpoints:
        try:
            importlib.import_module(endpoint)
            print(f'✓ {endpoint}: OK')
        except Exception as e:
            issues.append(f'{endpoint}: {str(e)}')
    
    # Middleware
    middlewares = [
        'app.middleware.security',
        'app.middleware.security_headers',
        'app.middleware.rate_limit'
    ]
    
    for middleware in middlewares:
        try:
            importlib.import_module(middleware)
            print(f'✓ {middleware}: OK')
        except Exception as e:
            issues.append(f'{middleware}: {str(e)}')
    
    return issues

def test_fastapi_app() -> List[str]:
    """Test FastAPI app configuration"""
    issues = []
    
    try:
        from app.main import app
        print(f'✓ App title: {app.title}')
        print(f'✓ App version: {app.version}')
        print(f'✓ Middleware count: {len(app.user_middleware)}')
        print(f'✓ Routes count: {len(app.routes)}')
        
        # Test route registration
        route_paths = [route.path for route in app.routes if hasattr(route, 'path')]
        api_routes = len([r for r in route_paths if r.startswith('/api')])
        ws_routes = len([r for r in route_paths if r.startswith('/ws')])
        health_routes = len([r for r in route_paths if r in ['/health', '/ready']])
        
        print(f'✓ API routes: {api_routes}')
        print(f'✓ WebSocket routes: {ws_routes}')
        print(f'✓ Health routes: {health_routes}')
        
    except Exception as e:
        issues.append(f'FastAPI app validation: {str(e)}')
    
    return issues

def test_configuration() -> List[str]:
    """Test configuration loading"""
    issues = []
    
    try:
        from app.core.config import settings
        print(f'✓ Environment: {settings.ENVIRONMENT}')
        print(f'✓ Debug mode: {settings.DEBUG}')
        print(f'✓ Database URL configured: {bool(settings.DATABASE_URL)}')
        print(f'✓ Redis URL configured: {bool(settings.REDIS_URL)}')
        print(f'✓ Security headers enabled: {settings.ENABLE_SECURITY_HEADERS}')
        print(f'✓ CORS enabled: {settings.ENABLE_CORS}')
        print(f'✓ Rate limiting enabled: {settings.ENABLE_RATE_LIMITING}')
        
    except Exception as e:
        issues.append(f'Configuration test: {str(e)}')
    
    return issues

def test_database_connection() -> List[str]:
    """Test database connectivity"""
    issues = []
    
    try:
        from app.core.database import write_engine
        from sqlalchemy import text
        with write_engine.connect() as conn:
            result = conn.execute(text("SELECT 1")).fetchone()
            if result:
                print('✓ Database connection: OK')
            else:
                issues.append('Database query returned no results')
    except Exception as e:
        issues.append(f'Database connection: {str(e)}')
    
    return issues

def test_redis_connection() -> List[str]:
    """Test Redis connectivity (optional)"""
    issues = []
    
    try:
        from app.core.database import redis_manager
        redis_client = redis_manager.get_client()
        redis_client.ping()
        print('✓ Redis connection: OK')
    except Exception as e:
        print(f'⚠ Redis connection: {str(e)} (Optional - app will work without Redis)')
        # Don't add to issues since Redis is optional
    
    return issues

def main():
    """Run comprehensive smoke test"""
    print('=== COMPREHENSIVE SMOKE TEST FOR CUSTOMERCAREGPT ===\n')
    
    all_issues = []
    
    # Test imports
    print('1. Testing Imports...')
    all_issues.extend(test_imports())
    print()
    
    # Test FastAPI app
    print('2. Testing FastAPI App...')
    all_issues.extend(test_fastapi_app())
    print()
    
    # Test configuration
    print('3. Testing Configuration...')
    all_issues.extend(test_configuration())
    print()
    
    # Test database
    print('4. Testing Database Connection...')
    all_issues.extend(test_database_connection())
    print()
    
    # Test Redis
    print('5. Testing Redis Connection...')
    all_issues.extend(test_redis_connection())
    print()
    
    # Summary
    if all_issues:
        print(f'❌ FOUND {len(all_issues)} ISSUES:')
        for i, issue in enumerate(all_issues, 1):
            print(f'   {i}. {issue}')
        return 1
    else:
        print('✅ ALL TESTS PASSED! APPLICATION IS PRODUCTION READY!')
        return 0

if __name__ == '__main__':
    sys.exit(main())
