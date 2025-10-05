#!/usr/bin/env python3
"""
Production RAG Test Runner
Runs comprehensive tests for production RAG service and advanced features
"""

import os
import sys
import subprocess
import time
from pathlib import Path

def run_command(command, description):
    """Run a command and return success status"""
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
        print(f"\nSTDOUT:\n{result.stdout}")
    
    if result.stderr:
        print(f"\nSTDERR:\n{result.stderr}")
    
    return result.returncode == 0

def main():
    """Main test runner"""
    print("🚀 Production RAG Test Runner")
    print("=" * 60)
    
    # Change to backend directory
    backend_dir = Path(__file__).parent
    os.chdir(backend_dir)
    
    # Test configuration
    test_configs = [
        {
            "command": "pytest tests/unit/test_production_rag_advanced.py -v --cov=app --cov-report=html --cov-report=term-missing",
            "description": "Production RAG Advanced Unit Tests"
        },
        {
            "command": "pytest tests/integration/test_production_rag_integration.py -v --cov=app --cov-report=html --cov-report=term-missing",
            "description": "Production RAG Integration Tests"
        },
        {
            "command": "pytest tests/performance/test_production_rag_performance.py -v -m 'not slow'",
            "description": "Production RAG Performance Tests"
        },
        {
            "command": "pytest tests/e2e/test_production_rag_e2e.py -v",
            "description": "Production RAG End-to-End Tests"
        }
    ]
    
    # Run tests
    results = []
    for config in test_configs:
        success = run_command(config["command"], config["description"])
        results.append({
            "description": config["description"],
            "success": success
        })
    
    # Summary
    print(f"\n{'='*60}")
    print("TEST SUMMARY")
    print(f"{'='*60}")
    
    total_tests = len(results)
    passed_tests = sum(1 for r in results if r["success"])
    failed_tests = total_tests - passed_tests
    
    for result in results:
        status = "✅ PASSED" if result["success"] else "❌ FAILED"
        print(f"{status} - {result['description']}")
    
    print(f"\nTotal: {total_tests}")
    print(f"Passed: {passed_tests}")
    print(f"Failed: {failed_tests}")
    print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
    
    if failed_tests > 0:
        print(f"\n❌ {failed_tests} test suite(s) failed!")
        sys.exit(1)
    else:
        print(f"\n✅ All {total_tests} test suite(s) passed!")
        sys.exit(0)

if __name__ == "__main__":
    main()
