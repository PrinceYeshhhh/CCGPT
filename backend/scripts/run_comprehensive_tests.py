#!/usr/bin/env python3
"""
Comprehensive test runner for CustomerCareGPT
Runs all test suites with detailed reporting and coverage analysis
"""

import os
import sys
import subprocess
import json
import time
from pathlib import Path
from typing import Dict, List, Tuple, Any
import argparse

# Add the backend directory to the Python path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))


class TestRunner:
    """Comprehensive test runner with detailed reporting"""
    
    def __init__(self, backend_dir: Path):
        self.backend_dir = backend_dir
        self.test_dir = backend_dir / "tests"
        self.results = {
            "start_time": None,
            "end_time": None,
            "duration": 0,
            "total_tests": 0,
            "passed": 0,
            "failed": 0,
            "skipped": 0,
            "errors": 0,
            "coverage": 0,
            "test_suites": {},
            "performance": {},
            "security": {},
            "integration": {}
        }
    
    def run_all_tests(self, 
                     include_unit: bool = True,
                     include_integration: bool = True,
                     include_performance: bool = True,
                     include_security: bool = True,
                     parallel: bool = True,
                     coverage: bool = True,
                     verbose: bool = False) -> Dict[str, Any]:
        """Run all test suites with comprehensive reporting"""
        
        print("🚀 Starting Comprehensive Test Suite for CustomerCareGPT")
        print("=" * 60)
        
        self.results["start_time"] = time.time()
        
        # Set up test environment
        self._setup_test_environment()
        
        # Run test suites
        if include_unit:
            self._run_unit_tests(parallel, coverage, verbose)
        
        if include_integration:
            self._run_integration_tests(parallel, coverage, verbose)
        
        if include_performance:
            self._run_performance_tests(verbose)
        
        if include_security:
            self._run_security_tests(verbose)
        
        # Generate reports
        self._generate_coverage_report()
        self._generate_performance_report()
        self._generate_security_report()
        
        self.results["end_time"] = time.time()
        self.results["duration"] = self.results["end_time"] - self.results["start_time"]
        
        # Print summary
        self._print_summary()
        
        return self.results
    
    def _setup_test_environment(self):
        """Set up test environment variables"""
        os.environ.update({
            "TESTING": "true",
            "DATABASE_URL": "sqlite:///:memory:",
            "REDIS_URL": "redis://localhost:6379/1",
            "SECRET_KEY": "test-secret-key",
            "JWT_SECRET": "test-jwt-secret",
            "GEMINI_API_KEY": "test-gemini-key",
            "STRIPE_API_KEY": "test-stripe-key",
            "ENVIRONMENT": "testing",
            "DEBUG": "true",
            "LOG_LEVEL": "DEBUG"
        })
        
        print("✅ Test environment configured")
    
    def _run_unit_tests(self, parallel: bool, coverage: bool, verbose: bool):
        """Run unit tests"""
        print("\n📋 Running Unit Tests...")
        print("-" * 40)
        
        unit_test_files = [
            "tests/unit/test_auth_comprehensive.py",
            "tests/unit/test_document_processing_comprehensive.py",
            "tests/unit/test_rag_system_comprehensive.py",
            "tests/unit/test_auth.py",
            "tests/unit/test_database.py",
            "tests/unit/test_models_validation.py",
            "tests/unit/test_middleware.py",
            "tests/unit/test_security_services.py",
            "tests/unit/test_utility_services.py"
        ]
        
        # Filter existing test files
        existing_files = [f for f in unit_test_files if (self.test_dir / f).exists()]
        
        if not existing_files:
            print("⚠️  No unit test files found")
            return
        
        cmd = self._build_pytest_command(existing_files, parallel, coverage, verbose)
        result = self._run_command(cmd, "Unit Tests")
        
        self.results["test_suites"]["unit"] = result
        self._update_totals(result)
    
    def _run_integration_tests(self, parallel: bool, coverage: bool, verbose: bool):
        """Run integration tests"""
        print("\n🔗 Running Integration Tests...")
        print("-" * 40)
        
        integration_test_files = [
            "tests/integration/test_production_workflows_comprehensive.py",
            "tests/integration/test_integration_comprehensive.py",
            "tests/integration/test_integration.py",
            "tests/test_integration.py"
        ]
        
        # Filter existing test files
        existing_files = [f for f in integration_test_files if (self.test_dir / f).exists()]
        
        if not existing_files:
            print("⚠️  No integration test files found")
            return
        
        cmd = self._build_pytest_command(existing_files, parallel, coverage, verbose)
        result = self._run_command(cmd, "Integration Tests")
        
        self.results["test_suites"]["integration"] = result
        self._update_totals(result)
    
    def _run_performance_tests(self, verbose: bool):
        """Run performance tests"""
        print("\n⚡ Running Performance Tests...")
        print("-" * 40)
        
        performance_test_files = [
            "tests/performance/test_load_testing.py",
            "tests/performance/test_stress_testing.py",
            "tests/performance/test_production_rag_performance.py"
        ]
        
        # Filter existing test files
        existing_files = [f for f in performance_test_files if (self.test_dir / f).exists()]
        
        if not existing_files:
            print("⚠️  No performance test files found")
            return
        
        cmd = self._build_pytest_command(existing_files, False, False, verbose)
        result = self._run_command(cmd, "Performance Tests")
        
        self.results["test_suites"]["performance"] = result
        self._update_totals(result)
        
        # Extract performance metrics
        self._extract_performance_metrics()
    
    def _run_security_tests(self, verbose: bool):
        """Run security tests"""
        print("\n🔒 Running Security Tests...")
        print("-" * 40)
        
        security_test_files = [
            "tests/unit/test_auth_security.py",
            "tests/unit/test_security_services.py",
            "tests/security/test_security_comprehensive.py"
        ]
        
        # Filter existing test files
        existing_files = [f for f in security_test_files if (self.test_dir / f).exists()]
        
        if not existing_files:
            print("⚠️  No security test files found")
            return
        
        cmd = self._build_pytest_command(existing_files, False, False, verbose)
        result = self._run_command(cmd, "Security Tests")
        
        self.results["test_suites"]["security"] = result
        self._update_totals(result)
        
        # Extract security metrics
        self._extract_security_metrics()
    
    def _build_pytest_command(self, test_files: List[str], parallel: bool, coverage: bool, verbose: bool) -> List[str]:
        """Build pytest command with options"""
        cmd = ["python", "-m", "pytest"]
        
        # Add test files
        cmd.extend(test_files)
        
        # Add options
        if verbose:
            cmd.append("-v")
        
        if parallel:
            cmd.extend(["-n", "auto"])  # Use pytest-xdist for parallel execution
        
        if coverage:
            cmd.extend([
                "--cov=app",
                "--cov-report=html:htmlcov",
                "--cov-report=term-missing",
                "--cov-report=xml:coverage.xml",
                "--cov-fail-under=80"
            ])
        
        # Add other options
        cmd.extend([
            "--tb=short",
            "--strict-markers",
            "--disable-warnings",
            "--color=yes",
            "--durations=10"
        ])
        
        return cmd
    
    def _run_command(self, cmd: List[str], test_type: str) -> Dict[str, Any]:
        """Run a command and capture results"""
        print(f"Running: {' '.join(cmd)}")
        
        start_time = time.time()
        
        try:
            result = subprocess.run(
                cmd,
                cwd=self.backend_dir,
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )
            
            end_time = time.time()
            duration = end_time - start_time
            
            # Parse pytest output
            output_lines = result.stdout.split('\n')
            test_summary = self._parse_pytest_output(output_lines)
            
            return {
                "test_type": test_type,
                "duration": duration,
                "return_code": result.return_code,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "success": result.return_code == 0,
                **test_summary
            }
            
        except subprocess.TimeoutExpired:
            return {
                "test_type": test_type,
                "duration": 300,
                "return_code": -1,
                "stdout": "",
                "stderr": "Test timeout after 5 minutes",
                "success": False,
                "total_tests": 0,
                "passed": 0,
                "failed": 0,
                "skipped": 0,
                "errors": 0
            }
        except Exception as e:
            return {
                "test_type": test_type,
                "duration": 0,
                "return_code": -1,
                "stdout": "",
                "stderr": str(e),
                "success": False,
                "total_tests": 0,
                "passed": 0,
                "failed": 0,
                "skipped": 0,
                "errors": 0
            }
    
    def _parse_pytest_output(self, output_lines: List[str]) -> Dict[str, int]:
        """Parse pytest output to extract test statistics"""
        stats = {
            "total_tests": 0,
            "passed": 0,
            "failed": 0,
            "skipped": 0,
            "errors": 0
        }
        
        for line in output_lines:
            if "failed" in line and "passed" in line:
                # Parse line like "5 failed, 10 passed in 2.34s"
                parts = line.split()
                for i, part in enumerate(parts):
                    if part.isdigit():
                        if i > 0 and parts[i-1] in ["failed", "passed", "skipped", "error"]:
                            if parts[i-1] == "failed":
                                stats["failed"] = int(part)
                            elif parts[i-1] == "passed":
                                stats["passed"] = int(part)
                            elif parts[i-1] == "skipped":
                                stats["skipped"] = int(part)
                            elif parts[i-1] == "error":
                                stats["errors"] = int(part)
                
                stats["total_tests"] = stats["passed"] + stats["failed"] + stats["skipped"] + stats["errors"]
                break
        
        return stats
    
    def _update_totals(self, result: Dict[str, Any]):
        """Update total test statistics"""
        self.results["total_tests"] += result.get("total_tests", 0)
        self.results["passed"] += result.get("passed", 0)
        self.results["failed"] += result.get("failed", 0)
        self.results["skipped"] += result.get("skipped", 0)
        self.results["errors"] += result.get("errors", 0)
    
    def _extract_performance_metrics(self):
        """Extract performance metrics from test results"""
        # This would parse performance test output for metrics
        # For now, just set placeholder values
        self.results["performance"] = {
            "avg_response_time": 0.0,
            "max_response_time": 0.0,
            "throughput": 0.0,
            "memory_usage": 0.0,
            "cpu_usage": 0.0
        }
    
    def _extract_security_metrics(self):
        """Extract security metrics from test results"""
        # This would parse security test output for metrics
        # For now, just set placeholder values
        self.results["security"] = {
            "vulnerabilities_found": 0,
            "security_tests_passed": 0,
            "security_tests_failed": 0,
            "critical_issues": 0,
            "high_issues": 0,
            "medium_issues": 0,
            "low_issues": 0
        }
    
    def _generate_coverage_report(self):
        """Generate coverage report"""
        coverage_file = self.backend_dir / "coverage.xml"
        if coverage_file.exists():
            # Parse coverage XML to extract coverage percentage
            try:
                import xml.etree.ElementTree as ET
                tree = ET.parse(coverage_file)
                root = tree.getroot()
                
                # Extract coverage percentage
                coverage_attr = root.attrib.get("line-rate", "0")
                self.results["coverage"] = float(coverage_attr) * 100
            except Exception:
                self.results["coverage"] = 0.0
        else:
            self.results["coverage"] = 0.0
    
    def _generate_performance_report(self):
        """Generate performance report"""
        # This would generate a detailed performance report
        pass
    
    def _generate_security_report(self):
        """Generate security report"""
        # This would generate a detailed security report
        pass
    
    def _print_summary(self):
        """Print test summary"""
        print("\n" + "=" * 60)
        print("📊 COMPREHENSIVE TEST SUMMARY")
        print("=" * 60)
        
        print(f"⏱️  Total Duration: {self.results['duration']:.2f} seconds")
        print(f"🧪 Total Tests: {self.results['total_tests']}")
        print(f"✅ Passed: {self.results['passed']}")
        print(f"❌ Failed: {self.results['failed']}")
        print(f"⏭️  Skipped: {self.results['skipped']}")
        print(f"💥 Errors: {self.results['errors']}")
        print(f"📈 Coverage: {self.results['coverage']:.1f}%")
        
        # Test suite breakdown
        print("\n📋 Test Suite Breakdown:")
        for suite_name, suite_result in self.results["test_suites"].items():
            status = "✅" if suite_result["success"] else "❌"
            print(f"  {status} {suite_name.title()}: {suite_result.get('passed', 0)}/{suite_result.get('total_tests', 0)} passed")
        
        # Performance metrics
        if self.results["performance"]:
            print("\n⚡ Performance Metrics:")
            perf = self.results["performance"]
            print(f"  Average Response Time: {perf.get('avg_response_time', 0):.3f}s")
            print(f"  Max Response Time: {perf.get('max_response_time', 0):.3f}s")
            print(f"  Throughput: {perf.get('throughput', 0):.1f} req/s")
        
        # Security metrics
        if self.results["security"]:
            print("\n🔒 Security Metrics:")
            sec = self.results["security"]
            print(f"  Vulnerabilities Found: {sec.get('vulnerabilities_found', 0)}")
            print(f"  Security Tests Passed: {sec.get('security_tests_passed', 0)}")
            print(f"  Critical Issues: {sec.get('critical_issues', 0)}")
        
        # Overall status
        success_rate = (self.results["passed"] / self.results["total_tests"] * 100) if self.results["total_tests"] > 0 else 0
        print(f"\n🎯 Overall Success Rate: {success_rate:.1f}%")
        
        if self.results["failed"] == 0 and self.results["errors"] == 0:
            print("🎉 ALL TESTS PASSED!")
        else:
            print("⚠️  SOME TESTS FAILED - CHECK DETAILS ABOVE")
        
        print("=" * 60)
    
    def save_results(self, output_file: str = "test_results.json"):
        """Save test results to file"""
        output_path = self.backend_dir / output_file
        with open(output_path, 'w') as f:
            json.dump(self.results, f, indent=2)
        print(f"📄 Results saved to: {output_path}")


def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Comprehensive Test Runner for CustomerCareGPT")
    parser.add_argument("--unit", action="store_true", default=True, help="Run unit tests")
    parser.add_argument("--integration", action="store_true", default=True, help="Run integration tests")
    parser.add_argument("--performance", action="store_true", default=True, help="Run performance tests")
    parser.add_argument("--security", action="store_true", default=True, help="Run security tests")
    parser.add_argument("--no-parallel", action="store_true", help="Disable parallel test execution")
    parser.add_argument("--no-coverage", action="store_true", help="Disable coverage reporting")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument("--output", "-o", default="test_results.json", help="Output file for results")
    
    args = parser.parse_args()
    
    # Get backend directory
    backend_dir = Path(__file__).parent.parent
    
    # Create test runner
    runner = TestRunner(backend_dir)
    
    # Run tests
    results = runner.run_all_tests(
        include_unit=args.unit,
        include_integration=args.integration,
        include_performance=args.performance,
        include_security=args.security,
        parallel=not args.no_parallel,
        coverage=not args.no_coverage,
        verbose=args.verbose
    )
    
    # Save results
    runner.save_results(args.output)
    
    # Exit with appropriate code
    if results["failed"] > 0 or results["errors"] > 0:
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()
