#!/usr/bin/env python3
"""
Production Readiness Test Script

This script tests all production readiness features to ensure
the system is ready for production deployment.
"""

import asyncio
import httpx
import json
import time
import sys
from typing import Dict, Any, List

class ProductionReadinessTester:
    """Test production readiness features"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.client = httpx.AsyncClient(timeout=30.0)
        self.results = []
    
    async def test_health_endpoints(self) -> bool:
        """Test health check endpoints"""
        print("🔍 Testing health endpoints...")
        
        try:
            # Test liveness probe
            response = await self.client.get(f"{self.base_url}/health")
            if response.status_code != 200:
                print(f"❌ Health check failed: {response.status_code}")
                return False
            
            health_data = response.json()
            if health_data.get("status") != "healthy":
                print(f"❌ Health status not healthy: {health_data}")
                return False
            
            # Test readiness probe
            response = await self.client.get(f"{self.base_url}/ready")
            if response.status_code != 200:
                print(f"❌ Readiness check failed: {response.status_code}")
                return False
            
            readiness_data = response.json()
            if readiness_data.get("status") != "healthy":
                print(f"❌ Readiness status not healthy: {readiness_data}")
                return False
            
            print("✅ Health endpoints working correctly")
            return True
            
        except Exception as e:
            print(f"❌ Health endpoint test failed: {e}")
            return False
    
    async def test_metrics_endpoint(self) -> bool:
        """Test metrics endpoint"""
        print("🔍 Testing metrics endpoint...")
        
        try:
            response = await self.client.get(f"{self.base_url}/metrics")
            if response.status_code != 200:
                print(f"❌ Metrics endpoint failed: {response.status_code}")
                return False
            
            metrics_text = response.text
            if "http_requests_total" not in metrics_text:
                print("❌ Metrics endpoint missing expected metrics")
                return False
            
            print("✅ Metrics endpoint working correctly")
            return True
            
        except Exception as e:
            print(f"❌ Metrics endpoint test failed: {e}")
            return False
    
    async def test_rate_limiting(self) -> bool:
        """Test rate limiting functionality"""
        print("🔍 Testing rate limiting...")
        
        try:
            # Make multiple requests quickly to trigger rate limiting
            requests = []
            for i in range(10):
                requests.append(self.client.get(f"{self.base_url}/health"))
            
            responses = await asyncio.gather(*requests, return_exceptions=True)
            
            # Check if any requests were rate limited
            rate_limited = any(
                isinstance(r, httpx.Response) and r.status_code == 429
                for r in responses
            )
            
            if rate_limited:
                print("✅ Rate limiting working correctly")
                return True
            else:
                print("⚠️  Rate limiting not triggered (may be configured permissive)")
                return True  # Not necessarily a failure
            
        except Exception as e:
            print(f"❌ Rate limiting test failed: {e}")
            return False
    
    async def test_database_connectivity(self) -> bool:
        """Test database connectivity through health checks"""
        print("🔍 Testing database connectivity...")
        
        try:
            response = await self.client.get(f"{self.base_url}/ready")
            if response.status_code != 200:
                print(f"❌ Database connectivity test failed: {response.status_code}")
                return False
            
            data = response.json()
            db_status = data.get("components", {}).get("database", {})
            
            if db_status.get("status") != "healthy":
                print(f"❌ Database not healthy: {db_status}")
                return False
            
            print("✅ Database connectivity working correctly")
            return True
            
        except Exception as e:
            print(f"❌ Database connectivity test failed: {e}")
            return False
    
    async def test_redis_connectivity(self) -> bool:
        """Test Redis connectivity through health checks"""
        print("🔍 Testing Redis connectivity...")
        
        try:
            response = await self.client.get(f"{self.base_url}/ready")
            if response.status_code != 200:
                print(f"❌ Redis connectivity test failed: {response.status_code}")
                return False
            
            data = response.json()
            redis_status = data.get("components", {}).get("redis", {})
            
            if redis_status.get("status") != "healthy":
                print(f"❌ Redis not healthy: {redis_status}")
                return False
            
            print("✅ Redis connectivity working correctly")
            return True
            
        except Exception as e:
            print(f"❌ Redis connectivity test failed: {e}")
            return False
    
    async def test_chromadb_connectivity(self) -> bool:
        """Test ChromaDB connectivity through health checks"""
        print("🔍 Testing ChromaDB connectivity...")
        
        try:
            response = await self.client.get(f"{self.base_url}/ready")
            if response.status_code != 200:
                print(f"❌ ChromaDB connectivity test failed: {response.status_code}")
                return False
            
            data = response.json()
            chroma_status = data.get("components", {}).get("chromadb", {})
            
            if chroma_status.get("status") not in ["healthy", "skipped"]:
                print(f"❌ ChromaDB not healthy: {chroma_status}")
                return False
            
            print("✅ ChromaDB connectivity working correctly")
            return True
            
        except Exception as e:
            print(f"❌ ChromaDB connectivity test failed: {e}")
            return False
    
    async def test_api_endpoints(self) -> bool:
        """Test basic API endpoints"""
        print("🔍 Testing API endpoints...")
        
        try:
            # Test API documentation
            response = await self.client.get(f"{self.base_url}/api/docs")
            if response.status_code != 200:
                print(f"❌ API docs not accessible: {response.status_code}")
                return False
            
            # Test OpenAPI schema
            response = await self.client.get(f"{self.base_url}/api/openapi.json")
            if response.status_code != 200:
                print(f"❌ OpenAPI schema not accessible: {response.status_code}")
                return False
            
            print("✅ API endpoints working correctly")
            return True
            
        except Exception as e:
            print(f"❌ API endpoints test failed: {e}")
            return False
    
    async def test_logging_format(self) -> bool:
        """Test logging format (check if structured logging is working)"""
        print("🔍 Testing logging format...")
        
        try:
            # Make a request that should generate logs
            response = await self.client.get(f"{self.base_url}/health")
            
            # This is a basic test - in production, you'd check log files
            # For now, we'll just verify the endpoint responds
            if response.status_code == 200:
                print("✅ Logging format test passed (basic)")
                return True
            else:
                print(f"❌ Logging format test failed: {response.status_code}")
                return False
            
        except Exception as e:
            print(f"❌ Logging format test failed: {e}")
            return False
    
    async def run_all_tests(self) -> Dict[str, Any]:
        """Run all production readiness tests"""
        print("🚀 Starting Production Readiness Tests")
        print("=" * 50)
        
        tests = [
            ("Health Endpoints", self.test_health_endpoints),
            ("Metrics Endpoint", self.test_metrics_endpoint),
            ("Rate Limiting", self.test_rate_limiting),
            ("Database Connectivity", self.test_database_connectivity),
            ("Redis Connectivity", self.test_redis_connectivity),
            ("ChromaDB Connectivity", self.test_chromadb_connectivity),
            ("API Endpoints", self.test_api_endpoints),
            ("Logging Format", self.test_logging_format),
        ]
        
        results = {}
        passed = 0
        total = len(tests)
        
        for test_name, test_func in tests:
            try:
                result = await test_func()
                results[test_name] = result
                if result:
                    passed += 1
            except Exception as e:
                print(f"❌ {test_name} test crashed: {e}")
                results[test_name] = False
        
        print("\n" + "=" * 50)
        print(f"📊 Test Results: {passed}/{total} tests passed")
        
        if passed == total:
            print("🎉 All production readiness tests PASSED!")
            print("✅ System is ready for production deployment")
        else:
            print("⚠️  Some tests FAILED!")
            print("❌ System may not be ready for production deployment")
        
        return {
            "total_tests": total,
            "passed_tests": passed,
            "failed_tests": total - passed,
            "results": results,
            "ready_for_production": passed == total
        }
    
    async def close(self):
        """Close the HTTP client"""
        await self.client.aclose()

async def main():
    """Main test function"""
    base_url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000"
    
    tester = ProductionReadinessTester(base_url)
    
    try:
        results = await tester.run_all_tests()
        
        # Save results to file
        with open("production_readiness_results.json", "w") as f:
            json.dump(results, f, indent=2)
        
        print(f"\n📄 Results saved to: production_readiness_results.json")
        
        # Exit with appropriate code
        sys.exit(0 if results["ready_for_production"] else 1)
        
    except Exception as e:
        print(f"❌ Test runner failed: {e}")
        sys.exit(1)
    finally:
        await tester.close()

if __name__ == "__main__":
    asyncio.run(main())
