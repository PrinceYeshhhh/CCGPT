#!/usr/bin/env python3
"""
Check performance tables structure to understand column issues.
"""

import os
import sys
from sqlalchemy import create_engine, text

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.config import settings

def check_performance_tables():
    """Check the structure of performance tables."""
    database_url = settings.DATABASE_URL
    
    try:
        engine = create_engine(database_url)
        with engine.connect() as connection:
            # Check performance_configs table
            result = connection.execute(text("PRAGMA table_info(performance_configs);"))
            configs_columns = [row[1] for row in result.fetchall()]
            print(f"Performance configs columns: {configs_columns}")
            
            # Check performance_benchmarks table
            result = connection.execute(text("PRAGMA table_info(performance_benchmarks);"))
            benchmarks_columns = [row[1] for row in result.fetchall()]
            print(f"Performance benchmarks columns: {benchmarks_columns}")
            
            # Check if the problematic columns exist
            print(f"config_key exists: {'config_key' in configs_columns}")
            print(f"benchmark_name exists: {'benchmark_name' in benchmarks_columns}")
            
    except Exception as e:
        print(f"Error checking performance tables: {e}")

if __name__ == "__main__":
    check_performance_tables()
