#!/usr/bin/env python3
"""
Comprehensive Unit Test Runner for CustomerCareGPT Backend
Runs all unit tests with detailed coverage reporting for production readiness
"""

import os
import sys
import subprocess
import json
import time
from pathlib import Path
from datetime import datetime

# Add backend directory to Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

def run_command(command, description):
    """Run a command and return the result"""
    print(f"\n{'='*60}")
    print(f"Running: {description}")
    print(f"Command: {command}")
    print(f"{'='*60}")
    
    start_time = time.time()
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    end_time = time.time()
    
    print(f"Exit code: {result.returncode}")
    print(f"Duration: {end_time - start_time:.2f} seconds")
    
    if result.stdout:
        print("\nSTDOUT:")
        print(result.stdout)
    
    if result.stderr:
        print("\nSTDERR:")
        print(result.stderr)
    
    return result

def check_test_coverage():
    """Check current test coverage"""
    print("\n" + "="*80)
    print("TEST COVERAGE ANALYSIS")
    print("="*80)
    
    # Run coverage analysis
    coverage_cmd = "python -m pytest tests/unit/ --cov=app --cov-report=term-missing --cov-report=json:coverage.json --cov-report=html:htmlcov"
    result = run_command(coverage_cmd, "Unit Test Coverage Analysis")
    
    # Parse coverage results
    if os.path.exists("coverage.json"):
        with open("coverage.json", "r") as f:
            coverage_data = json.load(f)
        
        total_coverage = coverage_data.get("totals", {}).get("percent_covered", 0)
        print(f"\nTotal Coverage: {total_coverage:.2f}%")
        
        # Check if coverage meets production standards
        if total_coverage >= 80:
            print("✅ Coverage meets production standards (≥80%)")
        else:
            print("❌ Coverage below production standards (<80%)")
            print("   Consider adding more tests before production deployment")
        
        return total_coverage
    else:
        print("❌ Coverage report not generated")
        return 0

def run_unit_tests():
    """Run all unit tests"""
    print("\n" + "="*80)
    print("RUNNING UNIT TESTS")
    print("="*80)
    
    # Test categories
    test_categories = [
        ("Core Services", "tests/unit/test_services_unit.py"),
        ("API Endpoints", "tests/unit/test_api_endpoints_unit.py"),
        ("Authentication", "tests/unit/test_auth.py"),
        ("Middleware", "tests/unit/test_middleware.py"),
        ("Database", "tests/unit/test_database.py"),
        ("WebSocket", "tests/unit/test_websocket.py"),
        ("Production RAG System", "tests/unit/test_production_rag_system.py"),
        ("Enhanced Services", "tests/unit/test_enhanced_services.py"),
        ("Security Services", "tests/unit/test_security_services.py"),
        ("Utility Services", "tests/unit/test_utility_services.py"),
        ("Model Validation", "tests/unit/test_models_validation.py"),
    ]
    
    results = {}
    total_tests = 0
    passed_tests = 0
    failed_tests = 0
    
    for category, test_file in test_categories:
        if os.path.exists(test_file):
            print(f"\n--- {category} ---")
            cmd = f"python -m pytest {test_file} -v --tb=short"
            result = run_command(cmd, f"{category} Tests")
            
            results[category] = {
                "file": test_file,
                "exit_code": result.returncode,
                "passed": result.returncode == 0
            }
            
            if result.returncode == 0:
                passed_tests += 1
                print(f"✅ {category} tests PASSED")
            else:
                failed_tests += 1
                print(f"❌ {category} tests FAILED")
        else:
            print(f"⚠️  {category} test file not found: {test_file}")
            results[category] = {
                "file": test_file,
                "exit_code": -1,
                "passed": False
            }
            failed_tests += 1
    
    total_tests = passed_tests + failed_tests
    
    print(f"\n{'='*80}")
    print("UNIT TEST SUMMARY")
    print(f"{'='*80}")
    print(f"Total Categories: {total_tests}")
    print(f"Passed: {passed_tests}")
    print(f"Failed: {failed_tests}")
    print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
    
    return results, passed_tests, failed_tests

def run_integration_tests():
    """Run integration tests"""
    print("\n" + "="*80)
    print("RUNNING INTEGRATION TESTS")
    print("="*80)
    
    integration_tests = [
        "tests/test_integration.py",
        "tests/test_integration_comprehensive.py",
        "tests/test_system_comprehensive.py"
    ]
    
    results = {}
    total_tests = 0
    passed_tests = 0
    failed_tests = 0
    
    for test_file in integration_tests:
        if os.path.exists(test_file):
            test_name = Path(test_file).stem
            print(f"\n--- {test_name} ---")
            cmd = f"python -m pytest {test_file} -v --tb=short"
            result = run_command(cmd, f"{test_name} Integration Tests")
            
            results[test_name] = {
                "file": test_file,
                "exit_code": result.returncode,
                "passed": result.returncode == 0
            }
            
            if result.returncode == 0:
                passed_tests += 1
                print(f"✅ {test_name} tests PASSED")
            else:
                failed_tests += 1
                print(f"❌ {test_name} tests FAILED")
        else:
            print(f"⚠️  {test_name} test file not found: {test_file}")
            results[test_name] = {
                "file": test_file,
                "exit_code": -1,
                "passed": False
            }
            failed_tests += 1
    
    total_tests = passed_tests + failed_tests
    
    print(f"\n{'='*80}")
    print("INTEGRATION TEST SUMMARY")
    print(f"{'='*80}")
    print(f"Total Categories: {total_tests}")
    print(f"Passed: {passed_tests}")
    print(f"Failed: {failed_tests}")
    print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
    
    return results, passed_tests, failed_tests

