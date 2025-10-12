#!/usr/bin/env python3
"""
Comprehensive migration health check script.
This script performs a thorough health check of the migration system.
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

class MigrationHealthChecker:
    """Comprehensive migration health checker."""
    
    def __init__(self):
        self.database_url = settings.DATABASE_URL
        self.issues = []
        self.warnings = []
        self.successes = []
    
    def check_database_connection(self):
        """Check if database connection is working."""
        print("Checking database connection...")
        
        try:
            engine = create_engine(self.database_url)
            with engine.connect() as connection:
                connection.execute(text("SELECT 1"))
                self.successes.append("Database connection successful")
                return True
        except Exception as e:
            self.issues.append(f"Database connection failed: {e}")
            return False
    
    def check_alembic_version_table(self):
        """Check if alembic_version table exists and is valid."""
        print("Checking Alembic version table...")
        
        try:
            engine = create_engine(self.database_url)
            with engine.connect() as connection:
                # Check if table exists
                if "postgresql" in self.database_url:
                    result = connection.execute(text("""
                        SELECT EXISTS (
                            SELECT FROM information_schema.tables 
                            WHERE table_schema = 'public' 
                            AND table_name = 'alembic_version'
                        );
                    """))
                    table_exists = result.scalar()
                else:  # SQLite
                    result = connection.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name='alembic_version';"))
                    table_exists = result.fetchone() is not None
                
                if not table_exists:
                    self.issues.append("Alembic version table does not exist")
                    return False
                
                # Check if version is set
                result = connection.execute(text("SELECT version_num FROM alembic_version;"))
                version = result.scalar()
                
                if not version:
                    self.issues.append("Alembic version is not set")
                    return False
                
                self.successes.append(f"Alembic version table exists with version: {version}")
                return True
                
        except Exception as e:
            self.issues.append(f"Error checking Alembic version table: {e}")
            return False
    
    def check_migration_files(self):
        """Check if migration files are present and valid."""
        print("Checking migration files...")
        
        try:
            from alembic.script import ScriptDirectory
            from alembic.config import Config
            
            alembic_cfg = Config(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'alembic.ini'))
            script = ScriptDirectory.from_config(alembic_cfg)
            
            migrations = []
            for rev in script.walk_revisions():
                migrations.append(rev.revision)
            
            if not migrations:
                self.issues.append("No migration files found")
                return False
            
            self.successes.append(f"Found {len(migrations)} migration files")
            return True
            
        except Exception as e:
            self.issues.append(f"Error checking migration files: {e}")
            return False
    
    def check_database_schema(self):
        """Check if database schema matches expected structure."""
        print("Checking database schema...")
        
        try:
            engine = create_engine(self.database_url)
            with engine.connect() as connection:
                # Get all tables
                if "postgresql" in self.database_url:
                    result = connection.execute(text("""
                        SELECT table_name 
                        FROM information_schema.tables 
                        WHERE table_schema = 'public'
                        ORDER BY table_name;
                    """))
                else:  # SQLite
                    result = connection.execute(text("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;"))
                
                tables = [row[0] for row in result.fetchall()]
                
                # Check for essential tables
                essential_tables = ['users', 'workspaces', 'documents', 'subscriptions']
                missing_tables = [table for table in essential_tables if table not in tables]
                
                if missing_tables:
                    self.issues.append(f"Missing essential tables: {missing_tables}")
                    return False
                
                # Check users table structure
                if 'users' in tables:
                    if "postgresql" in self.database_url:
                        result = connection.execute(text("""
                            SELECT column_name 
                            FROM information_schema.columns 
                            WHERE table_name = 'users' 
                            ORDER BY ordinal_position;
                        """))
                    else:  # SQLite
                        result = connection.execute(text("PRAGMA table_info(users);"))
                    
                    user_columns = [row[0] for row in result.fetchall()]
                    
                    # Check for essential columns
                    essential_columns = ['id', 'email', 'hashed_password']
                    missing_columns = [col for col in essential_columns if col not in user_columns]
                    
                    if missing_columns:
                        self.issues.append(f"Users table missing essential columns: {missing_columns}")
                        return False
                
                self.successes.append(f"Database schema looks good with {len(tables)} tables")
                return True
                
        except Exception as e:
            self.issues.append(f"Error checking database schema: {e}")
            return False
    
    def check_migration_consistency(self):
        """Check if migration state is consistent."""
        print("Checking migration consistency...")
        
        try:
            # Get current version from database
            engine = create_engine(self.database_url)
            with engine.connect() as connection:
                result = connection.execute(text("SELECT version_num FROM alembic_version;"))
                current_version = result.scalar()
            
            # Get available migrations
            from alembic.script import ScriptDirectory
            from alembic.config import Config
            
            alembic_cfg = Config(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'alembic.ini'))
            script = ScriptDirectory.from_config(alembic_cfg)
            
            available_migrations = []
            for rev in script.walk_revisions():
                available_migrations.append(rev.revision)
            
            # Check if current version is valid
            if current_version not in available_migrations:
                self.issues.append(f"Current version {current_version} not found in available migrations")
                return False
            
            # Check if we can determine the migration state from database structure
            from validate_migration_state import determine_migration_state
            
            # Get database tables and columns for analysis
            engine = create_engine(self.database_url)
            with engine.connect() as connection:
                if "postgresql" in self.database_url:
                    result = connection.execute(text("""
                        SELECT table_name 
                        FROM information_schema.tables 
                        WHERE table_schema = 'public'
                        ORDER BY table_name;
                    """))
                else:  # SQLite
                    result = connection.execute(text("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;"))
                
                tables = [row[0] for row in result.fetchall()]
                
                if 'users' in tables:
                    if "postgresql" in self.database_url:
                        result = connection.execute(text("""
                            SELECT column_name 
                            FROM information_schema.columns 
                            WHERE table_name = 'users' 
                            ORDER BY ordinal_position;
                        """))
                    else:  # SQLite
                        result = connection.execute(text("PRAGMA table_info(users);"))
                    
                    user_columns = [row[0] for row in result.fetchall()]
                    
                    # Determine actual state
                    actual_state = determine_migration_state(user_columns, tables)
                    
                    if current_version != actual_state:
                        self.warnings.append(f"Version mismatch: Alembic thinks {current_version}, database shows {actual_state}")
                    else:
                        self.successes.append("Migration state is consistent")
            
            return True
            
        except Exception as e:
            self.issues.append(f"Error checking migration consistency: {e}")
            return False
    
    def check_migration_scripts(self):
        """Check if migration scripts can be executed."""
        print("Checking migration scripts...")
        
        scripts_to_check = [
            'validate_migration_state.py',
            'direct_migrate.py',
            'smart_migrate.py',
            'simple_migrate.py',
            'migrate_with_retry.py',
            'rollback_migration.py'
        ]
        
        for script in scripts_to_check:
            script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), script)
            if not os.path.exists(script_path):
                self.issues.append(f"Migration script not found: {script}")
            else:
                # Check if script is executable
                try:
                    result = subprocess.run(
                        ["python", "-c", f"import {script[:-3]}"],
                        cwd=os.path.dirname(os.path.abspath(__file__)),
                        capture_output=True,
                        text=True,
                        timeout=10
                    )
                    if result.returncode == 0:
                        self.successes.append(f"Migration script {script} is valid")
                    else:
                        self.warnings.append(f"Migration script {script} has issues: {result.stderr}")
                except Exception as e:
                    self.warnings.append(f"Could not validate migration script {script}: {e}")
    
    def check_database_permissions(self):
        """Check if database has necessary permissions."""
        print("Checking database permissions...")
        
        try:
            engine = create_engine(self.database_url)
            with engine.connect() as connection:
                # Test basic operations
                connection.execute(text("SELECT 1"))
                
                # Test table creation (in a transaction that we'll rollback)
                trans = connection.begin()
                try:
                    connection.execute(text("CREATE TABLE test_permissions (id INTEGER);"))
                    connection.execute(text("DROP TABLE test_permissions;"))
                    trans.rollback()
                    self.successes.append("Database has necessary permissions")
                    return True
                except Exception as e:
                    trans.rollback()
                    self.issues.append(f"Database permission issues: {e}")
                    return False
                    
        except Exception as e:
            self.issues.append(f"Error checking database permissions: {e}")
            return False
    
    def run_health_check(self):
        """Run the complete health check."""
        print("Migration Health Check")
        print("=" * 50)
        
        # Run all checks
        self.check_database_connection()
        self.check_alembic_version_table()
        self.check_migration_files()
        self.check_database_schema()
        self.check_migration_consistency()
        self.check_migration_scripts()
        self.check_database_permissions()
        
        # Print results
        print("\nHealth Check Results:")
        print("=" * 50)
        
        if self.successes:
            print(f"\nSUCCESSES ({len(self.successes)}):")
            for success in self.successes:
                print(f"  ✓ {success}")
        
        if self.warnings:
            print(f"\nWARNINGS ({len(self.warnings)}):")
            for warning in self.warnings:
                print(f"  ⚠ {warning}")
        
        if self.issues:
            print(f"\nISSUES ({len(self.issues)}):")
            for issue in self.issues:
                print(f"  ✗ {issue}")
        
        # Overall status
        if not self.issues:
            if not self.warnings:
                print("\n🎉 MIGRATION SYSTEM IS HEALTHY!")
                return True
            else:
                print("\n⚠️  MIGRATION SYSTEM IS MOSTLY HEALTHY (with warnings)")
                return True
        else:
            print(f"\n❌ MIGRATION SYSTEM HAS {len(self.issues)} ISSUES")
            return False

def main():
    """Main health check function."""
    checker = MigrationHealthChecker()
    success = checker.run_health_check()
    
    if success:
        print("\nSUCCESS: Migration system health check passed!")
        sys.exit(0)
    else:
        print("\nERROR: Migration system health check failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()
