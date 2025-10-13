#!/usr/bin/env python3
"""
Script to fix TestClient usage in test files
Reusable tool for maintaining test compatibility
"""

import re
import os
import glob

def fix_test_file(file_path):
    """Fix TestClient usage in a test file"""
    print(f"Fixing {file_path}...")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original_content = content
    
    # Remove direct TestClient instantiation
    content = re.sub(r'client = TestClient\(app\)\n', '', content)
    
    # Find all test methods that use client
    test_methods = re.findall(r'def (test_\w+)\(self\):', content)
    
    # Find which methods actually use client
    methods_with_client = []
    for method in test_methods:
        # Look for client. usage in the method
        method_pattern = rf'def {method}\(self\):.*?(?=def|\Z)'
        method_match = re.search(method_pattern, content, re.DOTALL)
        if method_match and 'client.' in method_match.group():
            methods_with_client.append(method)
    
    # Update method signatures to include client parameter
    for method in methods_with_client:
        old_pattern = f'def {method}\(self\):'
        new_pattern = f'def {method}(self, client):'
        content = content.replace(old_pattern, new_pattern)
    
    # Only write if changes were made
    if content != original_content:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"✅ Fixed {len(methods_with_client)} methods in {file_path}")
        return True
    else:
        print(f"⏭️  No changes needed for {file_path}")
        return False

def main():
    """Fix all test files"""
    test_files = glob.glob('tests/**/*.py', recursive=True)
    
    fixed_count = 0
    for file_path in test_files:
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                if 'TestClient(app)' in content:
                    if fix_test_file(file_path):
                        fixed_count += 1
    
    print(f"\n🎉 Fixed {fixed_count} test files with TestClient usage issues")

if __name__ == "__main__":
    main()
