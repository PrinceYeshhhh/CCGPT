#!/usr/bin/env python3
"""
Comprehensive migration issue diagnostic script.
This script helps identify why migrations might fail in different environments.
"""

import os
import sys
import platform
import subprocess
import time
from sqlalchemy import create_engine, text

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.config import settings

def get_environment_info():
    """Get comprehensive environment information."""
    print("Environment Information")
    print("=" * 50)
    
    print(f"Python version: {sys.version}")
    print(f"Platform: {platform.platform()}")
    print(f"Architecture: {platform.architecture()}")
    print(f"Machine: {platform.machine()}")
    print(f"Processor: {platform.processor()}")
    print(f"Node: {platform.node()}")
    print(f"System: {platform.system()}")
    print(f"Release: {platform.release()}")
    print(f"Version: {platform.version()}")
    
    print(f"\nEnvironment Variables:")
    print(f"  DATABASE_URL: {os.getenv('DATABASE_URL', 'Not set')}")
    print(f"  ENVIRONMENT: {os.getenv('ENVIRONMENT', 'Not set')}")
    print(f"  PYTHONPATH: {os.getenv('PYTHONPATH', 'Not set')}")
    print(f"  PWD: {os.getenv('PWD', 'Not set')}")
    
    print(f"\nCurrent Working Directory: {os.getcwd()}")
    print(f"Script Location: {os.path.dirname(os.path.abspath(__file__))}")

def check_python_packages():
    """Check Python package versions."""
    print("\nPython Package Versions")
    print("=" * 50)
    
    packages = [
        'sqlalchemy',
        'alembic',
        'psycopg2',
        'psycopg2-binary',
        'pytest',
        'fastapi',
        'pydantic'
    ]
    
    for package in packages:
        try:
            result = subprocess.run(
                [sys.executable, "-c", f"import {package.replace('-', '_')}; print({package.replace('-', '_')}.__version__)"],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                version = result.stdout.strip()
                print(f"  {package}: {version}")
            else:
                print(f"  {package}: Not installed or error")
        except Exception as e:
            print(f"  {package}: Error checking version - {e}")

def check_database_connection():
    """Check database connection details."""
    print("\nDatabase Connection Details")
    print("=" * 50)
    
    database_url = settings.DATABASE_URL
    print(f"Database URL: {database_url}")
    
    if "postgresql" in database_url:
        print("Database Type: PostgreSQL")
        try:
            # Parse connection details
            if "://" in database_url:
                parts = database_url.split("://")[1]
                if "@" in parts:
                    auth, host_db = parts.split("@")
                    if ":" in auth:
                        user, password = auth.split(":")
                        print(f"  User: {user}")
                        print(f"  Password: {'*' * len(password)}")
                    else:
                        print(f"  User: {auth}")
                    
                    if ":" in host_db:
                        host, db_part = host_db.split(":")
                        if "/" in db_part:
                            port, database = db_part.split("/")
                            print(f"  Host: {host}")
                            print(f"  Port: {port}")
                            print(f"  Database: {database}")
                        else:
                            print(f"  Host: {host}")
                            print(f"  Database: {db_part}")
                    else:
                        print(f"  Host: {host_db}")
        except Exception as e:
            print(f"  Error parsing connection string: {e}")
    else:
        print("Database Type: SQLite")
        print(f"  File: {database_url.replace('sqlite:///', '')}")
    
    # Test connection
    try:
        engine = create_engine(database_url)
        with engine.connect() as connection:
            result = connection.execute(text("SELECT 1"))
            print("  Connection: SUCCESS")
            
            # Get database version
            if "postgresql" in database_url:
                result = connection.execute(text("SELECT version();"))
                version = result.scalar()
                print(f"  PostgreSQL Version: {version}")
            else:
                result = connection.execute(text("SELECT sqlite_version();"))
                version = result.scalar()
                print(f"  SQLite Version: {version}")
                
    except Exception as e:
        print(f"  Connection: FAILED - {e}")

def check_migration_files():
    """Check migration files and their status."""
    print("\nMigration Files Status")
    print("=" * 50)
    
    migration_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'alembic', 'versions')
    
    if not os.path.exists(migration_dir):
        print("  ERROR: Migration directory not found")
        return
    
    migration_files = [f for f in os.listdir(migration_dir) if f.endswith('.py')]
    print(f"  Found {len(migration_files)} migration files:")
    
    for file in sorted(migration_files):
        file_path = os.path.join(migration_dir, file)
        try:
            with open(file_path, 'r') as f:
                content = f.read()
                if 'def upgrade()' in content and 'def downgrade()' in content:
                    print(f"    ✓ {file}")
                else:
                    print(f"    ⚠ {file} (missing upgrade/downgrade functions)")
        except Exception as e:
            print(f"    ✗ {file} (error reading: {e})")

