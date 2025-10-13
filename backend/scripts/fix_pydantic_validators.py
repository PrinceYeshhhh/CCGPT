#!/usr/bin/env python3
"""
Script to fix Pydantic V1 to V2 migration issues
Reusable tool for maintaining Pydantic compatibility
"""

import re
import os
import glob

def fix_pydantic_file(file_path):
    """Fix Pydantic validators in a file"""
    print(f"Fixing {file_path}...")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original_content = content
    
    # Fix imports
    content = re.sub(r'from pydantic import ([^,]+), validator', r'from pydantic import \1, field_validator', content)
    content = re.sub(r'from pydantic import BaseModel, EmailStr, field_validator', r'from pydantic import BaseModel, EmailStr, field_validator, ConfigDict', content)
    
    # Fix validator decorators
    content = re.sub(r'@validator\(([^)]+)\)\s*\n\s*def (\w+)\(cls, v(?:, [^)]+)?\):', 
                     r'@field_validator(\1)\n    @classmethod\n    def \2(cls, v, info=None):', content)
    
    # Fix validator decorators with mode
    content = re.sub(r'@validator\(([^)]+), mode=[^)]+\)\s*\n\s*def (\w+)\(cls, v(?:, [^)]+)?\):', 
                     r'@field_validator(\1, mode="before")\n    @classmethod\n    def \2(cls, v, info=None):', content)
    
    # Fix validator decorators with pre=True
    content = re.sub(r'@validator\(([^)]+), pre=True(?:, always=True)?\)\s*\n\s*def (\w+)\(cls, v(?:, [^)]+)?\):', 
                     r'@field_validator(\1, mode="before")\n    @classmethod\n    def \2(cls, v, info=None):', content)
    
    # Fix values parameter usage
    content = re.sub(r'values\.get\(([^)]+)\)', r'info.data.get(\1) if hasattr(info, "data") and info.data else None', content)
    content = re.sub(r"'([^']+)' in values", r"hasattr(info, 'data') and '\1' in info.data", content)
    content = re.sub(r'values\[([^\]]+)\]', r'info.data[\1] if hasattr(info, "data") and info.data else None', content)
    
    # Fix class-based config
    content = re.sub(r'class Config:\s*\n\s*from_attributes = True', r'model_config = ConfigDict(from_attributes=True)', content)
    
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
    """Fix all Python files with Pydantic validators"""
    # Find all Python files in the app directory
    python_files = glob.glob('app/**/*.py', recursive=True)
    
    fixed_count = 0
    for file_path in python_files:
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                if '@validator' in content or 'class Config:' in content:
                    if fix_pydantic_file(file_path):
                        fixed_count += 1
    
    print(f"\n🎉 Fixed {fixed_count} files with Pydantic V1 to V2 migration issues")

if __name__ == "__main__":
    main()
