#!/usr/bin/env python3
"""
Comprehensive Test Runner for CustomerCareGPT
Runs all test suites with proper configuration and reporting
"""

import os
import sys
import subprocess
import argparse
import json
import time
from pathlib import Path
from typing import List, Dict, Any

class TestRunner:
    def __init__(self, base_dir: str = None):
        self.base_dir = Path(base_dir) if base_dir else Path(__file__).parent
        self.results = {}
        self.start_time = time.time()
        
    def run_command(self, command: List[str], cwd: str = None) -> Dict[str, Any]:
        """Run a command and return the result"""
        print(f"Running: {' '.join(command)}")
        
        try:
            result = subprocess.run(
                command,
                cwd=cwd or self.base_dir,
                capture_output=True,
                text=True
            )
            
            return {
                "success": result.returncode == 0,
                "returncode": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "command": " ".join(command)
            }
        except subprocess.TimeoutExpired:
            # Should not occur without timeout, but keep for safety
            return {
                "success": False,
                "returncode": -1,
                "stdout": "",
                "stderr": "Command timeout encountered",
                "command": " ".join(command)
            }
        except Exception as e:
            return {
                "success": False,
                "returncode": -1,
                "stdout": "",
                "stderr": str(e),
                "command": " ".join(command)
            }
    
    def run_unit_tests(self) -> Dict[str, Any]:
        """Run backend unit tests"""
        print("\n🧪 Running Backend Unit Tests...")
        
        command = [
            "python", "-m", "pytest",
            "tests/unit/",
            "-v",
            "--cov=app",
            "--cov-report=html:htmlcov",
            "--cov-report=xml:coverage.xml",
            "--cov-report=term-missing",
            "--cov-fail-under=80",
            "--maxfail=10",
            "-n", "auto"
        ]
        
        return self.run_command(command)
    
    def run_integration_tests(self) -> Dict[str, Any]:
        """Run backend integration tests"""
        print("\n🔗 Running Backend Integration Tests...")
        
        command = [
            "python", "-m", "pytest",
            "tests/integration/",
            "-v",
            "--cov=app",
            "--cov-report=html:htmlcov",
            "--cov-report=xml:coverage.xml",
            "--cov-report=term-missing",
            "--cov-fail-under=75",
            "--maxfail=5",
            "-n", "auto"
        ]
        
        return self.run_command(command)
    
    def run_security_tests(self) -> Dict[str, Any]:
        """Run security tests"""
        print("\n🔒 Running Security Tests...")
        
        # Run security test suite
        security_result = self.run_command([
            "python", "-m", "pytest",
            "tests/security/",
            "-v",
            "--maxfail=5"
        ])
        
        # Run bandit security scan
        bandit_result = self.run_command([
            "bandit", "-r", "app/", "-f", "json", "-o", "security-report.json"
        ])
        
        # Run safety check
        safety_result = self.run_command([
            "safety", "check", "--json", "--output", "safety-report.json"
        ])
        
        return {
            "security_tests": security_result,
            "bandit_scan": bandit_result,
            "safety_check": safety_result,
            "success": all([
                security_result["success"],
                bandit_result["success"],
                safety_result["success"]
            ])
        }
    
    def run_performance_tests(self) -> Dict[str, Any]:
        """Run performance tests"""
        print("\n⚡ Running Performance Tests...")
        
        command = [
            "python", "-m", "pytest",
            "tests/performance/",
            "-v",
            "--maxfail=3"
        ]
        
        return self.run_command(command)
    
    def run_e2e_tests(self) -> Dict[str, Any]:
        """Run end-to-end tests"""
        print("\n🌐 Running End-to-End Tests...")
        
        command = [
            "python", "-m", "pytest",
            "tests/e2e/",
            "-v",
            "--maxfail=5"
        ]
        
        return self.run_command(command)
    
    def run_error_handling_tests(self) -> Dict[str, Any]:
        """Run error handling tests"""
        print("\n🚨 Running Error Handling Tests...")
        
        command = [
            "python", "-m", "pytest",
            "tests/integration/test_error_scenarios.py",
            "-v",
            "--maxfail=10"
        ]
        
        return self.run_command(command)
    
    def run_frontend_tests(self) -> Dict[str, Any]:
        """Run frontend tests"""
        print("\n🎨 Running Frontend Tests...")
        
        frontend_dir = self.base_dir.parent / "frontend"
        
        if not frontend_dir.exists():
            return {
                "success": False,
                "returncode": -1,
                "stdout": "",
                "stderr": "Frontend directory not found",
                "command": "npm test"
            }
        
        # Install dependencies
        install_result = self.run_command(["npm", "ci"], cwd=str(frontend_dir))
        if not install_result["success"]:
            return install_result
        
        # Run tests
        test_result = self.run_command(["npm", "run", "test:ci"], cwd=str(frontend_dir))
        
        return test_result
    
    def generate_report(self) -> str:
        """Generate a comprehensive test report"""
        total_time = time.time() - self.start_time
        
        report = f"""
# CustomerCareGPT Test Report

**Generated:** {time.strftime('%Y-%m-%d %H:%M:%S')}
**Total Runtime:** {total_time:.2f} seconds

## Test Results Summary

| Test Suite | Status | Duration | Coverage |
|------------|--------|----------|----------|
"""
        
        for test_name, result in self.results.items():
            if isinstance(result, dict) and "success" in result:
                status = "✅ PASS" if result["success"] else "❌ FAIL"
                duration = "N/A"
                coverage = "N/A"
            else:
                status = "✅ PASS" if result.get("success", False) else "❌ FAIL"
                duration = "N/A"
                coverage = "N/A"
            
            report += f"| {test_name} | {status} | {duration} | {coverage} |\n"
        
        report += "\n## Detailed Results\n\n"
        
        for test_name, result in self.results.items():
            report += f"### {test_name}\n\n"
            
            if isinstance(result, dict) and "success" in result:
                report += f"**Status:** {'✅ PASS' if result['success'] else '❌ FAIL'}\n"
                report += f"**Return Code:** {result['returncode']}\n"
                if result['stderr']:
                    report += f"**Error:** {result['stderr']}\n"
                report += "\n"
            else:
                for sub_test, sub_result in result.items():
                    report += f"**{sub_test}:** {'✅ PASS' if sub_result['success'] else '❌ FAIL'}\n"
                    if sub_result['stderr']:
                        report += f"**Error:** {sub_result['stderr']}\n"
                report += "\n"
        
        return report
    
    def run_all_tests(self, test_types: List[str] = None) -> bool:
        """Run all specified test types"""
        if test_types is None:
            test_types = [
                "unit", "integration", "security", 
                "performance", "e2e", "error_handling", "frontend"
            ]
        
        all_passed = True
        
        for test_type in test_types:
            if test_type == "unit":
                result = self.run_unit_tests()
            elif test_type == "integration":
                result = self.run_integration_tests()
            elif test_type == "security":
                result = self.run_security_tests()
            elif test_type == "performance":
                result = self.run_performance_tests()
            elif test_type == "e2e":
                result = self.run_e2e_tests()
            elif test_type == "error_handling":
                result = self.run_error_handling_tests()
            elif test_type == "frontend":
                result = self.run_frontend_tests()
            else:
                print(f"Unknown test type: {test_type}")
                continue
            
            self.results[test_type] = result
            
            if not result.get("success", False):
                all_passed = False
                print(f"❌ {test_type} tests failed")
            else:
                print(f"✅ {test_type} tests passed")
        
        return all_passed

def main():
    parser = argparse.ArgumentParser(description="Run comprehensive tests for CustomerCareGPT")
    parser.add_argument(
        "--test-types",
        nargs="+",
        choices=["unit", "integration", "security", "performance", "e2e", "error_handling", "frontend"],
        default=["unit", "integration", "security", "performance", "e2e", "error_handling", "frontend"],
        help="Types of tests to run"
    )
    parser.add_argument(
        "--output",
        "-o",
        default="test-report.md",
        help="Output file for test report"
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Verbose output"
    )
    
    args = parser.parse_args()
    
    runner = TestRunner()
    
    print("🚀 Starting Comprehensive Test Suite for CustomerCareGPT")
    print(f"Test types: {', '.join(args.test_types)}")
    
    success = runner.run_all_tests(args.test_types)
    
    # Generate report
    report = runner.generate_report()
    
    with open(args.output, 'w') as f:
        f.write(report)
    
    print(f"\n📊 Test report saved to: {args.output}")
    
    if success:
        print("🎉 All tests passed!")
        sys.exit(0)
    else:
        print("💥 Some tests failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()
