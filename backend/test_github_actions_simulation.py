#!/usr/bin/env python3
"""
Simulate GitHub Actions environment to test migration issues.
"""

import os
import sys
from sqlalchemy import create_engine, text

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_postgresql_connection_parameters():
    """Test PostgreSQL connection parameters that would be used in GitHub Actions."""
    
    # Simulate GitHub Actions environment
    database_url = "postgresql://postgres:postgres@localhost:5432/test_db"
    
    print("Testing PostgreSQL connection parameters...")
    print(f"Database URL: {database_url}")
    
    # Test different engine configurations
    configs = [
        {
            "name": "Current Alembic config",
            "config": {
                "poolclass": "NullPool",
                "pool_pre_ping": True,
                "pool_recycle": 1,
                "isolation_level": "AUTOCOMMIT"
            }
        },
        {
            "name": "With connect_args (old problematic)",
            "config": {
                "poolclass": "NullPool",
                "pool_pre_ping": True,
                "pool_recycle": 1,
                "isolation_level": "AUTOCOMMIT",
                "connect_args": {
                    "options": "-c default_transaction_isolation='read committed'"
                }
            }
        },
        {
            "name": "With connect_args (underscore)",
            "config": {
                "poolclass": "NullPool",
                "pool_pre_ping": True,
                "pool_recycle": 1,
                "isolation_level": "AUTOCOMMIT",
                "connect_args": {
                    "options": "-c default_transaction_isolation=read_committed"
                }
            }
        },
        {
            "name": "Minimal config",
            "config": {
                "pool_pre_ping": True
            }
        }
    ]
    
    for config in configs:
        print(f"\n--- Testing {config['name']} ---")
        try:
            # Import the pool class
            from sqlalchemy.pool import NullPool
            if "poolclass" in config["config"] and config["config"]["poolclass"] == "NullPool":
                config["config"]["poolclass"] = NullPool
            
            engine = create_engine(database_url, **config["config"])
            
            # Try to create the engine (this will fail with connection refused, but we can see the error)
            print(f"  Engine created successfully")
            
            # Try to connect (this will fail, but we can see the exact error)
            try:
                with engine.connect() as connection:
                    result = connection.execute(text("SELECT 1"))
                    print(f"  Connection successful!")
            except Exception as e:
                print(f"  Connection failed: {e}")
                # Check if it's the specific PostgreSQL parameter error
                if "default_transaction_isolation" in str(e):
                    print(f"  *** POSTGRESQL PARAMETER ERROR DETECTED ***")
                    print(f"  Error details: {e}")
                elif "Connection refused" in str(e):
                    print(f"  Connection refused (expected - no PostgreSQL server)")
                else:
                    print(f"  Other error: {e}")
                    
        except Exception as e:
            print(f"  Engine creation failed: {e}")
            if "default_transaction_isolation" in str(e):
                print(f"  *** POSTGRESQL PARAMETER ERROR DETECTED ***")

def test_alembic_environment():
    """Test the actual Alembic environment configuration."""
    print("\n" + "="*60)
    print("Testing Alembic environment configuration...")
    
    try:
        # Import the Alembic environment
        from alembic import config
        from alembic.script import ScriptDirectory
        
        # Get the Alembic config
        alembic_cfg = config.Config(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'alembic.ini'))
        
        # Test the URL function
        from alembic.env import get_url
        url = get_url()
        print(f"Alembic URL: {url}")
        
        # Test engine creation from Alembic config
        from alembic.env import run_migrations_online
        print("Alembic environment loaded successfully")
        
    except Exception as e:
        print(f"Error loading Alembic environment: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_postgresql_connection_parameters()
    test_alembic_environment()
