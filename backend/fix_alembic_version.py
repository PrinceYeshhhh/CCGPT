#!/usr/bin/env python3
"""
Fix Alembic version table to match actual database state.
"""

import os
import sys
from sqlalchemy import create_engine, text

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.config import settings

def fix_alembic_version():
    """Fix the Alembic version table to match the actual database state."""
    database_url = settings.DATABASE_URL
    
    try:
        engine = create_engine(database_url)
        with engine.connect() as connection:
            trans = connection.begin()
            
            try:
                # Update the version to match the actual database state
                connection.execute(text("UPDATE alembic_version SET version_num = '008_add_performance_indexes';"))
                trans.commit()
                print("✅ Alembic version updated to match database state")
                
                # Verify the update
                result = connection.execute(text("SELECT version_num FROM alembic_version;"))
                current_version = result.scalar()
                print(f"✅ Current Alembic version: {current_version}")
                
                return True
                
            except Exception as e:
                trans.rollback()
                print(f"❌ Failed to update Alembic version: {e}")
                return False
                
    except Exception as e:
        print(f"❌ Error fixing Alembic version: {e}")
        return False

if __name__ == "__main__":
    success = fix_alembic_version()
    
    if success:
        print("\n✅ Alembic version fixed successfully!")
        sys.exit(0)
    else:
        print("\n❌ Failed to fix Alembic version")
        sys.exit(1)
