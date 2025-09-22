#!/usr/bin/env python3
"""
Script to fix UUID(as_uuid=True) references in all model files
"""

import os
import re

# List of model files to fix
model_files = [
    "app/models/chat.py",
    "app/models/document.py", 
    "app/models/embed.py",
    "app/models/subscriptions.py"
]

def fix_file(file_path):
    """Fix UUID references in a single file"""
    if not os.path.exists(file_path):
        print(f"File not found: {file_path}")
        return
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Replace UUID(as_uuid=True) with UUID()
    old_pattern = r'UUID\(as_uuid=True\)'
    new_pattern = 'UUID()'
    
    new_content = re.sub(old_pattern, new_pattern, content)
    
    if new_content != content:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print(f"Fixed: {file_path}")
    else:
        print(f"No changes needed: {file_path}")

def main():
    """Fix all model files"""
    for file_path in model_files:
        fix_file(file_path)
    print("All files processed!")

if __name__ == "__main__":
    main()
