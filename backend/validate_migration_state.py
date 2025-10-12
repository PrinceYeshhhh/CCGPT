#!/usr/bin/env python3
"""
Migration state validation script.
This script validates the database state before running migrations to prevent errors.
"""

import os
import sys
from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.config import settings

def validate_migration_state():
    """Validate the current migration state and detect potential issues."""
    database_url = settings.DATABASE_URL
    
    print("Validating migration state...")
    print("=" * 60)
    
    try:
        engine = create_engine(database_url)
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
            else:  # SQLite
                result = connection.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name='alembic_version';"))
                version_table_exists = result.fetchone() is not None
            
            if not version_table_exists:
                print("ERROR: Alembic version table does not exist")
                return False, "no_version_table"
            
            # Get current version
            result = connection.execute(text("SELECT version_num FROM alembic_version;"))
            current_version = result.scalar()
            print(f"Current Alembic version: {current_version}")
            
            # Check all tables
            if "postgresql" in database_url:
                result = connection.execute(text("""
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_schema = 'public'
                    ORDER BY table_name;
                """))
            else:  # SQLite
                result = connection.execute(text("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;"))
            
            tables = [row[0] for row in result.fetchall()]
            print(f"Existing tables: {len(tables)} tables")
            
            # Check users table columns
            if 'users' in tables:
                if "postgresql" in database_url:
                    result = connection.execute(text("""
                        SELECT column_name 
                        FROM information_schema.columns 
                        WHERE table_name = 'users' 
                        ORDER BY ordinal_position;
                    """))
                else:  # SQLite
                    result = connection.execute(text("PRAGMA table_info(users);"))
                
                user_columns = [row[0] for row in result.fetchall()]
                print(f"Users table columns: {len(user_columns)} columns")
                
                # Determine actual migration state based on columns
                actual_state = determine_migration_state(user_columns, tables)
                print(f"Actual database state: {actual_state}")
                
                # Check for version mismatch
                if current_version != actual_state:
                    print(f"WARNING: VERSION MISMATCH DETECTED!")
                    print(f"   Alembic thinks: {current_version}")
                    print(f"   Database shows: {actual_state}")
                    return False, "version_mismatch", current_version, actual_state
                else:
                    print(f"SUCCESS: Version matches database state")
            else:
                print("ERROR: Users table does not exist")
                return False, "no_users_table"
            
            # Check for potential circular dependency issues
            circular_dependency_risk = check_circular_dependency_risk(user_columns, current_version)
            if circular_dependency_risk:
                print(f"WARNING: CIRCULAR DEPENDENCY RISK DETECTED!")
                print(f"   Risk: {circular_dependency_risk}")
                return False, "circular_dependency_risk", circular_dependency_risk
            
            print("SUCCESS: Migration state validation passed")
            return True, "valid"
            
    except Exception as e:
        print(f"ERROR: Error validating migration state: {e}")
        return False, "validation_error", str(e)

def determine_migration_state(user_columns, tables):
    """Determine the actual migration state based on database structure."""
    # Check for latest features first
    if 'mobile_phone' in user_columns and 'phone_verified' in user_columns:
        if 'email_verification_token' in user_columns and 'two_factor_secret' in user_columns:
            if 'preferences' in user_columns and 'theme' in user_columns:
                if 'performance_metrics' in tables:
                    return '008_add_performance_indexes'  # Latest
                else:
                    return '007_create_missing_tables'
            else:
                return '005_add_email_verification_fields'
        else:
            return '004_add_mobile_phone_unique'
    elif 'workspace_id' in user_columns:
        return '003_add_subscriptions_table'
    else:
        return '001_create_users_table'

def check_circular_dependency_risk(user_columns, current_version):
    """Check for potential circular dependency risks."""
    # If we're at an early version but have advanced columns, there's a risk
    early_versions = ['001', '002', '003']
    advanced_columns = ['mobile_phone', 'phone_verified', 'email_verification_token', 'two_factor_secret']
    
    if any(version in current_version for version in early_versions):
        if any(column in user_columns for column in advanced_columns):
            return f"Database has advanced columns but Alembic is at early version {current_version}"
    
    return None

def fix_version_mismatch(current_version, actual_state):
    """Fix version mismatch by updating Alembic version table."""
    database_url = settings.DATABASE_URL
    
    print(f"Fixing version mismatch: {current_version} -> {actual_state}")
    
    try:
        engine = create_engine(database_url)
        with engine.connect() as connection:
            trans = connection.begin()
            
            try:
                connection.execute(text("UPDATE alembic_version SET version_num = :version"), 
                                 {"version": actual_state})
                trans.commit()
                print(f"SUCCESS: Version updated to {actual_state}")
                return True
            except Exception as e:
                trans.rollback()
                print(f"ERROR: Failed to update version: {e}")
                return False
                
    except Exception as e:
        print(f"ERROR: Error fixing version mismatch: {e}")
        return False

if __name__ == "__main__":
    result = validate_migration_state()
    
    if result[0]:  # Success
        print("\nSUCCESS: Migration state validation passed!")
        sys.exit(0)
    else:
        error_type = result[1]
        print(f"\nERROR: Migration state validation failed: {error_type}")
        
        if error_type == "version_mismatch" and len(result) > 3:
            current_version, actual_state = result[2], result[3]
            if fix_version_mismatch(current_version, actual_state):
                print("SUCCESS: Version mismatch fixed!")
                sys.exit(0)
        
        sys.exit(1)
