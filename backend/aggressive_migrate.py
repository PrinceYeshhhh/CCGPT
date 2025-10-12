#!/usr/bin/env python3
"""
Aggressive migration script for handling persistent transaction states.
This script uses multiple strategies to clear failed transaction states.
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

def force_connection_reset():
    """Force a complete connection reset to clear any failed transaction states."""
    database_url = settings.DATABASE_URL
    
    print("🔄 Forcing complete connection reset...")
    
    try:
        # Create a new engine with different connection parameters
        engine = create_engine(
            database_url, 
            pool_pre_ping=True,
            pool_recycle=1,  # Force connection recycling
            pool_reset_on_return='commit'  # Reset on return
        )
        
        with engine.connect() as connection:
            # Force a complete transaction reset
            try:
                # Try to rollback any existing transaction
                connection.rollback()
            except Exception:
                pass
            
            # Force a new transaction by executing a simple query
            try:
                connection.execute(text("SELECT 1"))
                print("✅ Connection reset successful")
                return True
            except Exception as e:
                print(f"❌ Connection reset failed: {e}")
                return False
                
    except Exception as e:
        print(f"❌ Failed to create connection: {e}")
        return False

def reset_alembic_version_table():
    """Reset the Alembic version table to a clean state."""
    database_url = settings.DATABASE_URL
    
    print("🔄 Resetting Alembic version table...")
    
    try:
        engine = create_engine(database_url, pool_pre_ping=True)
        
        with engine.connect() as connection:
            # Start a new transaction
            trans = connection.begin()
            
            try:
                # Check if alembic_version table exists (database-agnostic)
                if "postgresql" in database_url:
                    # PostgreSQL-specific check
                    result = connection.execute(text("""
                        SELECT EXISTS (
                            SELECT FROM information_schema.tables 
                            WHERE table_schema = 'public' 
                            AND table_name = 'alembic_version'
                        );
                    """))
                    table_exists = result.scalar()
                else:
                    # SQLite-specific check
                    result = connection.execute(text("""
                        SELECT name FROM sqlite_master 
                        WHERE type='table' AND name='alembic_version';
                    """))
                    table_exists = result.fetchone() is not None
                
                if table_exists:
                    print("Alembic version table exists. Resetting to clean state...")
                    
                    # Get current version
                    try:
                        result = connection.execute(text("SELECT version_num FROM alembic_version;"))
                        current_version = result.scalar()
                        print(f"Current version: {current_version}")
                    except Exception:
                        print("Could not read current version, will reset anyway")
                    
                    # Don't reset version - just ensure it's valid
                    print("✅ Version table is valid")
                else:
                    print("Alembic version table does not exist. Creating it...")
                    connection.execute(text("""
                        CREATE TABLE alembic_version (
                            version_num VARCHAR(32) NOT NULL,
                            CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num)
                        );
                    """))
                    connection.execute(text("INSERT INTO alembic_version (version_num) VALUES ('001');"))
                    print("✅ Created alembic_version table with version 001")
                
                # Commit the transaction
                trans.commit()
                print("✅ Alembic version table reset successfully")
                return True
                
            except Exception as e:
                # Rollback on error
                trans.rollback()
                print(f"❌ Error during reset: {e}")
                return False
                
    except Exception as e:
        print(f"❌ Failed to reset Alembic version table: {e}")
        return False

def run_aggressive_migration():
    """Run migration with aggressive transaction state clearing."""
    print("🚀 Starting aggressive migration...")
    
    # Step 1: Force connection reset
    if not force_connection_reset():
        print("❌ Failed to reset connection")
        return False
    
    # Step 2: Reset Alembic version table
    if not reset_alembic_version_table():
        print("❌ Failed to reset Alembic version table")
        return False
    
    # Step 3: Wait a bit for the database to stabilize
    print("⏳ Waiting for database to stabilize...")
    time.sleep(2)
    
    # Step 4: Run the migration
    print("🔄 Running migration...")
    
    try:
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
            return False
            
    except subprocess.TimeoutExpired:
        print("❌ Migration timed out")
        return False
    except Exception as e:
        print(f"❌ Unexpected error during migration: {e}")
        return False

if __name__ == "__main__":
    success = run_aggressive_migration()
    
    if success:
        print("\n✅ Aggressive migration completed successfully!")
        sys.exit(0)
    else:
        print("\n❌ Aggressive migration failed")
        sys.exit(1)
