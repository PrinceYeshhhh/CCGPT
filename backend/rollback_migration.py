#!/usr/bin/env python3
"""
Migration rollback script.
This script safely rollbacks migrations if they fail or cause issues.
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

def get_current_migration_version():
    """Get the current migration version from the database."""
    database_url = settings.DATABASE_URL
    
    try:
        engine = create_engine(database_url)
        with engine.connect() as connection:
            result = connection.execute(text("SELECT version_num FROM alembic_version;"))
            return result.scalar()
    except Exception as e:
        print(f"ERROR: Could not get current migration version: {e}")
        return None

def get_available_migrations():
    """Get all available migration versions."""
    try:
        from alembic.script import ScriptDirectory
        from alembic.config import Config
        
        alembic_cfg = Config(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'alembic.ini'))
        script = ScriptDirectory.from_config(alembic_cfg)
        
        migrations = []
        for rev in script.walk_revisions():
            migrations.append(rev.revision)
        
        return sorted(migrations)
    except Exception as e:
        print(f"ERROR: Could not get available migrations: {e}")
        return []

def rollback_to_version(target_version):
    """Rollback to a specific migration version."""
    print(f"Rolling back to version: {target_version}")
    
    try:
        result = subprocess.run(
            ["python", "-m", "alembic", "downgrade", target_version],
            cwd=os.path.dirname(os.path.abspath(__file__)),
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout
        )
        
        if result.returncode == 0:
            print(f"SUCCESS: Rolled back to version {target_version}")
            print("Rollback output:")
            print(result.stdout)
            return True
        else:
            print(f"ERROR: Rollback failed with return code {result.returncode}")
            print("Error output:")
            print(result.stderr)
            return False
            
    except subprocess.TimeoutExpired:
        print("ERROR: Rollback timed out")
        return False
    except Exception as e:
        print(f"ERROR: Unexpected error during rollback: {e}")
        return False

def rollback_to_previous_version():
    """Rollback to the previous migration version."""
    current_version = get_current_migration_version()
    if not current_version:
        print("ERROR: Could not determine current migration version")
        return False
    
    available_migrations = get_available_migrations()
    if not available_migrations:
        print("ERROR: Could not get available migrations")
        return False
    
    # Find current version index
    try:
        current_index = available_migrations.index(current_version)
    except ValueError:
        print(f"ERROR: Current version {current_version} not found in available migrations")
        return False
    
    # Get previous version
    if current_index > 0:
        previous_version = available_migrations[current_index - 1]
        return rollback_to_version(previous_version)
    else:
        print("WARNING: Already at the first migration version, cannot rollback further")
        return True

def rollback_to_initial():
    """Rollback to the initial migration (001)."""
    return rollback_to_version("001")

def rollback_to_base():
    """Rollback to base (no migrations applied)."""
    print("Rolling back to base (no migrations applied)")
    
    try:
        result = subprocess.run(
            ["python", "-m", "alembic", "downgrade", "base"],
            cwd=os.path.dirname(os.path.abspath(__file__)),
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout
        )
        
        if result.returncode == 0:
            print("SUCCESS: Rolled back to base")
            print("Rollback output:")
            print(result.stdout)
            return True
        else:
            print(f"ERROR: Rollback to base failed with return code {result.returncode}")
            print("Error output:")
            print(result.stderr)
            return False
            
    except subprocess.TimeoutExpired:
        print("ERROR: Rollback to base timed out")
        return False
    except Exception as e:
        print(f"ERROR: Unexpected error during rollback to base: {e}")
        return False

def emergency_rollback():
    """Emergency rollback that resets the database to a clean state."""
    print("EMERGENCY ROLLBACK: Resetting database to clean state")
    
    database_url = settings.DATABASE_URL
    
    try:
        engine = create_engine(database_url)
        with engine.connect() as connection:
            # Get all tables
            if "postgresql" in database_url:
                result = connection.execute(text("""
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name != 'alembic_version'
                    ORDER BY table_name;
                """))
            else:  # SQLite
                result = connection.execute(text("""
                    SELECT name 
                    FROM sqlite_master 
                    WHERE type='table' 
                    AND name != 'alembic_version'
                    ORDER BY name;
                """))
            
            tables = [row[0] for row in result.fetchall()]
            
            # Drop all tables
            for table in tables:
                try:
                    connection.execute(text(f"DROP TABLE IF EXISTS {table} CASCADE;"))
                    print(f"Dropped table: {table}")
                except Exception as e:
                    print(f"WARNING: Could not drop table {table}: {e}")
            
            # Reset alembic version
            connection.execute(text("DELETE FROM alembic_version;"))
            connection.execute(text("INSERT INTO alembic_version (version_num) VALUES ('001');"))
            
            print("SUCCESS: Emergency rollback completed")
            return True
            
    except Exception as e:
        print(f"ERROR: Emergency rollback failed: {e}")
        return False

def interactive_rollback():
    """Interactive rollback menu."""
    print("Migration Rollback Tool")
    print("=" * 40)
    
    current_version = get_current_migration_version()
    print(f"Current migration version: {current_version}")
    
    available_migrations = get_available_migrations()
    print(f"Available migrations: {', '.join(available_migrations)}")
    
    print("\nRollback options:")
    print("1. Rollback to previous version")
    print("2. Rollback to specific version")
    print("3. Rollback to initial version (001)")
    print("4. Rollback to base (no migrations)")
    print("5. Emergency rollback (reset all tables)")
    print("6. Exit")
    
    while True:
        try:
            choice = input("\nEnter your choice (1-6): ").strip()
            
            if choice == "1":
                return rollback_to_previous_version()
            elif choice == "2":
                target = input("Enter target version: ").strip()
                if target in available_migrations:
                    return rollback_to_version(target)
                else:
                    print(f"ERROR: Version {target} not found in available migrations")
            elif choice == "3":
                return rollback_to_initial()
            elif choice == "4":
                return rollback_to_base()
            elif choice == "5":
                confirm = input("WARNING: This will delete all data! Are you sure? (yes/no): ").strip().lower()
                if confirm == "yes":
                    return emergency_rollback()
                else:
                    print("Emergency rollback cancelled")
            elif choice == "6":
                print("Exiting...")
                return True
            else:
                print("Invalid choice. Please enter 1-6.")
        except KeyboardInterrupt:
            print("\nExiting...")
            return True
        except Exception as e:
            print(f"ERROR: {e}")

def main():
    """Main rollback function."""
    if len(sys.argv) > 1:
        # Command line arguments
        command = sys.argv[1].lower()
        
        if command == "previous":
            success = rollback_to_previous_version()
        elif command == "initial":
            success = rollback_to_initial()
        elif command == "base":
            success = rollback_to_base()
        elif command == "emergency":
            success = emergency_rollback()
        elif command.startswith("to:"):
            target_version = command[3:]
            success = rollback_to_version(target_version)
        else:
            print(f"ERROR: Unknown command: {command}")
            print("Available commands: previous, initial, base, emergency, to:<version>")
            sys.exit(1)
        
        if success:
            print("\nSUCCESS: Rollback completed successfully!")
            sys.exit(0)
        else:
            print("\nERROR: Rollback failed")
            sys.exit(1)
    else:
        # Interactive mode
        success = interactive_rollback()
        if success:
            sys.exit(0)
        else:
            sys.exit(1)

if __name__ == "__main__":
    main()
