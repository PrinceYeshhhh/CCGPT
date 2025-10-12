#!/usr/bin/env python3
"""
Smart migration script that detects current database state and migrates accordingly.
This script handles cases where the version table is out of sync with actual database state.
"""

import os
import sys
import subprocess
import time
from sqlalchemy import create_engine, text

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.config import settings

def detect_database_state():
    """Detect the actual current state of the database."""
    database_url = settings.DATABASE_URL
    
    print("🔍 Detecting database state...")
    
    try:
        engine = create_engine(database_url, pool_pre_ping=True)
        
        with engine.connect() as connection:
            # Check if alembic_version table exists
            if "postgresql" in database_url:
                result = connection.execute(text("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_schema = 'public' 
                        AND table_name = 'alembic_version'
                    );
                """))
                version_table_exists = result.scalar()
            else:
                result = connection.execute(text("""
                    SELECT name FROM sqlite_master 
                    WHERE type='table' AND name='alembic_version';
                """))
                version_table_exists = result.fetchone() is not None
            
            if not version_table_exists:
                print("📊 Alembic version table does not exist - this is a fresh database")
                # For fresh databases, we need to create the version table and start from the beginning
                return "fresh"
            
            # Get current version from table
            result = connection.execute(text("SELECT version_num FROM alembic_version;"))
            current_version = result.scalar()
            print(f"📊 Version table shows: {current_version}")
            
            # Check what tables actually exist
            if "postgresql" in database_url:
                result = connection.execute(text("""
                    SELECT table_name FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    ORDER BY table_name;
                """))
            else:
                result = connection.execute(text("""
                    SELECT name FROM sqlite_master 
                    WHERE type='table' AND name NOT LIKE 'sqlite_%'
                    ORDER BY name;
                """))
            
            existing_tables = [row[0] for row in result.fetchall()]
            print(f"📊 Existing tables: {existing_tables}")
            
            # Check for specific columns that indicate migration state
            if 'users' in existing_tables:
                result = connection.execute(text("PRAGMA table_info(users)"))
                user_columns = [row[1] for row in result.fetchall()]
                print(f"📊 Users table columns: {user_columns}")
                
                # Determine likely migration state based on columns
                if 'mobile_phone' in user_columns and 'phone_verified' in user_columns:
                    # Check for performance tables to determine if we're at the latest
                    if 'performance_metrics' in existing_tables:
                        return '008_add_performance_indexes'  # Latest migration
                    elif 'workspace_id' in user_columns:
                        return '003_add_subscriptions_table'  # After subscriptions
                    else:
                        return '004_add_mobile_phone_unique'  # After mobile phone
                elif 'workspace_id' in user_columns:
                    return '003_add_subscriptions_table'  # After subscriptions
                else:
                    return '001_create_users_table'  # Basic users table
            
            return current_version
            
    except Exception as e:
        print(f"❌ Failed to detect database state: {e}")
        return None

def set_correct_version(target_version):
    """Set the Alembic version table to the correct version."""
    database_url = settings.DATABASE_URL
    
    print(f"🔄 Setting version to {target_version}...")
    
    try:
        engine = create_engine(database_url, pool_pre_ping=True)
        
        with engine.connect() as connection:
            trans = connection.begin()
            
            try:
                if target_version == "fresh":
                    # Create the version table for fresh databases
                    connection.execute(text("""
                        CREATE TABLE alembic_version (
                            version_num VARCHAR(32) NOT NULL,
                            CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num)
                        );
                    """))
                    connection.execute(text("INSERT INTO alembic_version (version_num) VALUES ('001');"))
                    print("✅ Created version table and set to 001")
                else:
                    # Update existing version table
                    connection.execute(text("UPDATE alembic_version SET version_num = :version"), 
                                     {"version": target_version})
                    print(f"✅ Version set to {target_version}")
                
                trans.commit()
                return True
            except Exception as e:
                trans.rollback()
                print(f"❌ Failed to set version: {e}")
                return False
                
    except Exception as e:
        print(f"❌ Failed to set version: {e}")
        return False

def run_smart_migration():
    """Run migration with smart state detection."""
    print("🚀 Starting smart migration...")
    
    # Step 1: Detect current database state
    detected_version = detect_database_state()
    
    if detected_version is None:
        print("❌ Could not detect database state")
        return False
    
    print(f"📊 Detected database state: {detected_version}")
    
    # Step 2: Set correct version if needed
    if not set_correct_version(detected_version):
        print("❌ Failed to set correct version")
        return False
    
    # Step 3: Wait for database to stabilize
    print("⏳ Waiting for database to stabilize...")
    time.sleep(1)
    
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
    success = run_smart_migration()
    
    if success:
        print("\n✅ Smart migration completed successfully!")
        sys.exit(0)
    else:
        print("\n❌ Smart migration failed")
        sys.exit(1)