def check_alembic_status():
    """Check Alembic status."""
    print("\nAlembic Status")
    print("=" * 50)
    
    try:
        # Check current version
        result = subprocess.run(
            ["python", "-m", "alembic", "current"],
            cwd=os.path.dirname(os.path.abspath(__file__)),
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode == 0:
            print(f"  Current version: {result.stdout.strip()}")
        else:
            print(f"  Error getting current version: {result.stderr}")
        
        # Check history
        result = subprocess.run(
            ["python", "-m", "alembic", "history"],
            cwd=os.path.dirname(os.path.abspath(__file__)),
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode == 0:
            lines = result.stdout.strip().split('\n')
            print(f"  Migration history ({len(lines)} entries):")
            for line in lines[:5]:  # Show first 5 entries
                print(f"    {line}")
            if len(lines) > 5:
                print(f"    ... and {len(lines) - 5} more")
        else:
            print(f"  Error getting history: {result.stderr}")
            
    except Exception as e:
        print(f"  Error running Alembic commands: {e}")

def test_migration_scripts():
    """Test all migration scripts."""
    print("\nMigration Scripts Test")
    print("=" * 50)
    
    scripts = [
        'direct_migrate',
        'smart_migrate',
        'simple_migrate',
        'migrate_with_retry',
        'ultra_migrate',
        'nuclear_migrate'
    ]
    
    for script in scripts:
        script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), f"{script}.py")
        if os.path.exists(script_path):
            print(f"  Testing {script}.py...")
            try:
                # Just test import, don't run the actual migration
                result = subprocess.run(
                    [sys.executable, "-c", f"import {script}"],
                    cwd=os.path.dirname(os.path.abspath(__file__)),
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                if result.returncode == 0:
                    print(f"    ✓ {script}.py imports successfully")
                else:
                    print(f"    ✗ {script}.py import failed: {result.stderr}")
            except Exception as e:
                print(f"    ✗ {script}.py test failed: {e}")
        else:
            print(f"  ✗ {script}.py not found")

def check_file_permissions():
    """Check file permissions and accessibility."""
    print("\nFile Permissions Check")
    print("=" * 50)
    
    important_files = [
        'alembic.ini',
        'alembic/env.py',
        'run_migration_chain.py',
        'direct_migrate.py',
        'smart_migrate.py'
    ]
    
    for file_path in important_files:
        full_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), file_path)
        if os.path.exists(full_path):
            try:
                # Check if file is readable
                with open(full_path, 'r') as f:
                    f.read(1)  # Try to read first character
                print(f"  ✓ {file_path} is readable")
                
                # Check if file is executable (for .py files)
                if file_path.endswith('.py'):
                    if os.access(full_path, os.X_OK):
                        print(f"    ✓ {file_path} is executable")
                    else:
                        print(f"    ⚠ {file_path} is not executable")
                        
            except Exception as e:
                print(f"  ✗ {file_path} is not readable: {e}")
        else:
            print(f"  ✗ {file_path} not found")

def main():
    """Run comprehensive diagnostics."""
    print("Migration Issue Diagnostics")
    print("=" * 60)
    print("This script helps identify why migrations might fail in different environments.")
    print("=" * 60)
    
    get_environment_info()
    check_python_packages()
    check_database_connection()
    check_migration_files()
    check_alembic_status()
    test_migration_scripts()
    check_file_permissions()
    
    print("\n" + "=" * 60)
    print("Diagnostics Complete!")
    print("=" * 60)
    print("\nIf you're still experiencing issues, please share this output")
    print("along with the specific error messages you're seeing.")

if __name__ == "__main__":
    main()
