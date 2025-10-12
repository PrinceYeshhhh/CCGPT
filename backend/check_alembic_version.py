#!/usr/bin/env python3
"""
Check Alembic version and migration status.
"""

import os
import sys
from sqlalchemy import create_engine, text

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.config import settings

def check_alembic_version():
    """Check the current Alembic version."""
    database_url = settings.DATABASE_URL
    
    try:
        engine = create_engine(database_url)
        with engine.connect() as connection:
            # Check current version
            result = connection.execute(text("SELECT version_num FROM alembic_version;"))
            current_version = result.scalar()
            print(f"Current Alembic version: {current_version}")
            
            # Check all migration files
            import os
            migration_dir = os.path.join(os.path.dirname(__file__), 'alembic', 'versions')
            migration_files = [f for f in os.listdir(migration_dir) if f.endswith('.py') and f != '__pycache__']
            migration_files.sort()
            
            print(f"\nAvailable migration files:")
            for i, file in enumerate(migration_files, 1):
                print(f"  {i}. {file}")
            
            # Check which migrations have been applied
            print(f"\nMigration status:")
            print(f"  Current version: {current_version}")
            
            # Find the index of current version
            version_numbers = [f.split('_')[0] for f in migration_files]
            try:
                current_index = version_numbers.index(current_version)
                print(f"  Applied migrations: {current_index + 1}/{len(migration_files)}")
                print(f"  Pending migrations: {len(migration_files) - current_index - 1}")
            except ValueError:
                print(f"  WARNING: Current version {current_version} not found in migration files!")
            
    except Exception as e:
        print(f"Error checking Alembic version: {e}")

if __name__ == "__main__":
    check_alembic_version()
