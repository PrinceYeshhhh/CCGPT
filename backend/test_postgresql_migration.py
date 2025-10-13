#!/usr/bin/env python3
"""
Test PostgreSQL migration system with real database.
"""

import os
import sys
import psycopg2
from sqlalchemy import create_engine, text

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def create_test_database():
    """Create the test database if it doesn't exist."""
    print("Creating test database...")
    
    try:
        # Connect to PostgreSQL server (not to a specific database)
        conn = psycopg2.connect(
            host="localhost",
            port=5432,
            user="postgres",
            password="postgres",  # Default password
            database="postgres"   # Connect to default postgres database
        )
        conn.autocommit = True
        
        cursor = conn.cursor()
        
        # Check if test_db exists
        cursor.execute("SELECT 1 FROM pg_database WHERE datname = 'test_db';")
        exists = cursor.fetchone()
        
        if not exists:
            cursor.execute("CREATE DATABASE test_db;")
            print("✓ Database 'test_db' created successfully")
        else:
            print("✓ Database 'test_db' already exists")
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"✗ Failed to create database: {e}")
        return False

def test_postgresql_migration():
    """Test migration system with PostgreSQL."""
    print("\nTesting PostgreSQL migration system...")
    
    # Set environment variables
    os.environ['DATABASE_URL'] = 'postgresql://postgres:postgres@localhost:5432/test_db'
    os.environ['ENVIRONMENT'] = 'testing'
    
    try:
        # Test direct migration
        print("  Testing direct migration...")
        import subprocess
        result = subprocess.run(
            ["python", "direct_migrate.py"],
            cwd=os.path.dirname(os.path.abspath(__file__)),
            capture_output=True,
            text=True,
            timeout=60
        )
        
        if result.returncode != 0:
            print(f"  ✗ Direct migration failed: {result.stderr}")
            return False
        
        print("  ✓ Direct migration successful")
        
        # Test Alembic migration
        print("  Testing Alembic migration...")
        result = subprocess.run(
            ["python", "-m", "alembic", "upgrade", "head"],
            cwd=os.path.dirname(os.path.abspath(__file__)),
            capture_output=True,
            text=True,
            timeout=60
        )
        
        if result.returncode != 0:
            print(f"  ✗ Alembic migration failed: {result.stderr}")
            return False
        
        print("  ✓ Alembic migration successful")
        
        # Verify database structure
        print("  Verifying database structure...")
        engine = create_engine('postgresql://postgres:postgres@localhost:5432/test_db')
        with engine.connect() as connection:
            # Check if all expected tables exist
            result = connection.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
                ORDER BY table_name;
            """))
            tables = [row[0] for row in result.fetchall()]
            
            expected_tables = [
                'alembic_version', 'users', 'workspaces', 'documents', 'document_chunks',
                'chat_sessions', 'chat_messages', 'embed_codes', 'subscriptions',
                'team_members', 'performance_metrics', 'performance_alerts',
                'performance_configs', 'performance_reports', 'performance_benchmarks'
            ]
            
            missing_tables = [table for table in expected_tables if table not in tables]
            if missing_tables:
                print(f"  ✗ Missing tables: {missing_tables}")
                return False
            
            print("  ✓ All expected tables exist")
            
            # Check users table structure
            result = connection.execute(text("""
                SELECT column_name 
                FROM information_schema.columns
                WHERE table_name = 'users'
                ORDER BY ordinal_position;
            """))
            columns = [row[0] for row in result.fetchall()]
            
            expected_columns = [
                'id', 'email', 'hashed_password', 'full_name', 'is_active', 'is_superuser',
                'created_at', 'updated_at', 'business_name', 'business_domain', 'subscription_plan',
                'workspace_id', 'mobile_phone', 'phone_verified', 'email_verified',
                'email_verification_token', 'email_verification_sent_at', 'username',
                'two_factor_secret', 'two_factor_enabled', 'phone_verification_token',
                'phone_verification_sent_at', 'password_reset_token', 'password_reset_sent_at',
                'last_login_at', 'login_attempts', 'locked_until', 'preferences', 'theme',
                'language', 'timezone', 'notification_settings'
            ]
            
            missing_columns = [col for col in expected_columns if col not in columns]
            if missing_columns:
                print(f"  ✗ Missing columns in users table: {missing_columns}")
                return False
            
            print("  ✓ Users table has all expected columns")
            
            # Test a simple query
            result = connection.execute(text("SELECT COUNT(*) FROM users;"))
            count = result.scalar()
            print(f"  ✓ Users table is accessible (count: {count})")
        
        return True
        
    except Exception as e:
        print(f"  ✗ PostgreSQL migration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        # Clean up environment
        if 'DATABASE_URL' in os.environ:
            del os.environ['DATABASE_URL']
        if 'ENVIRONMENT' in os.environ:
            del os.environ['ENVIRONMENT']

def main():
    """Run PostgreSQL migration test."""
    print("PostgreSQL Migration System Test")
    print("=" * 50)
    
    if not create_test_database():
        print("Failed to create test database. Exiting.")
        return False
    
    if test_postgresql_migration():
        print("\n🎉 ALL TESTS PASSED! PostgreSQL migration system works perfectly!")
        return True
    else:
        print("\n❌ Some tests failed.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
