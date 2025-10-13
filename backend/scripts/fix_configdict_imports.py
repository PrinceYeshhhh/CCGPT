#!/usr/bin/env python3
"""
Script to fix missing ConfigDict imports in Pydantic schemas
"""

import re
import os
import glob

def fix_configdict_imports(file_path):
    """Fix ConfigDict imports in a file"""
    print(f"Fixing {file_path}...")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original_content = content
    
    # Check if ConfigDict is used but not imported
    if 'ConfigDict' in content and 'from pydantic import' in content:
        # Check if ConfigDict is already imported
        if 'ConfigDict' not in re.search(r'from pydantic import[^\n]*', content).group(0):
            # Add ConfigDict to existing pydantic import
            content = re.sub(
                r'(from pydantic import[^,\n]*)',
                r'\1, ConfigDict',
                content
            )
        elif 'from pydantic import BaseModel' in content and 'ConfigDict' not in content:
            # Replace BaseModel import with BaseModel, ConfigDict
            content = re.sub(
                r'from pydantic import BaseModel',
                'from pydantic import BaseModel, ConfigDict',
                content
            )
    
    # Only write if changes were made
    if content != original_content:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"✅ Fixed {file_path}")
        return True
    else:
        print(f"⏭️  No changes needed for {file_path}")
        return False

def main():
    """Fix all Python files with missing ConfigDict imports"""
    python_files = glob.glob('app/schemas/*.py', recursive=True)
    
    fixed_count = 0
    for file_path in python_files:
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                if 'ConfigDict' in content and 'from pydantic import' in content:
                    if fix_configdict_imports(file_path):
                        fixed_count += 1
    
    print(f"\n🎉 Fixed {fixed_count} files with ConfigDict import issues")

if __name__ == "__main__":
    main()
