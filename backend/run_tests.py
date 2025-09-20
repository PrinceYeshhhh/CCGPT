#!/usr/bin/env python3
"""
Test runner for CustomerCareGPT
Runs all tests with proper configuration and reporting
"""

import os
import sys
import subprocess
import argparse
from pathlib import Path

def run_command(command, cwd=None):
    """Run a command and return the result."""
    try:
        result = subprocess.run(
            command,
            shell=True,
            cwd=cwd,
            capture_output=True,
            text=True,
            check=True
        )
        return True, result.stdout, result.stderr
    except subprocess.CalledProcessError as e:
        return False, e.stdout, e.stderr

def setup_test_environment():
    """Setup test environment variables."""
    test_env = {
        "TESTING": "true",
        "DATABASE_URL": "sqlite:///./test.db",
        "REDIS_URL": "redis://localhost:6379/1",
        "SECRET_KEY": "test-secret-key",
        "GEMINI_API_KEY": "test-gemini-key",
        "STRIPE_API_KEY": "test-stripe-key",
        "ENVIRONMENT": "testing",
        "SECRETS_PROVIDER": "env"
    }
    
    for key, value in test_env.items():
        os.environ[key] = value

def run_linting():
    """Run code linting."""
    print("🔍 Running code linting...")
    
    # Run flake8
    success, stdout, stderr = run_command("flake8 app/ --count --select=E9,F63,F7,F82 --show-source --statistics")
    if not success:
        print("❌ Linting failed:")
        print(stderr)
        return False
    
    # Run mypy
    success, stdout, stderr = run_command("mypy app/ --ignore-missing-imports")
    if not success:
        print("⚠️  Type checking warnings:")
        print(stderr)
    
    print("✅ Linting completed")
    return True

def run_unit_tests():
    """Run unit tests."""
    print("🧪 Running unit tests...")
    
    success, stdout, stderr = run_command("pytest tests/ -v --cov=app --cov-report=html --cov-report=term")
    
    if success:
        print("✅ Unit tests passed")
        print(stdout)
        return True
    else:
        print("❌ Unit tests failed:")
        print(stderr)
        return False

def run_integration_tests():
    """Run integration tests."""
    print("🔗 Running integration tests...")
    
    success, stdout, stderr = run_command("pytest tests/test_integration.py -v")
    
    if success:
        print("✅ Integration tests passed")
        print(stdout)
        return True
    else:
        print("❌ Integration tests failed:")
        print(stderr)
        return False

def run_e2e_tests():
    """Run end-to-end tests."""
    print("🚀 Running end-to-end tests...")
    
    success, stdout, stderr = run_command("pytest tests/test_e2e_workflows.py -v")
    
    if success:
        print("✅ End-to-end tests passed")
        print(stdout)
        return True
    else:
        print("❌ End-to-end tests failed:")
        print(stderr)
        return False

def run_all_tests():
    """Run all tests."""
    print("🎯 Running all tests...")
    
    success, stdout, stderr = run_command("pytest tests/ -v --cov=app --cov-report=html --cov-report=term --tb=short")
    
    if success:
        print("✅ All tests passed")
        print(stdout)
        return True
    else:
        print("❌ Some tests failed:")
        print(stderr)
        return False

def main():
    """Main test runner."""
    parser = argparse.ArgumentParser(description="CustomerCareGPT Test Runner")
    parser.add_argument("--lint", action="store_true", help="Run linting only")
    parser.add_argument("--unit", action="store_true", help="Run unit tests only")
    parser.add_argument("--integration", action="store_true", help="Run integration tests only")
    parser.add_argument("--e2e", action="store_true", help="Run end-to-end tests only")
    parser.add_argument("--all", action="store_true", help="Run all tests")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    
    args = parser.parse_args()
    
    # Setup test environment
    setup_test_environment()
    
    # Change to backend directory
    backend_dir = Path(__file__).parent
    os.chdir(backend_dir)
    
    success = True
    
    if args.lint:
        success = run_linting()
    elif args.unit:
        success = run_unit_tests()
    elif args.integration:
        success = run_integration_tests()
    elif args.e2e:
        success = run_e2e_tests()
    elif args.all:
        success = run_all_tests()
    else:
        # Default: run all tests
        print("Running all tests (default behavior)")
        success = run_all_tests()
    
    if success:
        print("\n🎉 All tests completed successfully!")
        sys.exit(0)
    else:
        print("\n💥 Some tests failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()
