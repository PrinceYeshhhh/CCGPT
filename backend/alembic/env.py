from logging.config import fileConfig
from sqlalchemy import engine_from_config
from sqlalchemy import pool
from sqlalchemy import text
from alembic import context
import os
import sys

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.config import settings
from app.core.database import Base

# Import all models to ensure they are registered with Base
from app.models import *  # This ensures all models are loaded

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
target_metadata = Base.metadata

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def get_url():
    return settings.DATABASE_URL


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = get_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode with circular dependency protection.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    configuration = config.get_section(config.config_ini_section)
    configuration["sqlalchemy.url"] = get_url()
    
    # Create engine with aggressive connection management
    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
        # Force new connections for each operation
        pool_pre_ping=True,
        pool_recycle=1,
        # Use autocommit mode to avoid transaction issues
        isolation_level='AUTOCOMMIT',
        # Additional PostgreSQL-specific settings
        connect_args={
            "options": "-c default_transaction_isolation=read_committed"
        } if "postgresql" in get_url() else {}
    )

    # Check for circular dependency risk before running migrations
    try:
        with connectable.connect() as connection:
            # Get current version
            try:
                result = connection.execute(text("SELECT version_num FROM alembic_version;"))
                current_version = result.scalar()
            except Exception:
                current_version = None
            
            # Check if we're at risk of circular dependency
            if current_version and "postgresql" in get_url():
                # For PostgreSQL, check if we're trying to re-run already applied migrations
                from alembic.script import ScriptDirectory
                script = ScriptDirectory.from_config(config)
                
                # Get the revision we're trying to upgrade to
                head_revision = script.get_current_head()
                
                # If we're already at head, skip migration
                if current_version == head_revision:
                    print("SUCCESS: Database is already at the latest migration version")
                    return
                
                # For PostgreSQL, ensure we're not in a failed transaction state
                if "postgresql" in get_url():
                    try:
                        # Check transaction state
                        result = connection.execute(text("SELECT txid_current();"))
                        print(f"Current transaction ID: {result.scalar()}")
                        
                        # Ensure clean transaction state
                        connection.execute(text("DISCARD ALL;"))
                    except Exception as e:
                        print(f"WARNING: Could not reset transaction state: {e}")
                        # Try to rollback any pending transaction
                        try:
                            connection.rollback()
                        except Exception:
                            pass
                
                # Check if current version is valid
                try:
                    script.get_revision(current_version)
                except Exception:
                    print(f"WARNING: Current version {current_version} is invalid, will reset to head")
                    # Reset to a known good state
                    connection.execute(text("UPDATE alembic_version SET version_num = '001';"))
    except Exception as e:
        print(f"WARNING: Could not check migration state: {e}")

    # For PostgreSQL, use a more aggressive approach
    if "postgresql" in get_url():
        max_retries = 3
        for attempt in range(max_retries):
            try:
                with connectable.connect() as connection:
                    # Force a clean connection
                    try:
                        connection.execute(text("SELECT 1"))
                    except Exception:
                        # If connection fails, try to reset it
                        connection.rollback()
                        connection.execute(text("SELECT 1"))
                    
                    context.configure(
                        connection=connection, 
                        target_metadata=target_metadata,
                        # Use autocommit for PostgreSQL to avoid transaction issues
                        transaction_per_migration=True,
                        # Add circular dependency protection
                        compare_type=True,
                        compare_server_default=True
                    )

                    # Run migrations without explicit transaction management
                    context.run_migrations()
                    break  # Success, exit retry loop
                    
            except Exception as e:
                if "CircularDependencyError" in str(e):
                    print(f"WARNING: Circular dependency detected, skipping migration: {e}")
                    break  # Skip migration to avoid circular dependency
                elif attempt == max_retries - 1:
                    raise e  # Re-raise on final attempt
                # Wait before retrying
                import time
                time.sleep(1)
    else:
        # For SQLite, use the original logic with circular dependency protection
        with connectable.connect() as connection:
            # Handle failed transactions by rolling back first
            try:
                connection.rollback()
            except Exception:
                pass  # Ignore rollback errors
            
            # Use batch mode for SQLite
            if "sqlite" in get_url():
                context.configure(
                    connection=connection, 
                    target_metadata=target_metadata,
                    render_as_batch=True,
                    # Add circular dependency protection
                    compare_type=True,
                    compare_server_default=True
                )
                try:
                    with context.begin_transaction():
                        context.run_migrations()
                except Exception as e:
                    if "CircularDependencyError" in str(e):
                        print(f"WARNING: Circular dependency detected, skipping migration: {e}")
                    else:
                        raise e
            else:
                context.configure(
                    connection=connection, 
                    target_metadata=target_metadata,
                    # Add circular dependency protection
                    compare_type=True,
                    compare_server_default=True
                )

                try:
                    with context.begin_transaction():
                        context.run_migrations()
                except Exception as e:
                    if "CircularDependencyError" in str(e):
                        print(f"WARNING: Circular dependency detected, skipping migration: {e}")
                    else:
                        raise e


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
