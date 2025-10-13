#!/usr/bin/env python3
"""
Script to fix FastAPI Query regex deprecation warnings
Replace 'regex' parameter with 'pattern' in Query validators
"""

import re
import os
import glob

def fix_query_regex_file(file_path):
    """Fix Query regex usage in a file"""
    print(f"Fixing {file_path}...")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original_content = content
    
    # Fix Query regex parameter
    content = re.sub(
        r'Query\([^,]*,\s*regex="([^"]+)"\)',
        r'Query(\1, pattern="\1")',
        content
    )
    
    # Fix more complex Query patterns
    content = re.sub(
        r'Query\(([^,]+),\s*regex="([^"]+)"\)',
        r'Query(\1, pattern="\2")',
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
    """Fix all Python files with Query regex usage"""
    python_files = glob.glob('app/**/*.py', recursive=True)
    
    fixed_count = 0
    for file_path in python_files:
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                if 'regex=' in content and 'Query(' in content:
                    if fix_query_regex_file(file_path):
                        fixed_count += 1
    
    print(f"\n🎉 Fixed {fixed_count} files with Query regex deprecation issues")

if __name__ == "__main__":
    main()
