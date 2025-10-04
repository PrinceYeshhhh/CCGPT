#!/usr/bin/env python3
"""
Debug script to identify hanging tests locally
"""

import subprocess
import sys
import time
import signal
import os
from pathlib import Path

def run_with_timeout(command, timeout_seconds=300):
    """Run command with timeout"""
    print(f"Running: {' '.join(command)}")
    print(f"Timeout: {timeout_seconds} seconds")
    
    start_time = time.time()
    
    try:
        result = subprocess.run(
            command,
            timeout=timeout_seconds,
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent / "backend"
        )
        
        end_time = time.time()
        duration = end_time - start_time
        
        print(f"Command completed in {duration:.2f} seconds")
        print(f"Return code: {result.returncode}")
        
        if result.stdout:
            print("STDOUT:")
            print(result.stdout)
        
        if result.stderr:
            print("STDERR:")
            print(result.stderr)
            
        return result.returncode == 0
        
    except subprocess.TimeoutExpired:
        end_time = time.time()
        duration = end_time - start_time
        print(f"Command timed out after {duration:.2f} seconds")
        return False

def main():
    """Main debug function"""
    print("=== Test Debug Script ===")
    
    # Test 1: Run a single test file
    print("\n1. Testing single test file...")
    success = run_with_timeout([
        "python", "-m", "pytest", 
        "tests/test_simple.py", 
        "-v", 
        "--timeout=30",
        "--log-cli-level=DEBUG"
    ], timeout_seconds=60)
    
    if not success:
        print("❌ Single test file failed or timed out")
        return 1
    
    # Test 2: Run unit tests
    print("\n2. Testing unit tests...")
    success = run_with_timeout([
        "python", "-m", "pytest", 
        "tests/unit/", 
        "-v", 
        "--timeout=60",
        "--log-cli-level=DEBUG",
        "-k", "not slow and not integration"
    ], timeout_seconds=120)
    
    if not success:
        print("❌ Unit tests failed or timed out")
        return 1
    
    # Test 3: Run with parallel execution
    print("\n3. Testing with parallel execution...")
    success = run_with_timeout([
        "python", "-m", "pytest", 
        "tests/unit/", 
        "-v", 
        "--timeout=60",
        "-n", "auto",
        "--log-cli-level=DEBUG",
        "-k", "not slow and not integration"
    ], timeout_seconds=180)
    
    if not success:
        print("❌ Parallel tests failed or timed out")
        return 1
    
    print("\n✅ All tests completed successfully!")
    return 0

if __name__ == "__main__":
    sys.exit(main())
