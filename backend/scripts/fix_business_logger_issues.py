#!/usr/bin/env python3
"""
Script to fix BusinessLogger issues
Replace business_logger.info with logger.info
"""

import re
import os
import glob

def fix_business_logger_file(file_path):
    """Fix BusinessLogger usage in a file"""
    print(f"Fixing {file_path}...")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original_content = content
    
    # Replace business_logger.info with logger.info
    content = re.sub(r'business_logger\.info\(', 'logger.info(', content)
    content = re.sub(r'business_logger\.error\(', 'logger.error(', content)
    content = re.sub(r'business_logger\.warning\(', 'logger.warning(', content)
    content = re.sub(r'business_logger\.debug\(', 'logger.debug(', content)
    
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
    """Fix all Python files with BusinessLogger issues"""
    python_files = glob.glob('app/**/*.py', recursive=True)
    
    fixed_count = 0
    for file_path in python_files:
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                if 'business_logger.' in content:
                    if fix_business_logger_file(file_path):
                        fixed_count += 1
    
    print(f"\n🎉 Fixed {fixed_count} files with BusinessLogger issues")

if __name__ == "__main__":
    main()
