"""
Cloud Performance Tests
Tests the performance of cloud backend from local machine
"""
import asyncio
import time
import statistics
import httpx
import os
from typing import List, Dict, Any
import json

# Cloud URLs
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")
API_V1_URL = f"{BACKEND_URL}/api/v1"

class CloudPerformanceTester:
    """Performance tester for cloud backend"""
    
    def __init__(self, base_url: str = API_V1_URL):
        self.base_url = base_url
        self.session = httpx.AsyncClient(timeout=60.0)
        self.results: List[Dict[str, Any]] = []
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.session.aclose()
    
    async def measure_endpoint(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Measure performance of a single endpoint"""
        url = f"{self.base_url}{endpoint}" if endpoint.startswith("/") else f"{self.base_url}/{endpoint}"
        
        start_time = time.time()
        try:
            if method.upper() == "GET":
                response = await self.session.get(url, **kwargs)
            elif method.upper() == "POST":
                response = await self.session.post(url, **kwargs)
            elif method.upper() == "PUT":
                response = await self.session.put(url, **kwargs)
            elif method.upper() == "DELETE":
                response = await self.session.delete(url, **kwargs)
            else:
                raise ValueError(f"Unsupported method: {method}")
            
            end_time = time.time()
            response_time = end_time - start_time
            
            result = {
                "method": method.upper(),
                "endpoint": endpoint,
                "status_code": response.status_code,
                "response_time": response_time,
                "success": 200 <= response.status_code < 400,
                "timestamp": start_time
            }
            
            self.results.append(result)
            return result
            
        except Exception as e:
            end_time = time.time()
            response_time = end_time - start_time
            
            result = {
                "method": method.upper(),
                "endpoint": endpoint,
                "status_code": 0,
                "response_time": response_time,
                "success": False,
                "error": str(e),
                "timestamp": start_time
            }
            
            self.results.append(result)
            return result
    
    async def load_test_endpoint(self, method: str, endpoint: str, concurrent_requests: int = 10, **kwargs) -> Dict[str, Any]:
        """Run load test on an endpoint"""
        print(f"🔄 Load testing {method} {endpoint} with {concurrent_requests} concurrent requests...")
        
        async def single_request():
            return await self.measure_endpoint(method, endpoint, **kwargs)
        
        # Run concurrent requests
        tasks = [single_request() for _ in range(concurrent_requests)]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filter out exceptions
        valid_results = [r for r in results if isinstance(r, dict)]
        
        if not valid_results:
            return {"error": "All requests failed"}
        
        # Calculate statistics
        response_times = [r["response_time"] for r in valid_results]
        success_count = sum(1 for r in valid_results if r["success"])
        
        stats = {
            "total_requests": len(valid_results),
            "successful_requests": success_count,
            "failed_requests": len(valid_results) - success_count,
            "success_rate": success_count / len(valid_results) * 100,
            "avg_response_time": statistics.mean(response_times),
            "min_response_time": min(response_times),
            "max_response_time": max(response_times),
            "median_response_time": statistics.median(response_times),
            "p95_response_time": self.percentile(response_times, 95),
            "p99_response_time": self.percentile(response_times, 99)
        }
        
        return stats
    
    def percentile(self, data: List[float], percentile: float) -> float:
        """Calculate percentile"""
        sorted_data = sorted(data)
        index = int((percentile / 100) * len(sorted_data))
        return sorted_data[min(index, len(sorted_data) - 1)]
    
    def generate_report(self) -> str:
        """Generate performance report"""
        if not self.results:
            return "No test results available."
        
        total_tests = len(self.results)
        successful_tests = sum(1 for r in self.results if r["success"])
        failed_tests = total_tests - successful_tests
        
        response_times = [r["response_time"] for r in self.results if r["success"]]
        
        report = f"""
🌐 Cloud Performance Test Report
===============================
Backend URL: {BACKEND_URL}
Total Tests: {total_tests}
Successful: {successful_tests}
Failed: {failed_tests}
Success Rate: {successful_tests/total_tests*100:.1f}%

Response Time Statistics:
- Average: {statistics.mean(response_times):.3f}s
- Median: {statistics.median(response_times):.3f}s
- Min: {min(response_times):.3f}s
- Max: {max(response_times):.3f}s
- P95: {self.percentile(response_times, 95):.3f}s
- P99: {self.percentile(response_times, 99):.3f}s

Detailed Results:
"""
        
        for result in self.results:
            status = "✅" if result["success"] else "❌"
            report += f"{status} {result['method']} {result['endpoint']} - {result['response_time']:.3f}s - {result['status_code']}\n"
        
        return report

async def test_health_endpoints(tester: CloudPerformanceTester):
    """Test health endpoints performance"""
    print("🏥 Testing Health Endpoints...")
    
    # Test basic health
    await tester.measure_endpoint("GET", "/health")
    
    # Test readiness
    await tester.measure_endpoint("GET", "/ready")
    
    # Test detailed health
    await tester.measure_endpoint("GET", "/health/detailed")

async def test_auth_endpoints(tester: CloudPerformanceTester):
    """Test authentication endpoints performance"""
    print("🔐 Testing Authentication Endpoints...")
    
    # Test registration
    timestamp = int(time.time())
    user_data = {
        "email": f"perf_test_{timestamp}@example.com",
        "password": "SecurePassword123!",
        "full_name": "Performance Test User"
    }
    
    await tester.measure_endpoint("POST", "/auth/register", json=user_data)
    
    # Test login
    login_data = {
        "email": f"perf_test_{timestamp}@example.com",
        "password": "SecurePassword123!"
    }
    
    await tester.measure_endpoint("POST", "/auth/login", json=login_data)

async def test_api_endpoints(tester: CloudPerformanceTester):
    """Test API endpoints performance"""
    print("📡 Testing API Endpoints...")
    
    # Test public endpoints (no auth required)
    await tester.measure_endpoint("GET", "/health")
    await tester.measure_endpoint("GET", "/ready")
    
    # Test protected endpoints (will return 401, but we measure response time)
    await tester.measure_endpoint("GET", "/workspaces/")
    await tester.measure_endpoint("GET", "/documents/")

async def run_load_tests(tester: CloudPerformanceTester):
    """Run load tests"""
    print("🚀 Running Load Tests...")
    
    # Load test health endpoint
    health_stats = await tester.load_test_endpoint("GET", "/health", concurrent_requests=20)
    print(f"Health endpoint load test: {health_stats}")
    
    # Load test auth endpoint
    timestamp = int(time.time())
    user_data = {
        "email": f"load_test_{timestamp}@example.com",
        "password": "SecurePassword123!",
        "full_name": "Load Test User"
    }
    
    auth_stats = await tester.load_test_endpoint("POST", "/auth/register", concurrent_requests=10, json=user_data)
    print(f"Auth endpoint load test: {auth_stats}")

async def test_concurrent_health_checks(tester: CloudPerformanceTester):
    """Test concurrent health checks"""
    print("🔄 Testing Concurrent Health Checks...")
    
    async def health_check():
        return await tester.measure_endpoint("GET", "/health")
    
    # Run 50 concurrent health checks
    tasks = [health_check() for _ in range(50)]
    results = await asyncio.gather(*tasks)
    
    successful = sum(1 for r in results if r["success"])
    response_times = [r["response_time"] for r in results if r["success"]]
    
    print(f"Concurrent health checks: {successful}/50 successful")
    if response_times:
        print(f"Average response time: {statistics.mean(response_times):.3f}s")
        print(f"Max response time: {max(response_times):.3f}s")

async def test_error_handling_performance(tester: CloudPerformanceTester):
    """Test error handling performance"""
    print("⚠️ Testing Error Handling Performance...")
    
    # Test 404 errors
    await tester.measure_endpoint("GET", "/nonexistent/endpoint")
    
    # Test 422 errors (malformed JSON)
    await tester.measure_endpoint("POST", "/auth/register", content="invalid json")
    
    # Test 401 errors
    await tester.measure_endpoint("GET", "/workspaces/")

async def main():
    """Run all performance tests"""
    print("🌐 Cloud Performance Testing Suite")
    print("=" * 50)
    print(f"Backend URL: {BACKEND_URL}")
    print(f"API URL: {API_V1_URL}")
    print("=" * 50)
    
    async with CloudPerformanceTester() as tester:
        # Run individual tests
        await test_health_endpoints(tester)
        await test_auth_endpoints(tester)
        await test_api_endpoints(tester)
        await test_error_handling_performance(tester)
        
        # Run load tests
        await run_load_tests(tester)
        
        # Run concurrent tests
        await test_concurrent_health_checks(tester)
        
        # Generate and print report
        report = tester.generate_report()
        print(report)
        
        # Save report to file
        with open("cloud_performance_report.txt", "w") as f:
            f.write(report)
        
        print("📊 Performance report saved to cloud_performance_report.txt")

if __name__ == "__main__":
    asyncio.run(main())
