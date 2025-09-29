#!/usr/bin/env python3
"""
Cloud Test Runner
Runs all cloud tests against your deployed backend
"""
import asyncio
import sys
import os
import argparse
import subprocess
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))

from test_cloud_integration import CloudTestClient, main as run_integration_tests
from test_cloud_performance import main as run_performance_tests
from test_cloud_security import main as run_security_tests

def print_banner():
    """Print test banner"""
    print("🌐 CustomerCareGPT Cloud Testing Suite")
    print("=" * 50)
    print("Testing your deployed cloud backend from local machine")
    print("=" * 50)

def check_dependencies():
    """Check if required dependencies are installed"""
    required_packages = [
        "pytest",
        "httpx",
        "asyncio"
    ]
    
    missing_packages = []
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print(f"❌ Missing required packages: {', '.join(missing_packages)}")
        print("Install them with: pip install pytest httpx")
        return False
    
    return True

def run_unit_tests():
    """Run unit tests"""
    print("\n🧪 Running Unit Tests...")
    print("-" * 30)
    
    try:
        result = subprocess.run([
            sys.executable, "-m", "pytest", 
            "backend/tests/unit/", 
            "-v", 
            "--tb=short"
        ], capture_output=True, text=True, cwd=Path(__file__).parent.parent.parent)
        
        print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
        
        return result.returncode == 0
    except Exception as e:
        print(f"❌ Unit tests failed: {e}")
        return False

def run_integration_tests_local():
    """Run integration tests locally"""
    print("\n🔗 Running Integration Tests...")
    print("-" * 30)
    
    try:
        result = subprocess.run([
            sys.executable, "-m", "pytest", 
            "backend/tests/integration/", 
            "-v", 
            "--tb=short"
        ], capture_output=True, text=True, cwd=Path(__file__).parent.parent.parent)
        
        print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
        
        return result.returncode == 0
    except Exception as e:
        print(f"❌ Integration tests failed: {e}")
        return False

async def run_cloud_integration_tests():
    """Run cloud integration tests"""
    print("\n🌐 Running Cloud Integration Tests...")
    print("-" * 30)
    
    try:
        await run_integration_tests()
        return True
    except Exception as e:
        print(f"❌ Cloud integration tests failed: {e}")
        return False

async def run_cloud_performance_tests():
    """Run cloud performance tests"""
    print("\n⚡ Running Cloud Performance Tests...")
    print("-" * 30)
    
    try:
        await run_performance_tests()
        return True
    except Exception as e:
        print(f"❌ Cloud performance tests failed: {e}")
        return False

async def run_cloud_security_tests():
    """Run cloud security tests"""
    print("\n🔒 Running Cloud Security Tests...")
    print("-" * 30)
    
    try:
        await run_security_tests()
        return True
    except Exception as e:
        print(f"❌ Cloud security tests failed: {e}")
        return False

def print_test_summary(results):
    """Print test summary"""
    print("\n📊 Test Summary")
    print("=" * 50)
    
    total_tests = len(results)
    passed_tests = sum(1 for result in results.values() if result)
    failed_tests = total_tests - passed_tests
    
    print(f"Total Test Suites: {total_tests}")
    print(f"Passed: {passed_tests}")
    print(f"Failed: {failed_tests}")
    print(f"Success Rate: {passed_tests/total_tests*100:.1f}%")
    
    print("\nDetailed Results:")
    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"  {status} {test_name}")
    
    if failed_tests > 0:
        print(f"\n⚠️  {failed_tests} test suite(s) failed. Check the logs above for details.")
        return False
    else:
        print("\n🎉 All tests passed!")
        return True

async def main():
    """Main test runner"""
    parser = argparse.ArgumentParser(description="Run CustomerCareGPT cloud tests")
    parser.add_argument("--unit", action="store_true", help="Run unit tests only")
    parser.add_argument("--integration", action="store_true", help="Run integration tests only")
    parser.add_argument("--cloud", action="store_true", help="Run cloud tests only")
    parser.add_argument("--performance", action="store_true", help="Run performance tests only")
    parser.add_argument("--security", action="store_true", help="Run security tests only")
    parser.add_argument("--all", action="store_true", help="Run all tests (default)")
    parser.add_argument("--environment", choices=["staging", "production"], default="production", help="Target environment")
    
    args = parser.parse_args()
    
    print_banner()
    
    # Check dependencies
    if not check_dependencies():
        sys.exit(1)
    
    # Set environment
    if args.environment == "staging":
        os.environ["BACKEND_URL"] = "http://localhost:8000"
        os.environ["FRONTEND_URL"] = "http://localhost:3000"
    else:
        os.environ["BACKEND_URL"] = "http://localhost:8000"
        os.environ["FRONTEND_URL"] = "http://localhost:3000"
    
    print(f"🎯 Target Environment: {args.environment}")
    print(f"🌐 Backend URL: {os.environ['BACKEND_URL']}")
    print(f"🌐 Frontend URL: {os.environ['FRONTEND_URL']}")
    
    results = {}
    
    # Determine which tests to run
    run_all = args.all or (not any([args.unit, args.integration, args.cloud, args.performance, args.security]))
    
    if args.unit or run_all:
        results["Unit Tests"] = run_unit_tests()
    
    if args.integration or run_all:
        results["Integration Tests"] = run_integration_tests_local()
    
    if args.cloud or run_all:
        results["Cloud Integration Tests"] = await run_cloud_integration_tests()
    
    if args.performance or run_all:
        results["Cloud Performance Tests"] = await run_cloud_performance_tests()
    
    if args.security or run_all:
        results["Cloud Security Tests"] = await run_cloud_security_tests()
    
    # Print summary
    success = print_test_summary(results)
    
    if success:
        print("\n🚀 Your application is ready for production!")
        sys.exit(0)
    else:
        print("\n🔧 Please fix the failing tests before deploying to production.")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
