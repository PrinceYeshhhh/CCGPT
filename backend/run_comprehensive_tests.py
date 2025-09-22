#!/usr/bin/env python3
"""
Comprehensive test runner for CustomerCareGPT
Runs all test categories and generates detailed reports
"""

import os
import sys
import subprocess
import json
import time
from datetime import datetime
from pathlib import Path

class TestRunner:
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.results = {}
        self.start_time = time.time()
        
    def run_command(self, command, description):
        """Run a command and return the result"""
        print(f"\n{'='*60}")
        print(f"Running: {description}")
        print(f"Command: {' '.join(command)}")
        print(f"{'='*60}")
        
        start_time = time.time()
        try:
            result = subprocess.run(
                command,
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )
            
            duration = time.time() - start_time
            
            return {
                "success": result.returncode == 0,
                "returncode": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "duration": duration
            }
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "returncode": -1,
                "stdout": "",
                "stderr": "Test timed out after 5 minutes",
                "duration": 300
            }
        except Exception as e:
            return {
                "success": False,
                "returncode": -1,
                "stdout": "",
                "stderr": str(e),
                "duration": time.time() - start_time
            }
    
    def run_unit_tests(self):
        """Run unit tests"""
        command = [
            "python", "-m", "pytest",
            "tests/test_services_unit.py",
            "tests/test_api_endpoints_unit.py",
            "-m", "unit",
            "--tb=short",
            "-v"
        ]
        return self.run_command(command, "Unit Tests")
    
    def run_integration_tests(self):
        """Run integration tests"""
        command = [
            "python", "-m", "pytest",
            "tests/test_integration.py",
            "tests/test_integration_comprehensive.py",
            "-m", "integration",
            "--tb=short",
            "-v"
        ]
        return self.run_command(command, "Integration Tests")
    
    def run_system_tests(self):
        """Run system tests"""
        command = [
            "python", "-m", "pytest",
            "tests/test_system_comprehensive.py",
            "-m", "system",
            "--tb=short",
            "-v"
        ]
        return self.run_command(command, "System Tests")
    
    def run_whitebox_tests(self):
        """Run white-box tests"""
        command = [
            "python", "-m", "pytest",
            "tests/test_whitebox_comprehensive.py",
            "-m", "whitebox",
            "--tb=short",
            "-v"
        ]
        return self.run_command(command, "White-box Tests")
    
    def run_blackbox_tests(self):
        """Run black-box tests"""
        command = [
            "python", "-m", "pytest",
            "tests/test_blackbox_comprehensive.py",
            "-m", "blackbox",
            "--tb=short",
            "-v"
        ]
        return self.run_command(command, "Black-box Tests")
    
    def run_security_tests(self):
        """Run security tests"""
        command = [
            "python", "-m", "pytest",
            "-m", "security",
            "--tb=short",
            "-v"
        ]
        return self.run_command(command, "Security Tests")
    
    def run_performance_tests(self):
        """Run performance tests"""
        command = [
            "python", "-m", "pytest",
            "-m", "performance",
            "--tb=short",
            "-v"
        ]
        return self.run_command(command, "Performance Tests")
    
    def run_coverage_analysis(self):
        """Run coverage analysis"""
        command = [
            "python", "-m", "pytest",
            "--cov=app",
            "--cov-report=html:htmlcov",
            "--cov-report=term-missing",
            "--cov-report=xml:coverage.xml",
            "--cov-fail-under=80",
            "--tb=short",
            "-v"
        ]
        return self.run_command(command, "Coverage Analysis")
    
    def run_linting(self):
        """Run code linting"""
        command = [
            "python", "-m", "flake8",
            "app/",
            "--max-line-length=100",
            "--ignore=E203,W503"
        ]
        return self.run_command(command, "Code Linting")
    
    def run_type_checking(self):
        """Run type checking"""
        command = [
            "python", "-m", "mypy",
            "app/",
            "--ignore-missing-imports",
            "--no-strict-optional"
        ]
        return self.run_command(command, "Type Checking")
    
    def generate_report(self):
        """Generate comprehensive test report"""
        total_duration = time.time() - self.start_time
        
        report = {
            "timestamp": datetime.now().isoformat(),
            "total_duration": total_duration,
            "test_categories": self.results,
            "summary": self.generate_summary()
        }
        
        # Save JSON report
        with open("test_report.json", "w") as f:
            json.dump(report, f, indent=2)
        
        # Generate HTML report
        self.generate_html_report(report)
        
        return report
    
    def generate_summary(self):
        """Generate test summary"""
        total_tests = len(self.results)
        successful_tests = sum(1 for result in self.results.values() if result["success"])
        failed_tests = total_tests - successful_tests
        
        total_duration = sum(result["duration"] for result in self.results.values())
        
        return {
            "total_categories": total_tests,
            "successful_categories": successful_tests,
            "failed_categories": failed_tests,
            "success_rate": (successful_tests / total_tests * 100) if total_tests > 0 else 0,
            "total_duration": total_duration
        }
    
    def generate_html_report(self, report):
        """Generate HTML test report"""
        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <title>CustomerCareGPT Test Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        .header {{ background-color: #f0f0f0; padding: 20px; border-radius: 5px; }}
        .summary {{ background-color: #e8f5e8; padding: 15px; border-radius: 5px; margin: 20px 0; }}
        .category {{ margin: 20px 0; padding: 15px; border: 1px solid #ddd; border-radius: 5px; }}
        .success {{ background-color: #d4edda; border-color: #c3e6cb; }}
        .failure {{ background-color: #f8d7da; border-color: #f5c6cb; }}
        .details {{ margin-top: 10px; }}
        .stdout {{ background-color: #f8f9fa; padding: 10px; border-radius: 3px; font-family: monospace; white-space: pre-wrap; }}
        .stderr {{ background-color: #fff3cd; padding: 10px; border-radius: 3px; font-family: monospace; white-space: pre-wrap; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>CustomerCareGPT Test Report</h1>
        <p>Generated: {report['timestamp']}</p>
        <p>Total Duration: {report['total_duration']:.2f} seconds</p>
    </div>
    
    <div class="summary">
        <h2>Summary</h2>
        <p>Total Categories: {report['summary']['total_categories']}</p>
        <p>Successful: {report['summary']['successful_categories']}</p>
        <p>Failed: {report['summary']['failed_categories']}</p>
        <p>Success Rate: {report['summary']['success_rate']:.1f}%</p>
    </div>
    
    <h2>Test Categories</h2>
"""
        
        for category, result in report['test_categories'].items():
            status_class = "success" if result["success"] else "failure"
            status_text = "PASSED" if result["success"] else "FAILED"
            
            html_content += f"""
    <div class="category {status_class}">
        <h3>{category} - {status_text}</h3>
        <p>Duration: {result['duration']:.2f} seconds</p>
        <p>Return Code: {result['returncode']}</p>
        
        <div class="details">
            <h4>Standard Output:</h4>
            <div class="stdout">{result['stdout']}</div>
            
            <h4>Standard Error:</h4>
            <div class="stderr">{result['stderr']}</div>
        </div>
    </div>
"""
        
        html_content += """
</body>
</html>
"""
        
        with open("test_report.html", "w") as f:
            f.write(html_content)
    
    def run_all_tests(self):
        """Run all test categories"""
        print("Starting comprehensive test suite for CustomerCareGPT")
        print(f"Project root: {self.project_root}")
        
        # Run all test categories
        test_categories = [
            ("Unit Tests", self.run_unit_tests),
            ("Integration Tests", self.run_integration_tests),
            ("System Tests", self.run_system_tests),
            ("White-box Tests", self.run_whitebox_tests),
            ("Black-box Tests", self.run_blackbox_tests),
            ("Security Tests", self.run_security_tests),
            ("Performance Tests", self.run_performance_tests),
            ("Coverage Analysis", self.run_coverage_analysis),
            ("Code Linting", self.run_linting),
            ("Type Checking", self.run_type_checking)
        ]
        
        for category_name, test_function in test_categories:
            print(f"\nRunning {category_name}...")
            result = test_function()
            self.results[category_name] = result
            
            if result["success"]:
                print(f"✅ {category_name} PASSED")
            else:
                print(f"❌ {category_name} FAILED")
                print(f"Return code: {result['returncode']}")
                if result["stderr"]:
                    print(f"Error: {result['stderr']}")
        
        # Generate report
        report = self.generate_report()
        
        # Print final summary
        print(f"\n{'='*60}")
        print("FINAL SUMMARY")
        print(f"{'='*60}")
        print(f"Total Categories: {report['summary']['total_categories']}")
        print(f"Successful: {report['summary']['successful_categories']}")
        print(f"Failed: {report['summary']['failed_categories']}")
        print(f"Success Rate: {report['summary']['success_rate']:.1f}%")
        print(f"Total Duration: {report['summary']['total_duration']:.2f} seconds")
        
        # Print report locations
        print(f"\nReports generated:")
        print(f"- JSON: test_report.json")
        print(f"- HTML: test_report.html")
        print(f"- Coverage: htmlcov/index.html")
        
        return report

def main():
    """Main entry point"""
    runner = TestRunner()
    report = runner.run_all_tests()
    
    # Exit with appropriate code
    if report['summary']['failed_categories'] > 0:
        sys.exit(1)
    else:
        sys.exit(0)

if __name__ == "__main__":
    main()
