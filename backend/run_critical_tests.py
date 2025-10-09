#!/usr/bin/env python3
"""
Critical test runner for production readiness validation
Runs all critical integration tests to ensure production safety
"""

import os
import sys
import subprocess
import time
from pathlib import Path

# Add backend directory to Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

def run_critical_tests():
    """Run all critical integration tests for production readiness"""
    
    print("🚀 Starting Critical Production Readiness Tests")
    print("=" * 60)
    
    # Define critical test files
    critical_tests = [
        "tests/integration/test_database_migrations.py",
        "tests/integration/test_multitenant_isolation.py", 
        "tests/integration/test_websocket_reliability.py",
        "tests/integration/test_file_processing_limits.py",
        "tests/integration/test_production_rag_quality.py",
        "tests/integration/test_background_job_reliability.py"
    ]
    
    # Test results tracking
    results = {
        "passed": 0,
        "failed": 0,
        "skipped": 0,
        "total": 0
    }
    
    failed_tests = []
    
    print(f"📋 Running {len(critical_tests)} critical test suites...")
    print()
    
    for test_file in critical_tests:
        test_path = backend_dir / test_file
        if not test_path.exists():
            print(f"❌ Test file not found: {test_file}")
            results["failed"] += 1
            failed_tests.append(f"{test_file} - File not found")
            continue
        
        print(f"🧪 Running {test_file}...")
        start_time = time.time()
        
        try:
            # Run the test file
            result = subprocess.run([
                sys.executable, "-m", "pytest", 
                str(test_path), 
                "-v", 
                "--tb=short",
                "--disable-warnings",
                "--color=yes"
            ], 
            cwd=backend_dir,
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout per test file
            )
            
            execution_time = time.time() - start_time
            
            if result.returncode == 0:
                print(f"✅ {test_file} - PASSED ({execution_time:.2f}s)")
                results["passed"] += 1
            else:
                print(f"❌ {test_file} - FAILED ({execution_time:.2f}s)")
                print(f"   Error: {result.stderr}")
                results["failed"] += 1
                failed_tests.append(f"{test_file} - {result.stderr}")
            
            results["total"] += 1
            
        except subprocess.TimeoutExpired:
            print(f"⏰ {test_file} - TIMEOUT (300s)")
            results["failed"] += 1
            failed_tests.append(f"{test_file} - Timeout after 300s")
            results["total"] += 1
            
        except Exception as e:
            print(f"💥 {test_file} - ERROR: {e}")
            results["failed"] += 1
            failed_tests.append(f"{test_file} - {e}")
            results["total"] += 1
        
        print()
    
    # Print summary
    print("=" * 60)
    print("📊 CRITICAL TEST RESULTS SUMMARY")
    print("=" * 60)
    print(f"Total Tests: {results['total']}")
    print(f"✅ Passed: {results['passed']}")
    print(f"❌ Failed: {results['failed']}")
    print(f"⏭️  Skipped: {results['skipped']}")
    print()
    
    if results["failed"] > 0:
        print("🚨 FAILED TESTS:")
        for failed_test in failed_tests:
            print(f"   - {failed_test}")
        print()
    
    # Determine overall status
    if results["failed"] == 0:
        print("🎉 ALL CRITICAL TESTS PASSED!")
        print("✅ Your backend is PRODUCTION READY!")
        return True
    else:
        print("⚠️  SOME CRITICAL TESTS FAILED!")
        print("🚫 Your backend is NOT ready for production.")
        print("🔧 Please fix the failing tests before deploying.")
        return False

def run_quick_smoke_tests():
    """Run quick smoke tests for basic functionality"""
    
    print("🔥 Running Quick Smoke Tests...")
    print("=" * 40)
    
    smoke_tests = [
        "tests/test_simple.py",
        "tests/test_utils.py"
    ]
    
    for test_file in smoke_tests:
        test_path = backend_dir / test_file
        if test_path.exists():
            print(f"🧪 Running {test_file}...")
            try:
                result = subprocess.run([
                    sys.executable, "-m", "pytest", 
                    str(test_path), 
                    "-v", 
                    "--tb=short",
                    "--disable-warnings"
                ], 
                cwd=backend_dir,
                capture_output=True,
                text=True,
                timeout=60
                )
                
                if result.returncode == 0:
                    print(f"✅ {test_file} - PASSED")
                else:
                    print(f"❌ {test_file} - FAILED")
                    print(f"   Error: {result.stderr}")
                    
            except Exception as e:
                print(f"💥 {test_file} - ERROR: {e}")
        else:
            print(f"⚠️  {test_file} - Not found")

if __name__ == "__main__":
    print("🔍 CustomerCareGPT Backend - Critical Test Suite")
    print("=" * 60)
    print()
    
    # Check if we're in the right directory
    if not (backend_dir / "app").exists():
        print("❌ Error: Please run this script from the backend directory")
        sys.exit(1)
    
    # Set environment variables for testing
    os.environ["TESTING"] = "true"
    os.environ["ENVIRONMENT"] = "testing"
    os.environ["DATABASE_URL"] = "sqlite:///./test_critical.db"
    
    # Run smoke tests first
    run_quick_smoke_tests()
    print()
    
    # Run critical tests
    success = run_critical_tests()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)
