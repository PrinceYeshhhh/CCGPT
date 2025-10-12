#!/usr/bin/env python3
"""
Fix PostgreSQL connection issues in Alembic environment.
This script ensures proper PostgreSQL connection parameters.
"""

import os
import sys

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def fix_postgresql_connection():
    """Fix PostgreSQL connection parameters in Alembic environment."""
    print("Fixing PostgreSQL connection parameters...")
    
    alembic_env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'alembic', 'env.py')
    
    if not os.path.exists(alembic_env_path):
        print("ERROR: Alembic env.py not found")
        return False
    
    # Read the current file
    with open(alembic_env_path, 'r') as f:
        content = f.read()
    
    # Check if the fix is already applied
    if "default_transaction_isolation='read committed'" in content:
        print("SUCCESS: PostgreSQL connection fix already applied")
        return True
    
    # Apply the fix
    old_pattern = 'default_transaction_isolation=read_committed'
    new_pattern = "default_transaction_isolation='read committed'"
    
    if old_pattern in content:
        content = content.replace(old_pattern, new_pattern)
        
        # Write the fixed content back
        with open(alembic_env_path, 'w') as f:
            f.write(content)
        
        print("SUCCESS: PostgreSQL connection parameters fixed")
        return True
    else:
        print("WARNING: PostgreSQL connection pattern not found - may already be fixed")
        return True

if __name__ == "__main__":
    success = fix_postgresql_connection()
    
    if success:
        print("\nSUCCESS: PostgreSQL connection fix completed!")
        sys.exit(0)
    else:
        print("\nERROR: PostgreSQL connection fix failed!")
        sys.exit(1)
