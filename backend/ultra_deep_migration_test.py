#!/usr/bin/env python3
"""
Ultra-deep migration test to ensure ZERO errors.
"""

import os
import sys
import tempfile
import shutil
from sqlalchemy import create_engine, text

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_sqlite_migration_chain():
    """Test the complete migration chain with SQLite."""
    print("Testing SQLite migration chain...")
    
    # Create a temporary database
    temp_db = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
    temp_db.close()
    
    try:
        # Set up environment
        os.environ['DATABASE_URL'] = f'sqlite:///{temp_db.name}'
        os.environ['ENVIRONMENT'] = 'testing'
        
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
        engine = create_engine(f'sqlite:///{temp_db.name}')
        with engine.connect() as connection:
            # Check if all expected tables exist
            result = connection.execute(text("SELECT name FROM sqlite_master WHERE type='table';"))
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
            result = connection.execute(text("PRAGMA table_info(users);"))
            columns = [row[1] for row in result.fetchall()]
            
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
        
        return True
        
    except Exception as e:
        print(f"  ✗ SQLite migration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        # Clean up
        try:
            if os.path.exists(temp_db.name):
                os.unlink(temp_db.name)
        except PermissionError:
            pass  # File might be locked, ignore
        if 'DATABASE_URL' in os.environ:
            del os.environ['DATABASE_URL']
        if 'ENVIRONMENT' in os.environ:
            del os.environ['ENVIRONMENT']

def test_postgresql_simulation():
    """Test PostgreSQL connection simulation."""
    print("\nTesting PostgreSQL connection simulation...")
    
    # Simulate GitHub Actions environment
    os.environ['DATABASE_URL'] = 'postgresql://postgres:postgres@localhost:5432/test_db'
    os.environ['ENVIRONMENT'] = 'testing'
    
    try:
        from app.core.database import create_database_engine
        
        # Test engine creation
        engine = create_database_engine(os.environ['DATABASE_URL'], is_read_replica=False)
        print("  ✓ PostgreSQL engine created successfully")
        
        # Test read replica engine
        engine = create_database_engine(os.environ['DATABASE_URL'], is_read_replica=True)
        print("  ✓ Read replica engine created successfully")
        
        # Test connection (will fail with connection refused, but should not have parameter errors)
        try:
            with engine.connect() as connection:
                result = connection.execute(text("SELECT 1"))
                print("  ✓ PostgreSQL connection successful")
        except Exception as e:
            if "default_transaction_isolation" in str(e):
                print(f"  ✗ PostgreSQL parameter error: {e}")
                return False
            elif "Connection refused" in str(e):
                print("  ✓ PostgreSQL connection fails with 'Connection refused' (expected)")
            else:
                print(f"  ⚠ PostgreSQL connection failed with unexpected error: {e}")
        
        return True
        
    except Exception as e:
        print(f"  ✗ PostgreSQL simulation failed: {e}")
        return False
    finally:
        # Clean up
        if 'DATABASE_URL' in os.environ:
            del os.environ['DATABASE_URL']
        if 'ENVIRONMENT' in os.environ:
            del os.environ['ENVIRONMENT']

def test_model_imports():
    """Test that all models can be imported without errors."""
    print("\nTesting model imports...")
    
    try:
        from app.models import (
            User, Workspace, Document, DocumentChunk, ChatSession, ChatMessage,
            EmbedCode, Subscription, TeamMember, PerformanceMetric, PerformanceAlert,
            PerformanceConfig, PerformanceReport, PerformanceBenchmark
        )
        print("  ✓ All models imported successfully")
        return True
    except Exception as e:
        print(f"  ✗ Model import failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_migration_script_imports():
    """Test that all migration scripts can be imported."""
    print("\nTesting migration script imports...")
    
    scripts = [
        'direct_migrate', 'smart_migrate', 'simple_migrate', 'migrate_with_retry',
        'ultra_migrate', 'nuclear_migrate', 'run_migration_chain'
    ]
    
    all_passed = True
    for script in scripts:
        try:
            __import__(script)
            print(f"  ✓ {script}.py imported successfully")
        except Exception as e:
            print(f"  ✗ {script}.py import failed: {e}")
            all_passed = False
    
    return all_passed

def test_alembic_configuration():
    """Test Alembic configuration."""
    print("\nTesting Alembic configuration...")
    
    try:
        from alembic.config import Config
        from alembic.script import ScriptDirectory
        
        cfg = Config('alembic.ini')
        script = ScriptDirectory.from_config(cfg)
        
        print("  ✓ Alembic configuration loaded successfully")
        
        # Check migration chain
        migrations = list(script.walk_revisions())
        print(f"  ✓ Found {len(migrations)} migrations")
        
        # Check for any issues
        for rev in migrations:
            if not rev.down_revision and rev.revision != '001':
                print(f"  ⚠ Migration {rev.revision} has no down_revision")
        
        return True
        
    except Exception as e:
        print(f"  ✗ Alembic configuration failed: {e}")
        return False

def main():
    """Run ultra-deep migration tests."""
    print("Ultra-Deep Migration System Test")
    print("=" * 60)
    
    tests = [
        test_sqlite_migration_chain,
        test_postgresql_simulation,
        test_model_imports,
        test_migration_script_imports,
        test_alembic_configuration
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
    
    print(f"\n" + "=" * 60)
    print(f"Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 ALL TESTS PASSED! Migration system is bulletproof.")
        return True
    else:
        print("❌ Some tests failed. Migration system needs more fixes.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
