#!/usr/bin/env python3
"""
Analyze the actual database state to determine what migration version it should be at.
"""

import os
import sys
from sqlalchemy import create_engine, text

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.config import settings

def analyze_database_state():
    """Analyze the actual database state to determine the correct migration version."""
    database_url = settings.DATABASE_URL
    
    try:
        engine = create_engine(database_url)
        with engine.connect() as connection:
            print("🔍 Analyzing database state...")
            print("=" * 60)
            
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
            print(f"📊 Existing tables: {tables}")
            
            # Check users table columns in detail
            if "postgresql" in database_url:
                result = connection.execute(text("""
                    SELECT column_name, data_type, is_nullable
                    FROM information_schema.columns 
                    WHERE table_name = 'users' 
                    ORDER BY ordinal_position;
                """))
            else:
                result = connection.execute(text("PRAGMA table_info(users);"))
            
            if "postgresql" in database_url:
                user_columns = [row[0] for row in result.fetchall()]
            else:
                user_columns = [row[1] for row in result.fetchall()]  # SQLite uses different column index
            print(f"📊 Users table columns: {user_columns}")
            
            # Determine likely migration state based on columns
            migration_state = "unknown"
            
            if 'mobile_phone' in user_columns and 'phone_verified' in user_columns:
                if 'email_verification_token' in user_columns and 'two_factor_secret' in user_columns:
                    if 'preferences' in user_columns and 'theme' in user_columns:
                        if 'performance_metrics' in tables:
                            migration_state = "008_add_performance_indexes"  # Latest
                        else:
                            migration_state = "007_create_missing_tables"
                    else:
                        migration_state = "005_add_email_verification_fields"
                else:
                    migration_state = "004_add_mobile_phone_unique"
            elif 'workspace_id' in user_columns:
                migration_state = "003_add_subscriptions_table"
            else:
                migration_state = "001_create_users_table"
            
            print(f"\n🎯 Detected migration state: {migration_state}")
            
            # Check current Alembic version
            result = connection.execute(text("SELECT version_num FROM alembic_version;"))
            current_version = result.scalar()
            print(f"📊 Current Alembic version: {current_version}")
            
            if current_version != migration_state:
                print(f"⚠️  VERSION MISMATCH DETECTED!")
                print(f"   Database state suggests: {migration_state}")
                print(f"   Alembic thinks it's at: {current_version}")
                print(f"   This explains the circular dependency error!")
            else:
                print(f"✅ Version matches database state")
            
    except Exception as e:
        print(f"Error analyzing database state: {e}")

if __name__ == "__main__":
    analyze_database_state()
