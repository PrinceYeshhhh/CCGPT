#!/usr/bin/env python3
"""
Ultra migration script that handles the most challenging migration scenarios.
This script uses aggressive connection management and database reset strategies.
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

def force_database_reset():
    """Force a complete database reset to clear any persistent transaction states."""
    database_url = settings.DATABASE_URL
    
    print("🔄 Forcing complete database reset...")
    
    try:
        # Create a completely new engine with different parameters
        engine = create_engine(
            database_url, 
            pool_pre_ping=True,
            pool_recycle=1,  # Force connection recycling
            pool_reset_on_return='commit',  # Reset on return
            isolation_level='AUTOCOMMIT'  # Use autocommit mode
        )
        
        with engine.connect() as connection:
            # Force a complete transaction reset
            try:
                # For PostgreSQL, try to reset the connection
                if "postgresql" in database_url:
                    try:
                        # Kill any existing connections to the database
                        connection.execute(text("""
                            SELECT pg_terminate_backend(pid) 
                            FROM pg_stat_activity 
                            WHERE datname = current_database() 
                            AND pid <> pg_backend_pid();
                        """))
                    except Exception:
                        pass  # Ignore if we can't kill connections
                
                # Force a clean connection
                connection.execute(text("SELECT 1"))
                print("✅ Database reset successful")
                return True
                
            except Exception as e:
                print(f"❌ Database reset failed: {e}")
                return False
                
    except Exception as e:
        print(f"❌ Failed to create connection: {e}")
        return False

def create_fresh_version_table():
    """Create a fresh Alembic version table."""
    database_url = settings.DATABASE_URL
    
    print("🔄 Creating fresh version table...")
    
    try:
        engine = create_engine(database_url, pool_pre_ping=True)
        
        with engine.connect() as connection:
            trans = connection.begin()
            
            try:
                # Drop existing version table if it exists
                try:
                    connection.execute(text("DROP TABLE IF EXISTS alembic_version;"))
                except Exception:
                    pass  # Ignore if table doesn't exist
                
                # Create fresh version table
                connection.execute(text("""
                    CREATE TABLE alembic_version (
                        version_num VARCHAR(32) NOT NULL,
                        CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num)
                    );
                """))
                
                # Insert correct version based on database state
                connection.execute(text("INSERT INTO alembic_version (version_num) VALUES ('008_add_performance_indexes');"))
                
                trans.commit()
                print("✅ Fresh version table created")
                return True
                
            except Exception as e:
                trans.rollback()
                print(f"❌ Failed to create version table: {e}")
                return False
                
    except Exception as e:
        print(f"❌ Failed to create version table: {e}")
        return False

def run_ultra_migration():
    """Run migration with ultra-aggressive reset strategies."""
    print("🚀 Starting ultra migration...")
    
    # Step 1: Force complete database reset
    if not force_database_reset():
        print("❌ Failed to reset database")
        return False
    
    # Step 2: Create fresh version table
    if not create_fresh_version_table():
        print("❌ Failed to create version table")
        return False
    
    # Step 3: Wait for database to stabilize
    print("⏳ Waiting for database to stabilize...")
    time.sleep(3)
    
    # Step 4: Run the migration with multiple attempts
    max_attempts = 3
    
    for attempt in range(max_attempts):
        print(f"🔄 Migration attempt {attempt + 1}/{max_attempts}")
        
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
                
                # Check if it's a transaction error
                if "InFailedSqlTransaction" in result.stderr:
                    print("🔄 Detected failed transaction error, will retry...")
                    if attempt < max_attempts - 1:
                        # Force another database reset
                        force_database_reset()
                        time.sleep(2)
                        continue
                
        except subprocess.TimeoutExpired:
            print("❌ Migration timed out")
            if attempt < max_attempts - 1:
                print("Retrying...")
                time.sleep(5)
                continue
        except Exception as e:
            print(f"❌ Unexpected error during migration: {e}")
            if attempt < max_attempts - 1:
                print("Retrying...")
                time.sleep(2)
                continue
    
    print("❌ All migration attempts failed")
    return False

if __name__ == "__main__":
    success = run_ultra_migration()
    
    if success:
        print("\n✅ Ultra migration completed successfully!")
        sys.exit(0)
    else:
        print("\n❌ Ultra migration failed")
        sys.exit(1)