def generate_test_report(unit_results, integration_results, coverage):
    """Generate comprehensive test report"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    report = {
        "timestamp": timestamp,
        "coverage": {
            "total_percentage": coverage,
            "meets_production_standards": coverage >= 80
        },
        "unit_tests": unit_results,
        "integration_tests": integration_results,
        "summary": {
            "total_unit_categories": len(unit_results),
            "passed_unit_categories": sum(1 for r in unit_results.values() if r["passed"]),
            "failed_unit_categories": sum(1 for r in unit_results.values() if not r["passed"]),
            "total_integration_categories": len(integration_results),
            "passed_integration_categories": sum(1 for r in integration_results.values() if r["passed"]),
            "failed_integration_categories": sum(1 for r in integration_results.values() if not r["passed"])
        }
    }
    
    # Save report
    with open("test_report.json", "w") as f:
        json.dump(report, f, indent=2)
    
    print(f"\n{'='*80}")
    print("COMPREHENSIVE TEST REPORT")
    print(f"{'='*80}")
    print(f"Generated: {timestamp}")
    print(f"Coverage: {coverage:.2f}%")
    print(f"Unit Tests: {report['summary']['passed_unit_categories']}/{report['summary']['total_unit_categories']} categories passed")
    print(f"Integration Tests: {report['summary']['passed_integration_categories']}/{report['summary']['total_integration_categories']} categories passed")
    
    # Production readiness assessment
    print(f"\n{'='*80}")
    print("PRODUCTION READINESS ASSESSMENT")
    print(f"{'='*80}")
    
    production_ready = True
    issues = []
    
    if coverage < 80:
        production_ready = False
        issues.append(f"Test coverage below 80% (current: {coverage:.2f}%)")
    
    unit_failures = report['summary']['failed_unit_categories']
    if unit_failures > 0:
        production_ready = False
        issues.append(f"{unit_failures} unit test categories failed")
    
    integration_failures = report['summary']['failed_integration_categories']
    if integration_failures > 0:
        production_ready = False
        issues.append(f"{integration_failures} integration test categories failed")
    
    if production_ready:
        print("✅ PRODUCTION READY - All tests passing and coverage adequate")
    else:
        print("❌ NOT PRODUCTION READY - Issues found:")
        for issue in issues:
            print(f"   - {issue}")
    
    return report

def main():
    """Main test runner function"""
    print("CustomerCareGPT Backend - Comprehensive Test Suite")
    print("=" * 80)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Change to backend directory
    os.chdir(backend_dir)
    
    # Set environment variables for testing
    os.environ["TESTING"] = "true"
    os.environ["DATABASE_URL"] = "sqlite:///./test.db"
    os.environ["REDIS_URL"] = "redis://localhost:6379/1"
    os.environ["SECRET_KEY"] = "test-secret-key"
    os.environ["GEMINI_API_KEY"] = "test-gemini-key"
    os.environ["STRIPE_API_KEY"] = "test-stripe-key"
    os.environ["ENVIRONMENT"] = "testing"
    
    try:
        # Run unit tests
        unit_results, unit_passed, unit_failed = run_unit_tests()
        
        # Run integration tests
        integration_results, integration_passed, integration_failed = run_integration_tests()
        
        # Check coverage
        coverage = check_test_coverage()
        
        # Generate report
        report = generate_test_report(unit_results, integration_results, coverage)
        
        # Final status
        total_passed = unit_passed + integration_passed
        total_failed = unit_failed + integration_failed
        total_tests = total_passed + total_failed
        
        print(f"\n{'='*80}")
        print("FINAL SUMMARY")
        print(f"{'='*80}")
        print(f"Total test categories: {total_tests}")
        print(f"Passed: {total_passed}")
        print(f"Failed: {total_failed}")
        print(f"Success rate: {(total_passed/total_tests)*100:.1f}%")
        print(f"Coverage: {coverage:.2f}%")
        
        if total_failed == 0 and coverage >= 80:
            print("\n🎉 ALL TESTS PASSED - READY FOR PRODUCTION! 🎉")
            return 0
        else:
            print("\n⚠️  SOME TESTS FAILED - REVIEW BEFORE PRODUCTION")
            return 1
            
    except Exception as e:
        print(f"\n❌ Test runner failed with error: {e}")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)

