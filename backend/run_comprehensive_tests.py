"""
Comprehensive Test Runner for CustomerCareGPT Backend
Runs all comprehensive integration tests including embed widget, analytics, real-time data, and backend logic
"""

import pytest
import os
import sys
import time
from datetime import datetime

# Add the backend directory to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

def run_test_suite(test_files, suite_name):
    """Run a specific test suite and return results"""
    print(f"\n{'='*60}")
    print(f"RUNNING {suite_name.upper()} TESTS")
    print(f"{'='*60}")
    
    start_time = time.time()
    
    # Run pytest on the specified files
    exit_code = pytest.main([
        "-v",  # verbose
        "-s",  # show print statements
        "--strict-markers",  # warn about unknown markers
        "--tb=short",  # short traceback format
        "--maxfail=5",  # stop after 5 failures
        "--disable-warnings",  # disable warnings for cleaner output
    ] + test_files)
    
    end_time = time.time()
    duration = end_time - start_time
    
    print(f"\n{suite_name} Tests Completed in {duration:.2f} seconds")
    print(f"Exit Code: {exit_code}")
    
    return exit_code, duration

def main():
    """Main test runner function"""
    print("🚀 CUSTOMERCAREGPT COMPREHENSIVE TEST SUITE")
    print("=" * 60)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    # Ensure we're in the backend directory
    current_dir = os.path.dirname(os.path.abspath(__file__))
    if os.path.basename(current_dir) == "backend":
        os.chdir(current_dir)
    else:
        print("❌ Error: Please run this script from the 'backend' directory.")
        sys.exit(1)
    
    # Define test suites
    test_suites = {
        "Embed Widget Comprehensive": [
            "tests/integration/test_embed_widget_comprehensive.py"
        ],
        "Analytics Comprehensive": [
            "tests/integration/test_analytics_comprehensive.py"
        ],
        "Real-time Data Comprehensive": [
            "tests/integration/test_realtime_data_comprehensive.py"
        ],
        "Backend Logic Comprehensive": [
            "tests/integration/test_backend_logic_comprehensive.py"
        ],
        "Integration Edge Cases": [
            "tests/integration/test_integration_edge_cases.py"
        ],
        "Critical Production Tests": [
            "tests/integration/test_database_migrations.py",
            "tests/integration/test_multitenant_isolation.py",
            "tests/integration/test_websocket_reliability.py",
            "tests/integration/test_file_processing_limits.py",
            "tests/integration/test_production_rag_quality.py",
            "tests/integration/test_background_job_reliability.py"
        ]
    }
    
    # Track results
    results = {}
    total_start_time = time.time()
    
    # Run each test suite
    for suite_name, test_files in test_suites.items():
        # Check if test files exist
        existing_files = []
        for test_file in test_files:
            if os.path.exists(test_file):
                existing_files.append(test_file)
            else:
                print(f"⚠️  Warning: Test file not found: {test_file}")
        
        if existing_files:
            exit_code, duration = run_test_suite(existing_files, suite_name)
            results[suite_name] = {
                "exit_code": exit_code,
                "duration": duration,
                "files_tested": len(existing_files),
                "status": "PASSED" if exit_code == 0 else "FAILED"
            }
        else:
            print(f"❌ No test files found for {suite_name}")
            results[suite_name] = {
                "exit_code": 1,
                "duration": 0,
                "files_tested": 0,
                "status": "SKIPPED"
            }
    
    # Calculate totals
    total_end_time = time.time()
    total_duration = total_end_time - total_start_time
    
    # Print summary
    print("\n" + "="*60)
    print("📊 COMPREHENSIVE TEST RESULTS SUMMARY")
    print("="*60)
    
    total_tests = 0
    passed_tests = 0
    failed_tests = 0
    skipped_tests = 0
    
    for suite_name, result in results.items():
        status_icon = "✅" if result["status"] == "PASSED" else "❌" if result["status"] == "FAILED" else "⏭️"
        print(f"{status_icon} {suite_name:<35} {result['status']:<8} ({result['duration']:.2f}s)")
        total_tests += 1
        if result["status"] == "PASSED":
            passed_tests += 1
        elif result["status"] == "FAILED":
            failed_tests += 1
        else:
            skipped_tests += 1
    
    print("-" * 60)
    print(f"Total Suites: {total_tests}")
    print(f"✅ Passed: {passed_tests}")
    print(f"❌ Failed: {failed_tests}")
    print(f"⏭️  Skipped: {skipped_tests}")
    print(f"⏱️  Total Duration: {total_duration:.2f} seconds")
    print("="*60)
    
    # Overall status
    if failed_tests == 0:
        print("🎉 ALL TEST SUITES PASSED! Your backend is production ready!")
        overall_exit_code = 0
    else:
        print(f"⚠️  {failed_tests} test suite(s) failed. Please review the results above.")
        overall_exit_code = 1
    
    print(f"Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    return overall_exit_code

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)