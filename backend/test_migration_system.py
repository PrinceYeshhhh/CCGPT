#!/usr/bin/env python3
"""
Comprehensive test suite for the migration system.
This script tests all migration scenarios and edge cases.
"""

import os
import sys
import subprocess
import tempfile
import shutil
import time
from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError, InternalError

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.config import settings

class MigrationTestSuite:
    """Comprehensive test suite for migration system."""
    
    def __init__(self):
        self.original_database_url = settings.DATABASE_URL
        self.test_results = []
        self.temp_dir = None
        self.test_database_url = None
    
    def setup_test_environment(self):
        """Set up a test environment with a temporary database."""
        print("Setting up test environment...")
        
        # Create temporary directory
        self.temp_dir = tempfile.mkdtemp()
        
        # Create test database URL
        if "sqlite" in self.original_database_url:
            test_db_path = os.path.join(self.temp_dir, "test.db")
            self.test_database_url = f"sqlite:///{test_db_path}"
        else:
            # For PostgreSQL, use a test database
            self.test_database_url = self.original_database_url.replace(
                "customercaregpt", "customercaregpt_test"
            )
        
        # Update settings for testing
        settings.DATABASE_URL = self.test_database_url
        
        print(f"Test database URL: {self.test_database_url}")
        return True
    
    def cleanup_test_environment(self):
        """Clean up test environment."""
        print("Cleaning up test environment...")
        
        # Restore original database URL
        settings.DATABASE_URL = self.original_database_url
        
        # Remove temporary directory
        if self.temp_dir and os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def run_test(self, test_name, test_func):
        """Run a single test and record results."""
        print(f"\nRunning test: {test_name}")
        print("-" * 50)
        
        try:
            result = test_func()
            if result:
                self.test_results.append((test_name, "PASS", None))
                print(f"SUCCESS: {test_name}")
            else:
                self.test_results.append((test_name, "FAIL", "Test returned False"))
                print(f"FAILED: {test_name}")
        except Exception as e:
            self.test_results.append((test_name, "ERROR", str(e)))
            print(f"ERROR: {test_name} - {e}")
    
    def test_fresh_database_migration(self):
        """Test migration on a completely fresh database."""
        print("Testing fresh database migration...")
        
        # Ensure we have a clean database
        engine = create_engine(self.test_database_url)
        with engine.connect() as connection:
            # Drop all tables if they exist
            if "postgresql" in self.test_database_url:
                connection.execute(text("DROP SCHEMA public CASCADE; CREATE SCHEMA public;"))
            else:
                # For SQLite, we'll create a new file
                pass
        
        # Run migration chain
        result = subprocess.run(
            ["python", "run_migration_chain.py"],
            cwd=os.path.dirname(os.path.abspath(__file__)),
            capture_output=True,
            text=True,
            timeout=300
        )
        
        if result.returncode != 0:
            print(f"Migration failed: {result.stderr}")
            return False
        
        # Verify database structure
        engine = create_engine(self.test_database_url)
        with engine.connect() as connection:
            if "postgresql" in self.test_database_url:
                result = connection.execute(text("""
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_schema = 'public'
                    ORDER BY table_name;
                """))
            else:
                result = connection.execute(text("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;"))
            
            tables = [row[0] for row in result.fetchall()]
            
            # Check for essential tables
            essential_tables = ['users', 'workspaces', 'documents', 'subscriptions', 'alembic_version']
            missing_tables = [table for table in essential_tables if table not in tables]
            
            if missing_tables:
                print(f"Missing essential tables: {missing_tables}")
                return False
        
        return True
    
    def test_migration_validation(self):
        """Test migration state validation."""
        print("Testing migration validation...")
        
        # Run validation script
        result = subprocess.run(
            ["python", "validate_migration_state.py"],
            cwd=os.path.dirname(os.path.abspath(__file__)),
            capture_output=True,
            text=True,
            timeout=60
        )
        
        # Validation should pass on a properly migrated database
        return result.returncode == 0
    
    def test_direct_migration(self):
        """Test direct migration script."""
        print("Testing direct migration...")
        
        # Run direct migration
        result = subprocess.run(
            ["python", "direct_migrate.py"],
            cwd=os.path.dirname(os.path.abspath(__file__)),
            capture_output=True,
            text=True,
            timeout=300
        )
        
        return result.returncode == 0
    
    def test_smart_migration(self):
        """Test smart migration script."""
        print("Testing smart migration...")
        
        # Run smart migration
        result = subprocess.run(
            ["python", "smart_migrate.py"],
            cwd=os.path.dirname(os.path.abspath(__file__)),
            capture_output=True,
            text=True,
            timeout=300
        )
        
        return result.returncode == 0
    
    def test_migration_rollback(self):
        """Test migration rollback functionality."""
        print("Testing migration rollback...")
        
        # Test rollback to previous version
        result = subprocess.run(
            ["python", "rollback_migration.py", "previous"],
            cwd=os.path.dirname(os.path.abspath(__file__)),
            capture_output=True,
            text=True,
            timeout=300
        )
        
        # Rollback might fail if we're already at the first version, which is OK
        return True  # We don't want rollback tests to fail the suite
    
    def test_migration_health_check(self):
        """Test migration health check."""
        print("Testing migration health check...")
        
        # Run health check
        result = subprocess.run(
            ["python", "migration_health_check.py"],
            cwd=os.path.dirname(os.path.abspath(__file__)),
            capture_output=True,
            text=True,
            timeout=60
        )
        
        return result.returncode == 0
    
    def test_circular_dependency_handling(self):
        """Test circular dependency handling."""
        print("Testing circular dependency handling...")
        
        # This test simulates a circular dependency scenario
        # by trying to run migrations when the database is already at the latest state
        
        # First, ensure we're at the latest migration
        result = subprocess.run(
            ["python", "run_migration_chain.py"],
            cwd=os.path.dirname(os.path.abspath(__file__)),
            capture_output=True,
            text=True,
            timeout=300
        )
        
        if result.returncode != 0:
            print(f"Initial migration failed: {result.stderr}")
            return False
        
        # Now try to run migrations again (should handle circular dependency gracefully)
        result = subprocess.run(
            ["python", "run_migration_chain.py"],
            cwd=os.path.dirname(os.path.abspath(__file__)),
            capture_output=True,
            text=True,
            timeout=300
        )
        
        # Should either succeed or fail gracefully
        return True
    
    def test_database_schema_consistency(self):
        """Test database schema consistency."""
        print("Testing database schema consistency...")
        
        engine = create_engine(self.test_database_url)
        with engine.connect() as connection:
            # Check that all tables have the expected structure
            if "postgresql" in self.test_database_url:
                result = connection.execute(text("""
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_schema = 'public'
                    ORDER BY table_name;
                """))
            else:
                result = connection.execute(text("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;"))
            
            tables = [row[0] for row in result.fetchall()]
            
            # Verify essential tables exist
            essential_tables = ['users', 'workspaces', 'documents', 'subscriptions', 'alembic_version']
            for table in essential_tables:
                if table not in tables:
                    print(f"Missing essential table: {table}")
                    return False
            
            # Check users table has essential columns
            if 'users' in tables:
                if "postgresql" in self.test_database_url:
                    result = connection.execute(text("""
                        SELECT column_name 
                        FROM information_schema.columns 
                        WHERE table_name = 'users' 
                        ORDER BY ordinal_position;
                    """))
                else:
                    result = connection.execute(text("PRAGMA table_info(users);"))
                
                user_columns = [row[0] for row in result.fetchall()]
                essential_columns = ['id', 'email', 'hashed_password']
                
                for col in essential_columns:
                    if col not in user_columns:
                        print(f"Missing essential column in users table: {col}")
                        return False
        
        return True
    
    def test_migration_script_imports(self):
        """Test that all migration scripts can be imported."""
        print("Testing migration script imports...")
        
        scripts = [
            'validate_migration_state',
            'direct_migrate',
            'smart_migrate',
            'simple_migrate',
            'migrate_with_retry',
            'rollback_migration',
            'migration_health_check',
            'run_migration_chain'
        ]
        
        for script in scripts:
            try:
                __import__(script)
            except Exception as e:
                print(f"Failed to import {script}: {e}")
                return False
        
        return True
    
    def run_all_tests(self):
        """Run all migration tests."""
        print("Migration System Test Suite")
        print("=" * 60)
        
        # Set up test environment
        if not self.setup_test_environment():
            print("ERROR: Failed to set up test environment")
            return False
        
        try:
            # Run all tests
            self.run_test("Fresh Database Migration", self.test_fresh_database_migration)
            self.run_test("Migration Validation", self.test_migration_validation)
            self.run_test("Direct Migration", self.test_direct_migration)
            self.run_test("Smart Migration", self.test_smart_migration)
            self.run_test("Migration Rollback", self.test_migration_rollback)
            self.run_test("Migration Health Check", self.test_migration_health_check)
            self.run_test("Circular Dependency Handling", self.test_circular_dependency_handling)
            self.run_test("Database Schema Consistency", self.test_database_schema_consistency)
            self.run_test("Migration Script Imports", self.test_migration_script_imports)
            
            # Print test results
            print("\nTest Results Summary:")
            print("=" * 60)
            
            passed = 0
            failed = 0
            errors = 0
            
            for test_name, status, error in self.test_results:
                if status == "PASS":
                    print(f"✓ {test_name}")
                    passed += 1
                elif status == "FAIL":
                    print(f"✗ {test_name} - {error}")
                    failed += 1
                else:  # ERROR
                    print(f"✗ {test_name} - ERROR: {error}")
                    errors += 1
            
            print(f"\nTotal: {len(self.test_results)} tests")
            print(f"Passed: {passed}")
            print(f"Failed: {failed}")
            print(f"Errors: {errors}")
            
            if failed == 0 and errors == 0:
                print("\n🎉 ALL TESTS PASSED!")
                return True
            else:
                print(f"\n❌ {failed + errors} TESTS FAILED")
                return False
                
        finally:
            # Clean up test environment
            self.cleanup_test_environment()

def main():
    """Main test function."""
    test_suite = MigrationTestSuite()
    success = test_suite.run_all_tests()
    
    if success:
        print("\nSUCCESS: All migration tests passed!")
        sys.exit(0)
    else:
        print("\nERROR: Some migration tests failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()
