#!/usr/bin/env python3
"""
Migration wrapper with retry logic and transaction recovery.
This script handles failed transaction states in CI/CD environments.
"""

import os
import sys
import subprocess
import time
from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError, InternalError

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.config import settings

def reset_database_connection():
    """Reset database connection to clear any failed transaction states."""
    database_url = settings.DATABASE_URL
    
    try:
        engine = create_engine(database_url, pool_pre_ping=True)
        
        with engine.connect() as connection:
            # Force a clean connection
            connection.execute(text("SELECT 1"))
            
            # For PostgreSQL, ensure we're in a clean state
            if "postgresql" in database_url:
                try:
                    # Check if we're in a failed transaction
                    result = connection.execute(text("SELECT txid_current();"))
                    print(f"Current transaction ID: {result.scalar()}")
                except Exception as e:
                    print(f"Transaction check failed: {e}")
                    # Try to reset the connection
                    connection.rollback()
                    
        print("✅ Database connection reset successfully")
        return True
        
    except Exception as e:
        print(f"❌ Failed to reset database connection: {e}")
        return False

def run_migration_with_retry():
    """Run Alembic migration with retry logic."""
    max_retries = 3
    
    for attempt in range(max_retries):
        print(f"\n🔄 Migration attempt {attempt + 1}/{max_retries}")
        
        # Reset database connection before each attempt
        if not reset_database_connection():
            print("❌ Failed to reset database connection")
            if attempt < max_retries - 1:
                print("Retrying...")
                time.sleep(2)
                continue
            else:
                return False
        
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
                print("✅ Migration completed successfully")
                print("Migration output:")
                print(result.stdout)
                return True
            else:
                print(f"❌ Migration failed with return code {result.returncode}")
                print("Error output:")
                print(result.stderr)
                
                # Check if it's a transaction error
                if "InFailedSqlTransaction" in result.stderr:
                    print("🔄 Detected failed transaction error, will retry...")
                    if attempt < max_retries - 1:
                        time.sleep(3)
                        continue
                
        except subprocess.TimeoutExpired:
            print("❌ Migration timed out")
            if attempt < max_retries - 1:
                print("Retrying...")
                time.sleep(5)
                continue
        except Exception as e:
            print(f"❌ Unexpected error during migration: {e}")
            if attempt < max_retries - 1:
                print("Retrying...")
                time.sleep(2)
                continue
    
    print("❌ All migration attempts failed")
    return False

if __name__ == "__main__":
    print("🚀 Starting migration with retry logic...")
    
    success = run_migration_with_retry()
    
    if success:
        print("\n✅ Migration completed successfully!")
        sys.exit(0)
    else:
        print("\n❌ Migration failed after all retry attempts")
        sys.exit(1)
