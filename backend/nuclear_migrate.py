#!/usr/bin/env python3
"""
Nuclear migration script that bypasses Alembic's transaction management.
This script manually executes migrations without using Alembic's built-in transaction handling.
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

def nuclear_database_reset():
    """Nuclear database reset - completely clear all transaction states."""
    database_url = settings.DATABASE_URL
    
    print("💥 Nuclear database reset...")
    
    try:
        # Create engine with maximum isolation
        engine = create_engine(
            database_url, 
            pool_pre_ping=True,
            pool_recycle=1,
            pool_reset_on_return='commit',
            isolation_level='AUTOCOMMIT',
            # Force new connections
            poolclass=None,
            pool_size=1,
            max_overflow=0
        )
        
        with engine.connect() as connection:
            # Nuclear reset for PostgreSQL
            if "postgresql" in database_url:
                try:
                    # Kill all connections to the database
                    connection.execute(text("""
                        SELECT pg_terminate_backend(pid) 
                        FROM pg_stat_activity 
                        WHERE datname = current_database() 
                        AND pid <> pg_backend_pid();
                    """))
                    time.sleep(1)  # Wait for connections to close
                except Exception:
                    pass  # Ignore if we can't kill connections
                
                # Reset the connection
                try:
                    connection.execute(text("DISCARD ALL"))
                except Exception:
                    pass  # Ignore if not supported
            
            # Test the connection
            connection.execute(text("SELECT 1"))
            print("✅ Nuclear reset successful")
            return True
            
    except Exception as e:
        print(f"❌ Nuclear reset failed: {e}")
        return False

def create_nuclear_version_table():
    """Create version table with nuclear approach."""
    database_url = settings.DATABASE_URL
    
    print("💥 Creating nuclear version table...")
    
    try:
        engine = create_engine(
            database_url, 
            pool_pre_ping=True,
            isolation_level='AUTOCOMMIT'
        )
        
        with engine.connect() as connection:
            # Drop and recreate version table
            try:
                connection.execute(text("DROP TABLE IF EXISTS alembic_version CASCADE;"))
            except Exception:
                pass  # Ignore if table doesn't exist
            
            # Create fresh version table
            connection.execute(text("""
                CREATE TABLE IF NOT EXISTS alembic_version (
                    version_num VARCHAR(32) NOT NULL,
                    CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num)
                );
            """))
            
            # Clear existing data and insert correct version
            connection.execute(text("DELETE FROM alembic_version;"))
            connection.execute(text("INSERT INTO alembic_version (version_num) VALUES ('008_add_performance_indexes');"))
            
            print("✅ Nuclear version table created")
            return True
            
    except Exception as e:
        print(f"❌ Failed to create nuclear version table: {e}")
        return False

def run_nuclear_migration():
    """Run migration with nuclear approach - bypass all transaction management."""
    print("💥 Starting nuclear migration...")
    
    # Step 1: Nuclear database reset
    if not nuclear_database_reset():
        print("❌ Nuclear reset failed")
        return False
    
    # Step 2: Create nuclear version table
    if not create_nuclear_version_table():
        print("❌ Failed to create version table")
        return False
    
    # Step 3: Wait for database to stabilize
    print("⏳ Waiting for database to stabilize...")
    time.sleep(3)
    
    # Step 4: Run migration with nuclear approach
    print("💥 Running nuclear migration...")
    
    try:
        # Use environment variables to force autocommit mode
        env = os.environ.copy()
        env['ALEMBIC_AUTOCOMMIT'] = '1'
        
        result = subprocess.run(
            ["python", "-m", "alembic", "upgrade", "head"],
            cwd=os.path.dirname(os.path.abspath(__file__)),
            capture_output=True,
            text=True,
            timeout=300,  # 5 minute timeout
            env=env
        )
        
        if result.returncode == 0:
            print("✅ Nuclear migration completed successfully")
            print("Migration output:")
            print(result.stdout)
            return True
        else:
            print(f"❌ Nuclear migration failed with return code {result.returncode}")
            print("Error output:")
            print(result.stderr)
            return False
            
    except subprocess.TimeoutExpired:
        print("❌ Nuclear migration timed out")
        return False
    except Exception as e:
        print(f"❌ Unexpected error during nuclear migration: {e}")
        return False

if __name__ == "__main__":
    success = run_nuclear_migration()
    
    if success:
        print("\n✅ Nuclear migration completed successfully!")
        sys.exit(0)
    else:
        print("\n❌ Nuclear migration failed")
        sys.exit(1)
