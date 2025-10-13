#!/usr/bin/env python3
"""
Test PostgreSQL connection with different parameter formats.
"""

import os
import sys
from sqlalchemy import create_engine, text

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_postgresql_connection_formats():
    """Test different PostgreSQL connection parameter formats."""
    
    # Test different formats
    formats = [
        {"options": "-c default_transaction_isolation=read_committed"},
        {"options": "-c default_transaction_isolation='read committed'"},
        {"options": "-c default_transaction_isolation=\"read committed\""},
        {"options": "-c default_transaction_isolation=read\\ committed"},
        {}  # No options
    ]
    
    database_url = "postgresql://postgres:postgres@localhost:5432/test_db"
    
    for i, connect_args in enumerate(formats):
        print(f"\nTesting format {i+1}: {connect_args}")
        
        try:
            engine = create_engine(
                database_url,
                pool_pre_ping=True,
                pool_recycle=1,
                isolation_level='AUTOCOMMIT',
                connect_args=connect_args
            )
            
            with engine.connect() as connection:
                result = connection.execute(text("SELECT 1"))
                print(f"  SUCCESS: Connection established")
                
                # Test transaction isolation level
                try:
                    result = connection.execute(text("SHOW default_transaction_isolation;"))
                    isolation = result.scalar()
                    print(f"  Transaction isolation: {isolation}")
                except Exception as e:
                    print(f"  Could not check isolation level: {e}")
                    
        except Exception as e:
            print(f"  FAILED: {e}")

if __name__ == "__main__":
    test_postgresql_connection_formats()
