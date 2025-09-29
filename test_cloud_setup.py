#!/usr/bin/env python3
"""
Comprehensive Cloud Testing Setup
Tests your deployed cloud backend from local machine
"""
import asyncio
import os
import sys
import time
import json
from pathlib import Path
from typing import Dict, Any, List

# Add backend to path
backend_path = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_path))

# Import test modules
from backend.tests.test_cloud_integration import CloudTestClient

class CloudTestRunner:
    """Comprehensive cloud test runner"""
    
    def __init__(self, environment: str = "production"):
        self.environment = environment
        self.backend_url = self._get_backend_url()
        self.frontend_url = self._get_frontend_url()
        self.results: Dict[str, Any] = {}
        
    def _get_backend_url(self) -> str:
        """Get backend URL based on environment"""
        if self.environment == "staging":
            return "https://customercaregpt-backend-staging-xxxxx-uc.a.run.app"
        else:
            return "https://customercaregpt-backend-xxxxx-uc.a.run.app"
    
    def _get_frontend_url(self) -> str:
        """Get frontend URL based on environment"""
        if self.environment == "staging":
            return "https://customercaregpt-frontend-staging.vercel.app"
        else:
            return "https://customercaregpt-frontend.vercel.app"
    
    def print_banner(self):
        """Print test banner"""
        print("🌐 CustomerCareGPT Cloud Testing Suite")
        print("=" * 60)
        print(f"Environment: {self.environment.upper()}")
        print(f"Backend URL: {self.backend_url}")
        print(f"Frontend URL: {self.frontend_url}")
        print("=" * 60)
    
    async def test_connectivity(self) -> bool:
        """Test basic connectivity to cloud backend"""
        print("\n🔗 Testing Connectivity...")
        print("-" * 30)
        
        try:
            async with CloudTestClient() as client:
                result, status = await client.get_health()
                
                if status == 200:
                    print("✅ Backend is reachable and healthy")
                    print(f"   Status: {result['status']}")
                    print(f"   Timestamp: {result.get('timestamp', 'N/A')}")
                    return True
                else:
                    print(f"❌ Backend returned status {status}")
                    print(f"   Response: {result}")
                    return False
                    
        except Exception as e:
            print(f"❌ Failed to connect to backend: {e}")
            return False
    
    async def test_authentication_flow(self) -> bool:
        """Test complete authentication flow"""
        print("\n🔐 Testing Authentication Flow...")
        print("-" * 30)
        
        try:
            async with CloudTestClient() as client:
                # Test registration
                timestamp = int(time.time())
                email = f"cloud_test_{timestamp}@example.com"
                password = "SecurePassword123!"
                full_name = "Cloud Test User"
                
                print(f"   Registering user: {email}")
                result, status = await client.register_user(email, password, full_name)
                
                if status not in [201, 409]:  # 409 = user already exists
                    print(f"❌ Registration failed: {result}")
                    return False
                
                print("✅ User registration successful")
                
                # Test login
                print(f"   Logging in user: {email}")
                result, status = await client.login_user(email, password)
                
                if status != 200:
                    print(f"❌ Login failed: {result}")
                    return False
                
                print("✅ User login successful")
                print(f"   Token type: {result.get('token_type', 'N/A')}")
                
                return True
                
        except Exception as e:
            print(f"❌ Authentication flow failed: {e}")
            return False
    
    async def test_core_functionality(self) -> bool:
        """Test core application functionality"""
        print("\n⚙️ Testing Core Functionality...")
        print("-" * 30)
        
        try:
            async with CloudTestClient() as client:
                # Authenticate first
                timestamp = int(time.time())
                email = f"core_test_{timestamp}@example.com"
                password = "SecurePassword123!"
                full_name = "Core Test User"
                
                await client.register_user(email, password, full_name)
                await client.login_user(email, password)
                
                # Test workspace creation
                print("   Creating workspace...")
                result, status = await client.create_workspace("Test Workspace", "Test Description")
                
                if status != 201:
                    print(f"❌ Workspace creation failed: {result}")
                    return False
                
                print("✅ Workspace creation successful")
                workspace_id = result["id"]
                
                # Test document upload
                print("   Uploading document...")
                content = "This is a test document for cloud integration testing."
                result, status = await client.upload_document(workspace_id, content, "test.txt")
                
                if status != 201:
                    print(f"❌ Document upload failed: {result}")
                    return False
                
                print("✅ Document upload successful")
                
                # Test chat functionality
                print("   Testing chat...")
                result, status = await client.send_chat_message(workspace_id, "Hello, this is a test message.")
                
                if status != 200:
                    print(f"❌ Chat message failed: {result}")
                    return False
                
                print("✅ Chat functionality working")
                
                return True
                
        except Exception as e:
            print(f"❌ Core functionality test failed: {e}")
            return False
    
    async def run_integration_tests(self) -> bool:
        """Run comprehensive integration tests"""
        print("\n🔗 Running Integration Tests...")
        print("-" * 30)
        
        try:
            # Set environment variables for tests
            os.environ["BACKEND_URL"] = self.backend_url
            os.environ["FRONTEND_URL"] = self.frontend_url
            
            # Run integration tests using pytest
            import subprocess
            result = subprocess.run([
                sys.executable, "-m", "pytest", 
                "backend/tests/test_cloud_integration.py", 
                "-v", 
                "--tb=short"
            ], capture_output=True, text=True, cwd=Path(__file__).parent)
            
            print(result.stdout)
            if result.stderr:
                print("STDERR:", result.stderr)
            
            print("✅ Integration tests completed")
            return result.returncode == 0
            
        except Exception as e:
            print(f"❌ Integration tests failed: {e}")
            return False
    
    async def run_performance_tests(self) -> bool:
        """Run performance tests"""
        print("\n⚡ Running Performance Tests...")
        print("-" * 30)
        
        try:
            # Set environment variables for tests
            os.environ["BACKEND_URL"] = self.backend_url
            os.environ["FRONTEND_URL"] = self.frontend_url
            
            # Run performance tests directly
            import subprocess
            result = subprocess.run([
                sys.executable, 
                "backend/tests/test_cloud_performance.py"
            ], capture_output=True, text=True, cwd=Path(__file__).parent)
            
            print(result.stdout)
            if result.stderr:
                print("STDERR:", result.stderr)
            
            print("✅ Performance tests completed")
            return result.returncode == 0
            
        except Exception as e:
            print(f"❌ Performance tests failed: {e}")
            return False
    
    async def run_security_tests(self) -> bool:
        """Run security tests"""
        print("\n🔒 Running Security Tests...")
        print("-" * 30)
        
        try:
            # Set environment variables for tests
            os.environ["BACKEND_URL"] = self.backend_url
            os.environ["FRONTEND_URL"] = self.frontend_url
            
            # Run security tests directly
            import subprocess
            result = subprocess.run([
                sys.executable, 
                "backend/tests/test_cloud_security.py"
            ], capture_output=True, text=True, cwd=Path(__file__).parent)
            
            print(result.stdout)
            if result.stderr:
                print("STDERR:", result.stderr)
            
            print("✅ Security tests completed")
            return result.returncode == 0
            
        except Exception as e:
            print(f"❌ Security tests failed: {e}")
            return False
    
    def generate_report(self) -> str:
        """Generate comprehensive test report"""
        total_tests = len(self.results)
        passed_tests = sum(1 for result in self.results.values() if result)
        failed_tests = total_tests - passed_tests
        
        report = f"""
🌐 CustomerCareGPT Cloud Test Report
====================================
Environment: {self.environment.upper()}
Backend URL: {self.backend_url}
Frontend URL: {self.frontend_url}
Test Date: {time.strftime('%Y-%m-%d %H:%M:%S')}

Test Results:
- Total Tests: {total_tests}
- Passed: {passed_tests}
- Failed: {failed_tests}
- Success Rate: {passed_tests/total_tests*100:.1f}%

Detailed Results:
"""
        
        for test_name, passed in self.results.items():
            status = "✅ PASS" if passed else "❌ FAIL"
            report += f"  {status} {test_name}\n"
        
        if failed_tests > 0:
            report += f"\n⚠️  {failed_tests} test(s) failed. Check the logs above for details.\n"
        else:
            report += "\n🎉 All tests passed! Your application is ready for production.\n"
        
        return report
    
    async def run_all_tests(self):
        """Run all tests"""
        self.print_banner()
        
        # Run tests
        self.results["Connectivity"] = await self.test_connectivity()
        self.results["Authentication Flow"] = await self.test_authentication_flow()
        self.results["Core Functionality"] = await self.test_core_functionality()
        self.results["Integration Tests"] = await self.run_integration_tests()
        self.results["Performance Tests"] = await self.run_performance_tests()
        self.results["Security Tests"] = await self.run_security_tests()
        
        # Generate and print report
        report = self.generate_report()
        print(report)
        
        # Save report to file
        report_filename = f"cloud_test_report_{self.environment}_{int(time.time())}.txt"
        with open(report_filename, "w") as f:
            f.write(report)
        
        print(f"📊 Detailed report saved to: {report_filename}")
        
        # Return success status
        return all(self.results.values())

async def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Run CustomerCareGPT cloud tests")
    parser.add_argument("--environment", choices=["staging", "production"], default="production", help="Target environment")
    parser.add_argument("--quick", action="store_true", help="Run quick tests only (connectivity + auth)")
    
    args = parser.parse_args()
    
    runner = CloudTestRunner(environment=args.environment)
    
    if args.quick:
        # Run quick tests only
        runner.print_banner()
        runner.results["Connectivity"] = await runner.test_connectivity()
        runner.results["Authentication Flow"] = await runner.test_authentication_flow()
        
        report = runner.generate_report()
        print(report)
        
        success = all(runner.results.values())
    else:
        # Run all tests
        success = await runner.run_all_tests()
    
    if success:
        print("\n🚀 Your application is ready for production!")
        sys.exit(0)
    else:
        print("\n🔧 Please fix the failing tests before deploying to production.")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
