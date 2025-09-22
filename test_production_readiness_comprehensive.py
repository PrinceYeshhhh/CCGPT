#!/usr/bin/env python3
"""
Comprehensive Production Readiness Test Suite
Tests all critical components and integrations for production deployment
"""

import asyncio
import sys
import os
import time
import json
from datetime import datetime
from typing import Dict, Any, List
import subprocess
import requests
import psutil

# Add the backend directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from backend.app.utils.production_validator import production_validator
from backend.app.core.config import settings
class ProductionReadinessTester:
    """Comprehensive production readiness testing"""
    
    def __init__(self):
        self.results = {
            "timestamp": datetime.utcnow().isoformat(),
            "tests": {},
            "overall_status": "unknown",
            "summary": {
                "total_tests": 0,
                "passed": 0,
                "failed": 0,
                "warnings": 0
            }
        }
    
    async def run_all_tests(self) -> Dict[str, Any]:
        """Run all production readiness tests"""
        print("🚀 Starting Comprehensive Production Readiness Tests")
        print("=" * 60)
        
        # Test categories
        test_categories = [
            ("Environment Setup", self.test_environment_setup),
            ("Database Tests", self.test_database),
            ("Redis Tests", self.test_redis),
            ("ChromaDB Tests", self.test_chromadb),
            ("API Tests", self.test_api_endpoints),
            ("Security Tests", self.test_security),
            ("Performance Tests", self.test_performance),
            ("Monitoring Tests", self.test_monitoring),
            ("Frontend Tests", self.test_frontend),
            ("Integration Tests", self.test_integrations),
            ("Docker Tests", self.test_docker),
            ("Production Validation", self.test_production_validation)
        ]
        
        for category_name, test_func in test_categories:
            print(f"\n📋 Running {category_name}...")
            try:
                result = await test_func()
                self.results["tests"][category_name] = result
                self.update_summary(result)
                self.print_test_result(category_name, result)
            except Exception as e:
                error_result = {
                    "status": "failed",
                    "message": f"Test execution failed: {str(e)}",
                    "details": {"error": str(e)}
                }
                self.results["tests"][category_name] = error_result
                self.update_summary(error_result)
                self.print_test_result(category_name, error_result)
        
        # Determine overall status
        self.determine_overall_status()
        
        # Print final summary
        self.print_final_summary()
        
        return self.results
    
    async def test_environment_setup(self) -> Dict[str, Any]:
        """Test environment setup and configuration"""
        issues = []
        warnings = []
        
        # Check required environment variables
        required_vars = [
            "DATABASE_URL", "REDIS_URL", "CHROMA_URL", "GEMINI_API_KEY",
            "SECRET_KEY", "STRIPE_API_KEY", "STRIPE_WEBHOOK_SECRET"
        ]
        
        missing_vars = []
        for var in required_vars:
            if not getattr(settings, var, None):
                missing_vars.append(var)
        
        if missing_vars:
            issues.append(f"Missing required environment variables: {', '.join(missing_vars)}")
        
        # Check if running in production mode
        if settings.DEBUG:
            warnings.append("Debug mode is enabled")
        
        # Check secret key strength
        if len(settings.SECRET_KEY) < 32:
            issues.append("SECRET_KEY is too short")
        
        if settings.SECRET_KEY == "your-secret-key-here":
            issues.append("Default SECRET_KEY is being used")
        
        status = "passed" if not issues else "failed"
        
        return {
            "status": status,
            "message": f"Environment setup {'passed' if not issues else 'failed'}",
            "issues": issues,
            "warnings": warnings,
            "details": {
                "missing_variables": missing_vars,
                "debug_mode": settings.DEBUG,
                "environment": settings.ENVIRONMENT
            }
        }
    
    async def test_database(self) -> Dict[str, Any]:
        """Test database connectivity and performance"""
        try:
            from backend.app.core.database import get_db
            from sqlalchemy import text
            
            start_time = time.time()
            db = next(get_db())
            
            # Test basic connectivity
            result = db.execute(text("SELECT 1")).scalar()
            basic_latency = (time.time() - start_time) * 1000
            
            # Test query performance
            start_time = time.time()
            db.execute(text("SELECT COUNT(*) FROM information_schema.tables"))
            query_latency = (time.time() - start_time) * 1000
            
            # Check database size
            size_result = db.execute(text("SELECT pg_database_size(current_database())")).scalar()
            db_size_mb = size_result / (1024 * 1024)
            
            issues = []
            warnings = []
            
            if basic_latency > 1000:
                warnings.append(f"Database basic connectivity is slow: {basic_latency:.2f}ms")
            
            if query_latency > 2000:
                warnings.append(f"Database queries are slow: {query_latency:.2f}ms")
            
            if db_size_mb > 1000:
                warnings.append(f"Database size is large: {db_size_mb:.2f}MB")
            
            status = "passed" if not issues else "failed"
            
            return {
                "status": status,
                "message": "Database connectivity successful",
                "issues": issues,
                "warnings": warnings,
                "details": {
                    "basic_latency_ms": round(basic_latency, 2),
                    "query_latency_ms": round(query_latency, 2),
                    "database_size_mb": round(db_size_mb, 2)
                }
            }
            
        except Exception as e:
            return {
                "status": "failed",
                "message": f"Database test failed: {str(e)}",
                "issues": [str(e)],
                "warnings": [],
                "details": {"error": str(e)}
            }
    
    async def test_redis(self) -> Dict[str, Any]:
        """Test Redis connectivity and performance"""
        try:
            from backend.app.core.database import redis_client
            
            start_time = time.time()
            redis_client.ping()
            latency = (time.time() - start_time) * 1000
            
            # Test Redis operations
            start_time = time.time()
            redis_client.set("test_key", "test_value", ex=10)
            redis_client.get("test_key")
            redis_client.delete("test_key")
            operation_latency = (time.time() - start_time) * 1000
            
            issues = []
            warnings = []
            
            if latency > 100:
                warnings.append(f"Redis ping is slow: {latency:.2f}ms")
            
            if operation_latency > 500:
                warnings.append(f"Redis operations are slow: {operation_latency:.2f}ms")
            
            status = "passed" if not issues else "failed"
            
            return {
                "status": status,
                "message": "Redis connectivity successful",
                "issues": issues,
                "warnings": warnings,
                "details": {
                    "ping_latency_ms": round(latency, 2),
                    "operation_latency_ms": round(operation_latency, 2)
                }
            }
            
        except Exception as e:
            return {
                "status": "failed",
                "message": f"Redis test failed: {str(e)}",
                "issues": [str(e)],
                "warnings": [],
                "details": {"error": str(e)}
            }
    
    async def test_chromadb(self) -> Dict[str, Any]:
        """Test ChromaDB connectivity"""
        try:
            import httpx
            
            start_time = time.time()
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(f"{settings.CHROMA_URL}/api/v1/heartbeat")
                latency = (time.time() - start_time) * 1000
            
            issues = []
            warnings = []
            
            if response.status_code != 200:
                issues.append(f"ChromaDB returned status {response.status_code}")
            
            if latency > 1000:
                warnings.append(f"ChromaDB response is slow: {latency:.2f}ms")
            
            status = "passed" if not issues else "failed"
            
            return {
                "status": status,
                "message": "ChromaDB connectivity successful",
                "issues": issues,
                "warnings": warnings,
                "details": {
                    "status_code": response.status_code,
                    "response_latency_ms": round(latency, 2)
                }
            }
            
        except Exception as e:
            return {
                "status": "failed",
                "message": f"ChromaDB test failed: {str(e)}",
                "issues": [str(e)],
                "warnings": [],
                "details": {"error": str(e)}
            }
    
    async def test_api_endpoints(self) -> Dict[str, Any]:
        """Test API endpoints"""
        try:
            import httpx
            
            base_url = "http://localhost:8000"
            endpoints = [
                "/health",
                "/ready",
                "/metrics",
                "/status"
            ]
            
            results = {}
            issues = []
            warnings = []
            
            async with httpx.AsyncClient(timeout=10.0) as client:
                for endpoint in endpoints:
                    try:
                        start_time = time.time()
                        response = await client.get(f"{base_url}{endpoint}")
                        latency = (time.time() - start_time) * 1000
                        
                        results[endpoint] = {
                            "status_code": response.status_code,
                            "latency_ms": round(latency, 2),
                            "success": response.status_code == 200
                        }
                        
                        if response.status_code != 200:
                            issues.append(f"Endpoint {endpoint} returned status {response.status_code}")
                        
                        if latency > 1000:
                            warnings.append(f"Endpoint {endpoint} is slow: {latency:.2f}ms")
                            
                    except Exception as e:
                        issues.append(f"Endpoint {endpoint} failed: {str(e)}")
                        results[endpoint] = {
                            "status_code": None,
                            "latency_ms": None,
                            "success": False,
                            "error": str(e)
                        }
            
            status = "passed" if not issues else "failed"
            
            return {
                "status": status,
                "message": f"API endpoints test {'passed' if not issues else 'failed'}",
                "issues": issues,
                "warnings": warnings,
                "details": {"endpoints": results}
            }
            
        except Exception as e:
            return {
                "status": "failed",
                "message": f"API endpoints test failed: {str(e)}",
                "issues": [str(e)],
                "warnings": [],
                "details": {"error": str(e)}
            }
    
    async def test_security(self) -> Dict[str, Any]:
        """Test security configuration"""
        issues = []
        warnings = []
        
        # Check security headers
        try:
            import httpx
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get("http://localhost:8000/health")
                headers = response.headers
                
                security_headers = [
                    "X-Content-Type-Options",
                    "X-Frame-Options",
                    "X-XSS-Protection",
                    "Strict-Transport-Security"
                ]
                
                missing_headers = []
                for header in security_headers:
                    if header not in headers:
                        missing_headers.append(header)
                
                if missing_headers:
                    warnings.append(f"Missing security headers: {', '.join(missing_headers)}")
                
        except Exception as e:
            warnings.append(f"Could not check security headers: {str(e)}")
        
        # Check CORS configuration
        if "*" in settings.CORS_ORIGINS:
            issues.append("CORS is configured to allow all origins")
        
        # Check if rate limiting is enabled
        if not settings.ENABLE_RATE_LIMITING:
            warnings.append("Rate limiting is disabled")
        
        status = "passed" if not issues else "failed"
        
        return {
            "status": status,
            "message": f"Security test {'passed' if not issues else 'failed'}",
            "issues": issues,
            "warnings": warnings,
            "details": {
                "cors_origins": settings.CORS_ORIGINS,
                "rate_limiting_enabled": settings.ENABLE_RATE_LIMITING,
                "security_headers_enabled": settings.ENABLE_SECURITY_HEADERS
            }
        }
    
    async def test_performance(self) -> Dict[str, Any]:
        """Test performance metrics"""
        try:
            # Test memory usage
            memory = psutil.virtual_memory()
            memory_usage = memory.percent
            
            # Test CPU usage
            cpu_usage = psutil.cpu_percent(interval=1)
            
            # Test disk usage
            disk = psutil.disk_usage('/')
            disk_usage = disk.percent
            
            issues = []
            warnings = []
            
            if memory_usage > 80:
                warnings.append(f"High memory usage: {memory_usage}%")
            
            if cpu_usage > 80:
                warnings.append(f"High CPU usage: {cpu_usage}%")
            
            if disk_usage > 90:
                warnings.append(f"Low disk space: {disk_usage}% used")
            
            status = "passed" if not issues else "failed"
            
            return {
                "status": status,
                "message": "Performance test completed",
                "issues": issues,
                "warnings": warnings,
                "details": {
                    "memory_usage_percent": memory_usage,
                    "cpu_usage_percent": cpu_usage,
                    "disk_usage_percent": disk_usage
                }
            }
            
        except Exception as e:
            return {
                "status": "failed",
                "message": f"Performance test failed: {str(e)}",
                "issues": [str(e)],
                "warnings": [],
                "details": {"error": str(e)}
            }
    
    async def test_monitoring(self) -> Dict[str, Any]:
        """Test monitoring and metrics"""
        issues = []
        warnings = []
        
        # Check if monitoring is enabled
        if not settings.PROMETHEUS_ENABLED:
            warnings.append("Prometheus metrics are disabled")
        
        if not settings.METRICS_ENABLED:
            warnings.append("Metrics collection is disabled")
        
        if not settings.HEALTH_CHECK_ENABLED:
            warnings.append("Health checks are disabled")
        
        # Test metrics endpoint
        try:
            import httpx
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get("http://localhost:8000/metrics")
                if response.status_code != 200:
                    issues.append("Metrics endpoint is not working")
        except Exception as e:
            warnings.append(f"Could not test metrics endpoint: {str(e)}")
        
        status = "passed" if not issues else "failed"
        
        return {
            "status": status,
            "message": f"Monitoring test {'passed' if not issues else 'failed'}",
            "issues": issues,
            "warnings": warnings,
            "details": {
                "prometheus_enabled": settings.PROMETHEUS_ENABLED,
                "metrics_enabled": settings.METRICS_ENABLED,
                "health_check_enabled": settings.HEALTH_CHECK_ENABLED
            }
        }
    
    async def test_frontend(self) -> Dict[str, Any]:
        """Test frontend build and deployment"""
        try:
            # Check if frontend build exists
            frontend_build_path = "frontend/dist"
            if not os.path.exists(frontend_build_path):
                return {
                    "status": "failed",
                    "message": "Frontend build not found",
                    "issues": ["Frontend build directory does not exist"],
                    "warnings": [],
                    "details": {"build_path": frontend_build_path}
                }
            
            # Check if index.html exists
            index_path = os.path.join(frontend_build_path, "index.html")
            if not os.path.exists(index_path):
                return {
                    "status": "failed",
                    "message": "Frontend index.html not found",
                    "issues": ["index.html not found in build directory"],
                    "warnings": [],
                    "details": {"index_path": index_path}
                }
            
            return {
                "status": "passed",
                "message": "Frontend build is ready",
                "issues": [],
                "warnings": [],
                "details": {
                    "build_path": frontend_build_path,
                    "index_exists": True
                }
            }
            
        except Exception as e:
            return {
                "status": "failed",
                "message": f"Frontend test failed: {str(e)}",
                "issues": [str(e)],
                "warnings": [],
                "details": {"error": str(e)}
            }
    
    async def test_integrations(self) -> Dict[str, Any]:
        """Test external integrations"""
        issues = []
        warnings = []
        
        # Test Gemini API
        if settings.GEMINI_API_KEY:
            try:
                import httpx
                async with httpx.AsyncClient(timeout=10.0) as client:
                    response = await client.get(
                        "https://generativelanguage.googleapis.com/v1beta/models",
                        params={"key": settings.GEMINI_API_KEY}
                    )
                    if response.status_code != 200:
                        issues.append(f"Gemini API returned status {response.status_code}")
            except Exception as e:
                warnings.append(f"Gemini API test failed: {str(e)}")
        else:
            warnings.append("Gemini API key not configured")
        
        # Test Stripe API
        if settings.STRIPE_API_KEY:
            try:
                import stripe
                stripe.api_key = settings.STRIPE_API_KEY
                # Test API key validity
                stripe.Account.retrieve()
            except Exception as e:
                warnings.append(f"Stripe API test failed: {str(e)}")
        else:
            warnings.append("Stripe API key not configured")
        
        status = "passed" if not issues else "failed"
        
        return {
            "status": status,
            "message": f"Integrations test {'passed' if not issues else 'failed'}",
            "issues": issues,
            "warnings": warnings,
            "details": {
                "gemini_configured": bool(settings.GEMINI_API_KEY),
                "stripe_configured": bool(settings.STRIPE_API_KEY)
            }
        }
    
    async def test_docker(self) -> Dict[str, Any]:
        """Test Docker configuration"""
        try:
            # Check if Docker is available
            result = subprocess.run(["docker", "--version"], capture_output=True, text=True)
            if result.returncode != 0:
                return {
                    "status": "failed",
                    "message": "Docker is not available",
                    "issues": ["Docker command failed"],
                    "warnings": [],
                    "details": {"docker_output": result.stderr}
                }
            
            # Check if docker-compose is available
            result = subprocess.run(["docker-compose", "--version"], capture_output=True, text=True)
            if result.returncode != 0:
                return {
                    "status": "failed",
                    "message": "Docker Compose is not available",
                    "issues": ["Docker Compose command failed"],
                    "warnings": [],
                    "details": {"docker_compose_output": result.stderr}
                }
            
            return {
                "status": "passed",
                "message": "Docker configuration is ready",
                "issues": [],
                "warnings": [],
                "details": {
                    "docker_version": result.stdout.strip(),
                    "docker_compose_version": result.stdout.strip()
                }
            }
            
        except Exception as e:
            return {
                "status": "failed",
                "message": f"Docker test failed: {str(e)}",
                "issues": [str(e)],
                "warnings": [],
                "details": {"error": str(e)}
            }
    
    async def test_production_validation(self) -> Dict[str, Any]:
        """Test production validation using the validator"""
        try:
            validation_result = await production_validator.validate_all()
            
            issues = validation_result.get("critical_failures", [])
            warnings = validation_result.get("warnings", [])
            
            status = "passed" if not issues else "failed"
            
            return {
                "status": status,
                "message": f"Production validation {'passed' if not issues else 'failed'}",
                "issues": issues,
                "warnings": warnings,
                "details": validation_result
            }
            
        except Exception as e:
            return {
                "status": "failed",
                "message": f"Production validation failed: {str(e)}",
                "issues": [str(e)],
                "warnings": [],
                "details": {"error": str(e)}
            }
    
    def update_summary(self, result: Dict[str, Any]):
        """Update test summary"""
        self.results["summary"]["total_tests"] += 1
        
        if result["status"] == "passed":
            self.results["summary"]["passed"] += 1
        elif result["status"] == "failed":
            self.results["summary"]["failed"] += 1
        else:
            self.results["summary"]["warnings"] += 1
    
    def determine_overall_status(self):
        """Determine overall test status"""
        if self.results["summary"]["failed"] > 0:
            self.results["overall_status"] = "failed"
        elif self.results["summary"]["warnings"] > 0:
            self.results["overall_status"] = "warning"
        else:
            self.results["overall_status"] = "passed"
    
    def print_test_result(self, category: str, result: Dict[str, Any]):
        """Print test result"""
        status_emoji = {
            "passed": "✅",
            "failed": "❌",
            "warning": "⚠️"
        }
        
        emoji = status_emoji.get(result["status"], "❓")
        print(f"  {emoji} {result['message']}")
        
        if result.get("issues"):
            for issue in result["issues"]:
                print(f"    ❌ {issue}")
        
        if result.get("warnings"):
            for warning in result["warnings"]:
                print(f"    ⚠️ {warning}")
    
    def print_final_summary(self):
        """Print final test summary"""
        print("\n" + "=" * 60)
        print("📊 FINAL PRODUCTION READINESS SUMMARY")
        print("=" * 60)
        
        summary = self.results["summary"]
        print(f"Total Tests: {summary['total_tests']}")
        print(f"✅ Passed: {summary['passed']}")
        print(f"❌ Failed: {summary['failed']}")
        print(f"⚠️ Warnings: {summary['warnings']}")
        
        overall_status = self.results["overall_status"]
        status_emoji = {
            "passed": "✅",
            "failed": "❌",
            "warning": "⚠️"
        }
        
        print(f"\nOverall Status: {status_emoji.get(overall_status, '❓')} {overall_status.upper()}")
        
        if overall_status == "passed":
            print("\n🎉 CONGRATULATIONS! Your application is PRODUCTION READY!")
        elif overall_status == "warning":
            print("\n⚠️ Your application is mostly ready but has some warnings to address.")
        else:
            print("\n❌ Your application is NOT ready for production. Please fix the critical issues.")
        
        # Save results to file
        with open("production_readiness_results.json", "w") as f:
            json.dump(self.results, f, indent=2)
        
        print(f"\n📄 Detailed results saved to: production_readiness_results.json")

async def main():
    """Main function"""
    tester = ProductionReadinessTester()
    results = await tester.run_all_tests()
    
    # Exit with appropriate code
    if results["overall_status"] == "failed":
        sys.exit(1)
    elif results["overall_status"] == "warning":
        sys.exit(2)
    else:
        sys.exit(0)

if __name__ == "__main__":
    asyncio.run(main())
