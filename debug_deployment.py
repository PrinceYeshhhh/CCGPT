#!/usr/bin/env python3
"""
Debug script for CustomerCareGPT deployment
Tests all endpoints and services to identify issues
"""

import asyncio
import aiohttp
import json
import time
from datetime import datetime
from typing import Dict, Any, List

class DeploymentDebugger:
    """Debug deployment issues"""
    
    def __init__(self, frontend_url: str, backend_url: str):
        self.frontend_url = frontend_url
        self.backend_url = backend_url
        self.results = {
            "timestamp": datetime.utcnow().isoformat(),
            "frontend_url": frontend_url,
            "backend_url": backend_url,
            "tests": {},
            "errors": [],
            "warnings": []
        }
    
    async def test_frontend(self):
        """Test frontend deployment"""
        print("🌐 Testing Frontend...")
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(self.frontend_url, timeout=10) as response:
                    if response.status == 200:
                        self.results["tests"]["frontend"] = {
                            "status": "success",
                            "message": "Frontend is accessible",
                            "status_code": response.status
                        }
                        print("✅ Frontend is accessible")
                    else:
                        self.results["tests"]["frontend"] = {
                            "status": "error",
                            "message": f"Frontend returned status {response.status}",
                            "status_code": response.status
                        }
                        self.results["errors"].append(f"Frontend returned status {response.status}")
                        print(f"❌ Frontend returned status {response.status}")
        except Exception as e:
            self.results["tests"]["frontend"] = {
                "status": "error",
                "message": str(e)
            }
            self.results["errors"].append(f"Frontend error: {str(e)}")
            print(f"❌ Frontend error: {str(e)}")
    
    async def test_backend_health(self):
        """Test backend health endpoint"""
        print("🏥 Testing Backend Health...")
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.backend_url}/health", timeout=10) as response:
                    if response.status == 200:
                        data = await response.json()
                        self.results["tests"]["backend_health"] = {
                            "status": "success",
                            "message": "Backend health check passed",
                            "status_code": response.status,
                            "data": data
                        }
                        print("✅ Backend health check passed")
                    else:
                        self.results["tests"]["backend_health"] = {
                            "status": "error",
                            "message": f"Backend health returned status {response.status}",
                            "status_code": response.status
                        }
                        self.results["errors"].append(f"Backend health returned status {response.status}")
                        print(f"❌ Backend health returned status {response.status}")
        except Exception as e:
            self.results["tests"]["backend_health"] = {
                "status": "error",
                "message": str(e)
            }
            self.results["errors"].append(f"Backend health error: {str(e)}")
            print(f"❌ Backend health error: {str(e)}")
    
    async def test_backend_api(self):
        """Test backend API endpoints"""
        print("🔌 Testing Backend API...")
        
        endpoints = [
            ("/api/v1/", "API Root"),
            ("/api/v1/auth/", "Auth Endpoint"),
            ("/api/v1/documents/", "Documents Endpoint"),
            ("/api/v1/chat/", "Chat Endpoint"),
            ("/api/v1/embed/", "Embed Endpoint")
        ]
        
        async with aiohttp.ClientSession() as session:
            for endpoint, name in endpoints:
                try:
                    url = f"{self.backend_url}{endpoint}"
                    async with session.get(url, timeout=10) as response:
                        if response.status in [200, 401, 403]:  # 401/403 are expected for protected endpoints
                            self.results["tests"][f"api_{name.lower().replace(' ', '_')}"] = {
                                "status": "success",
                                "message": f"{name} is accessible",
                                "status_code": response.status,
                                "url": url
                            }
                            print(f"✅ {name} is accessible (status {response.status})")
                        else:
                            self.results["tests"][f"api_{name.lower().replace(' ', '_')}"] = {
                                "status": "error",
                                "message": f"{name} returned status {response.status}",
                                "status_code": response.status,
                                "url": url
                            }
                            self.results["errors"].append(f"{name} returned status {response.status}")
                            print(f"❌ {name} returned status {response.status}")
                except Exception as e:
                    self.results["tests"][f"api_{name.lower().replace(' ', '_')}"] = {
                        "status": "error",
                        "message": str(e),
                        "url": url
                    }
                    self.results["errors"].append(f"{name} error: {str(e)}")
                    print(f"❌ {name} error: {str(e)}")
    
    async def test_cors(self):
        """Test CORS configuration"""
        print("🔒 Testing CORS...")
        
        try:
            async with aiohttp.ClientSession() as session:
                headers = {
                    "Origin": self.frontend_url,
                    "Access-Control-Request-Method": "GET",
                    "Access-Control-Request-Headers": "X-Requested-With"
                }
                
                async with session.options(f"{self.backend_url}/api/v1/", headers=headers, timeout=10) as response:
                    cors_headers = {
                        "access-control-allow-origin": response.headers.get("access-control-allow-origin"),
                        "access-control-allow-methods": response.headers.get("access-control-allow-methods"),
                        "access-control-allow-headers": response.headers.get("access-control-allow-headers")
                    }
                    
                    if response.status == 200 and cors_headers["access-control-allow-origin"]:
                        self.results["tests"]["cors"] = {
                            "status": "success",
                            "message": "CORS is properly configured",
                            "status_code": response.status,
                            "headers": cors_headers
                        }
                        print("✅ CORS is properly configured")
                    else:
                        self.results["tests"]["cors"] = {
                            "status": "error",
                            "message": "CORS is not properly configured",
                            "status_code": response.status,
                            "headers": cors_headers
                        }
                        self.results["errors"].append("CORS is not properly configured")
                        print("❌ CORS is not properly configured")
        except Exception as e:
            self.results["tests"]["cors"] = {
                "status": "error",
                "message": str(e)
            }
            self.results["errors"].append(f"CORS error: {str(e)}")
            print(f"❌ CORS error: {str(e)}")
    
    async def test_debug_endpoints(self):
        """Test debug endpoints"""
        print("🐛 Testing Debug Endpoints...")
        
        debug_endpoints = [
            ("/debug/health", "Debug Health"),
            ("/debug/errors", "Error Summary"),
            ("/debug/test-connectivity", "Connectivity Test")
        ]
        
        async with aiohttp.ClientSession() as session:
            for endpoint, name in debug_endpoints:
                try:
                    url = f"{self.backend_url}{endpoint}"
                    async with session.get(url, timeout=10) as response:
                        if response.status == 200:
                            data = await response.json()
                            self.results["tests"][f"debug_{name.lower().replace(' ', '_')}"] = {
                                "status": "success",
                                "message": f"{name} is accessible",
                                "status_code": response.status,
                                "data": data
                            }
                            print(f"✅ {name} is accessible")
                        else:
                            self.results["tests"][f"debug_{name.lower().replace(' ', '_')}"] = {
                                "status": "error",
                                "message": f"{name} returned status {response.status}",
                                "status_code": response.status
                            }
                            self.results["errors"].append(f"{name} returned status {response.status}")
                            print(f"❌ {name} returned status {response.status}")
                except Exception as e:
                    self.results["tests"][f"debug_{name.lower().replace(' ', '_')}"] = {
                        "status": "error",
                        "message": str(e)
                    }
                    self.results["errors"].append(f"{name} error: {str(e)}")
                    print(f"❌ {name} error: {str(e)}")
    
    async def run_all_tests(self):
        """Run all tests"""
        print("🚀 Starting Deployment Debug Tests")
        print("=" * 50)
        
        await self.test_frontend()
        await self.test_backend_health()
        await self.test_backend_api()
        await self.test_cors()
        await self.test_debug_endpoints()
        
        # Calculate overall status
        successful_tests = sum(1 for test in self.results["tests"].values() if test["status"] == "success")
        total_tests = len(self.results["tests"])
        
        if successful_tests == total_tests:
            self.results["overall_status"] = "healthy"
            print("\n🎉 All tests passed! Your deployment is healthy!")
        elif successful_tests > total_tests // 2:
            self.results["overall_status"] = "partial"
            print(f"\n⚠️ {successful_tests}/{total_tests} tests passed. Some issues found.")
        else:
            self.results["overall_status"] = "unhealthy"
            print(f"\n❌ Only {successful_tests}/{total_tests} tests passed. Major issues found.")
        
        # Save results
        with open("deployment_debug_results.json", "w") as f:
            json.dump(self.results, f, indent=2)
        
        print(f"\n📄 Detailed results saved to: deployment_debug_results.json")
        
        return self.results

async def main():
    """Main function"""
    # Update these URLs with your actual deployment URLs
    frontend_url = "https://customercaregpt-frontend.vercel.app"
    backend_url = "https://customercaregpt-backend-xxxxx-uc.a.run.app"
    
    debugger = DeploymentDebugger(frontend_url, backend_url)
    results = await debugger.run_all_tests()
    
    # Print summary
    print("\n" + "=" * 50)
    print("📊 DEBUG SUMMARY")
    print("=" * 50)
    print(f"Overall Status: {results['overall_status']}")
    print(f"Total Tests: {len(results['tests'])}")
    print(f"Errors: {len(results['errors'])}")
    print(f"Warnings: {len(results['warnings'])}")
    
    if results['errors']:
        print("\n❌ ERRORS FOUND:")
        for error in results['errors']:
            print(f"  - {error}")
    
    if results['warnings']:
        print("\n⚠️ WARNINGS:")
        for warning in results['warnings']:
            print(f"  - {warning}")

if __name__ == "__main__":
    asyncio.run(main())
