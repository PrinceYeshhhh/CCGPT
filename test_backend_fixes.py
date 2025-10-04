#!/usr/bin/env python3
"""
Quick test script to verify backend test fixes work locally
"""

import os
import sys
import subprocess
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def run_backend_tests():
    """Run a subset of backend tests to verify fixes."""
    logger.info("Testing backend fixes...")
    
    # Change to backend directory
    backend_dir = os.path.join(os.path.dirname(__file__), 'backend')
    if not os.path.isdir(backend_dir):
        logger.error(f"Backend directory not found at: {backend_dir}")
        return False
    
    # Set environment variables
    os.environ['PYTHONPATH'] = backend_dir
    os.environ['TESTING'] = 'true'
    os.environ['SKIP_PROBLEMATIC_TESTS'] = 'true'
    os.environ['SKIP_EXTERNAL_TESTS'] = 'true'
    
    # Run a small subset of tests first
    test_command = [
        sys.executable, '-m', 'pytest',
        'tests/unit/test_auth.py::TestAuthService::test_generate_jwt_token',
        'tests/unit/test_auth.py::TestAuthService::test_verify_jwt_token_valid',
        '--timeout=30',
        '--log-cli-level=INFO',
        '-v'
    ]
    
    logger.info(f"Running command: {' '.join(test_command)}")
    
    try:
        result = subprocess.run(test_command, cwd=backend_dir, check=False, capture_output=True, text=True)
        
        if result.returncode == 0:
            logger.info("✅ Backend test fixes working!")
            logger.info("Test output:")
            print(result.stdout)
            return True
        else:
            logger.error("❌ Backend tests still failing")
            logger.error("STDOUT:")
            print(result.stdout)
            logger.error("STDERR:")
            print(result.stderr)
            return False
            
    except Exception as e:
        logger.error(f"Error running tests: {e}")
        return False

if __name__ == "__main__":
    success = run_backend_tests()
    sys.exit(0 if success else 1)
