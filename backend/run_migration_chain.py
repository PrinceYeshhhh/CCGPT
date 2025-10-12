#!/usr/bin/env python3
"""
Migration chain runner for GitHub Actions.
This script runs the migration chain with proper error handling and PowerShell compatibility.
"""

import os
import sys
import subprocess
import time

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def run_migration_script(script_name, description):
    """Run a migration script and return success status."""
    print(f"Running {description}...")
    
    try:
        result = subprocess.run(
            ["python", script_name],
            cwd=os.path.dirname(os.path.abspath(__file__)),
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout
        )
        
        if result.returncode == 0:
            print(f"SUCCESS: {description} completed successfully")
            return True
        else:
            print(f"FAILED: {description} failed with return code {result.returncode}")
            print("Error output:")
            print(result.stderr)
            return False
            
    except subprocess.TimeoutExpired:
        print(f"TIMEOUT: {description} timed out")
        return False
    except Exception as e:
        print(f"ERROR: {description} failed with error: {e}")
        return False

def run_migration_chain():
    """Run the complete migration chain with fallback strategies."""
    print("Starting migration chain...")
    print("=" * 60)
    
    # Migration chain with fallback strategies
    # Direct migration first since it bypasses Alembic and avoids PostgreSQL connection issues
    migration_scripts = [
        ("direct_migrate.py", "Direct migration (bypasses Alembic)"),
        ("validate_migration_state.py", "Migration state validation"),
        ("nuclear_migrate.py", "Nuclear migration (aggressive reset)"),
        ("smart_migrate.py", "Smart migration (intelligent detection)"),
        ("simple_migrate.py", "Simple migration (direct Alembic)"),
        ("migrate_with_retry.py", "Retry migration (complex retry logic)"),
        ("ultra_migrate.py", "Ultra migration (ultra-aggressive reset)")
    ]
    
    # Try each migration script in order
    for script_name, description in migration_scripts:
        if run_migration_script(script_name, description):
            print(f"\nSUCCESS: Migration chain completed successfully with: {description}")
            return True
        else:
            print(f"WARNING: {description} failed, trying next migration strategy...")
            time.sleep(2)  # Wait before trying next strategy
    
    print("\nFAILED: All migration strategies failed")
    return False

if __name__ == "__main__":
    success = run_migration_chain()
    
    if success:
        print("\nSUCCESS: Migration chain completed successfully!")
        sys.exit(0)
    else:
        print("\nFAILED: Migration chain failed")
        sys.exit(1)
