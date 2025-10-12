#!/usr/bin/env python3
"""
Check table structure to understand the circular dependency issue.
"""

import os
import sys
from sqlalchemy import create_engine, text

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.config import settings

def check_users_table():
    """Check the current structure of the users table."""
    database_url = settings.DATABASE_URL
    
    try:
        engine = create_engine(database_url)
        with engine.connect() as connection:
            if "postgresql" in database_url:
                result = connection.execute(text("""
                    SELECT column_name, data_type, is_nullable, column_default
                    FROM information_schema.columns 
                    WHERE table_name = 'users' 
                    ORDER BY ordinal_position;
                """))
            else:  # SQLite
                result = connection.execute(text("PRAGMA table_info(users);"))
            
            print("Users table structure:")
            print("=" * 50)
            for row in result.fetchall():
                if "postgresql" in database_url:
                    print(f"  {row[0]} - {row[1]} - nullable: {row[2]} - default: {row[3]}")
                else:
                    print(f"  {row[1]} - {row[2]} - nullable: {row[3]} - default: {row[4]}")
            
            # Check if mobile_phone and phone_verified already exist
            if "postgresql" in database_url:
                result = connection.execute(text("""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name = 'users' 
                    AND column_name IN ('mobile_phone', 'phone_verified');
                """))
            else:
                result = connection.execute(text("""
                    SELECT name FROM pragma_table_info('users') 
                    WHERE name IN ('mobile_phone', 'phone_verified');
                """))
            
            existing_columns = [row[0] for row in result.fetchall()]
            print(f"\nColumns that migration 004 is trying to add:")
            print(f"  mobile_phone: {'EXISTS' if 'mobile_phone' in existing_columns else 'MISSING'}")
            print(f"  phone_verified: {'EXISTS' if 'phone_verified' in existing_columns else 'MISSING'}")
            
    except Exception as e:
        print(f"Error checking table structure: {e}")

if __name__ == "__main__":
    check_users_table()
