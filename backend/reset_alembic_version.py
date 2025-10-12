#!/usr/bin/env python3
"""
Reset Alembic version table to handle failed transaction states.
This script can be used in CI/CD environments to recover from failed migrations.
"""

import os
import sys
import time
from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError, InternalError

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.config import settings

def reset_alembic_version():
    """Reset the Alembic version table to handle failed transaction states."""
    database_url = settings.DATABASE_URL
    
    print(f"Connecting to database: {database_url}")
    
    # Create engine with retry logic
    max_retries = 5
    for attempt in range(max_retries):
        try:
            engine = create_engine(database_url, pool_pre_ping=True)
            
            with engine.connect() as connection:
                # Start a new transaction
                trans = connection.begin()
                
                try:
                    # Check if alembic_version table exists
                    result = connection.execute(text("""
                        SELECT EXISTS (
                            SELECT FROM information_schema.tables 
                            WHERE table_schema = 'public' 
                            AND table_name = 'alembic_version'
                        );
                    """))
                    
                    table_exists = result.scalar()
                    
                    if table_exists:
                        print("Alembic version table exists. Checking current version...")
                        
                        # Get current version
                        result = connection.execute(text("SELECT version_num FROM alembic_version;"))
                        current_version = result.scalar()
                        print(f"Current version: {current_version}")
                        
                        # Reset to version 001 to allow clean migration
                        connection.execute(text("UPDATE alembic_version SET version_num = '001';"))
                        print("Reset version to 001")
                    else:
                        print("Alembic version table does not exist. Creating it...")
                        connection.execute(text("""
                            CREATE TABLE alembic_version (
                                version_num VARCHAR(32) NOT NULL,
                                CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num)
                            );
                        """))
                        connection.execute(text("INSERT INTO alembic_version (version_num) VALUES ('001');"))
                        print("Created alembic_version table with version 001")
                    
                    # Commit the transaction
                    trans.commit()
                    print("Successfully reset Alembic version table")
                    return True
                    
                except Exception as e:
                    # Rollback on error
                    trans.rollback()
                    print(f"Error during reset: {e}")
                    raise e
                    
        except (OperationalError, InternalError) as e:
            print(f"Attempt {attempt + 1} failed: {e}")
            if attempt < max_retries - 1:
                print(f"Retrying in {2 ** attempt} seconds...")
                time.sleep(2 ** attempt)
            else:
                print("All retry attempts failed")
                return False
        except Exception as e:
            print(f"Unexpected error: {e}")
            return False
    
    return False

if __name__ == "__main__":
    success = reset_alembic_version()
    if success:
        print("✅ Alembic version reset completed successfully")
        sys.exit(0)
    else:
        print("❌ Alembic version reset failed")
        sys.exit(1)
