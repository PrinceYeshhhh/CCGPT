#!/usr/bin/env python3
"""
Script to fix PyPDF2 deprecation warnings
Replace PyPDF2 with pypdf library
"""

import re
import os
import glob

def fix_pypdf2_file(file_path):
    """Fix PyPDF2 usage in a file"""
    print(f"Fixing {file_path}...")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original_content = content
    
    # Fix imports
    content = re.sub(r'import PyPDF2', 'import pypdf', content)
    content = re.sub(r'from PyPDF2', 'from pypdf', content)
    
    # Fix class names
    content = re.sub(r'PyPDF2\.PdfFileReader', 'pypdf.PdfReader', content)
    content = re.sub(r'PyPDF2\.PdfFileWriter', 'pypdf.PdfWriter', content)
    content = re.sub(r'PyPDF2\.PdfFileMerger', 'pypdf.PdfMerger', content)
    
    # Fix method names
    content = re.sub(r'\.getNumPages\(\)', '.get_num_pages()', content)
    content = re.sub(r'\.getPage\(', '.get_page(', content)
    content = re.sub(r'\.addPage\(', '.add_page(', content)
    content = re.sub(r'\.write\(', '.write(', content)
    
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
    """Fix all Python files with PyPDF2 usage"""
    python_files = glob.glob('app/**/*.py', recursive=True)
    
    fixed_count = 0
    for file_path in python_files:
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                if 'PyPDF2' in content:
                    if fix_pypdf2_file(file_path):
                        fixed_count += 1
    
    print(f"\n🎉 Fixed {fixed_count} files with PyPDF2 deprecation issues")

if __name__ == "__main__":
    main()
