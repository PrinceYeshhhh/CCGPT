#!/usr/bin/env python3
"""
Simple migration script for CI/CD environments.
This script provides a clean, simple migration approach.
"""

import os
import sys
import subprocess

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def run_simple_migration():
    """Run a simple migration without complex retry logic."""
    print("Starting simple migration...")
    
    try:
        # Run the migration
        result = subprocess.run(
            ["python", "-m", "alembic", "upgrade", "head"],
            cwd=os.path.dirname(os.path.abspath(__file__)),
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout
        )
        
        if result.returncode == 0:
            print("SUCCESS: Migration completed successfully")
            print("Migration output:")
            print(result.stdout)
            return True
        else:
            print(f"FAILED: Migration failed with return code {result.returncode}")
            print("Error output:")
            print(result.stderr)
            return False
            
    except subprocess.TimeoutExpired:
        print("TIMEOUT: Migration timed out")
        return False
    except Exception as e:
        print(f"ERROR: Unexpected error during migration: {e}")
        return False

if __name__ == "__main__":
    success = run_simple_migration()
    
    if success:
        print("\nSUCCESS: Migration completed successfully!")
        sys.exit(0)
    else:
        print("\nFAILED: Migration failed")
        sys.exit(1)
