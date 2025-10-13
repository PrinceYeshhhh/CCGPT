#!/usr/bin/env python3
"""
Check the migration chain for any issues.
"""

import os
import sys
from alembic.config import Config
from alembic.script import ScriptDirectory

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def check_migration_chain():
    """Check the migration chain for issues."""
    print("Checking migration chain...")
    
    try:
        cfg = Config('alembic.ini')
        script = ScriptDirectory.from_config(cfg)
        
        print("\nMigration chain:")
        migrations = []
        for rev in script.walk_revisions():
            migrations.append((rev.revision, rev.branch_labels[0] if rev.branch_labels else "no_label"))
            print(f"  {rev.revision}: {rev.branch_labels[0] if rev.branch_labels else 'no_label'}")
        
        print(f"\nTotal migrations: {len(migrations)}")
        
        # Check for circular dependencies
        print("\nChecking for circular dependencies...")
        revision_set = set()
        for rev, label in migrations:
            if rev in revision_set:
                print(f"  ERROR: Duplicate revision {rev}")
                return False
            revision_set.add(rev)
        
        print("  ✓ No circular dependencies found")
        
        # Check revision references
        print("\nChecking revision references...")
        for rev in script.walk_revisions():
            if rev.down_revision:
                if isinstance(rev.down_revision, tuple):
                    for down_rev in rev.down_revision:
                        if down_rev not in revision_set:
                            print(f"  ERROR: Revision {rev.revision} references non-existent {down_rev}")
                            return False
                else:
                    if rev.down_revision not in revision_set:
                        print(f"  ERROR: Revision {rev.revision} references non-existent {rev.down_revision}")
                        return False
        
        print("  ✓ All revision references are valid")
        
        return True
        
    except Exception as e:
        print(f"ERROR: Failed to check migration chain: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = check_migration_chain()
    sys.exit(0 if success else 1)

