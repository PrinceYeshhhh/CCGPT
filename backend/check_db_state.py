#!/usr/bin/env python3
"""
Check current database state to understand the issues.
"""

import os
import sys
from sqlalchemy import create_engine, text

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.config import settings

def check_database_state():
    """Check the current state of the database."""
    database_url = settings.DATABASE_URL
    print(f"Database URL: {database_url}")
    
    try:
        engine = create_engine(database_url)
        with engine.connect() as connection:
            # Check alembic version
            try:
                result = connection.execute(text("SELECT version_num FROM alembic_version;"))
                version = result.scalar()
                print(f"Alembic version: {version}")
            except Exception as e:
                print(f"Alembic version error: {e}")
            
            # Check if users table exists
            if "postgresql" in database_url:
                result = connection.execute(text("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_schema = 'public' 
                        AND table_name = 'users'
                    );
                """))
                users_exists = result.scalar()
            else:
                result = connection.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name='users';"))
                users_exists = result.fetchone() is not None
            
            print(f"Users table exists: {users_exists}")
            
            if users_exists:
                # Check users table columns
                if "postgresql" in database_url:
                    result = connection.execute(text("""
                        SELECT column_name, data_type 
                        FROM information_schema.columns 
                        WHERE table_name = 'users' 
                        ORDER BY ordinal_position;
                    """))
                else:
                    result = connection.execute(text("PRAGMA table_info(users);"))
                
                columns = result.fetchall()
                print(f"Users table columns ({len(columns)}):")
                for col in columns:
                    if "postgresql" in database_url:
                        print(f"  {col[0]} - {col[1]}")
                    else:
                        print(f"  {col[1]} - {col[2]}")
            
            # Check all tables
            if "postgresql" in database_url:
                result = connection.execute(text("""
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_schema = 'public'
                    ORDER BY table_name;
                """))
            else:
                result = connection.execute(text("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;"))
            
            tables = [row[0] for row in result.fetchall()]
            print(f"All tables ({len(tables)}): {tables}")
            
    except Exception as e:
        print(f"Database connection error: {e}")

if __name__ == "__main__":
    check_database_state()
