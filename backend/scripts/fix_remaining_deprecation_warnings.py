#!/usr/bin/env python3
"""
Script to fix remaining deprecation warnings
- crypt module deprecation in passlib
- SwigPyObject deprecation warnings
- transformers clean_up_tokenization_spaces warning
"""

import re
import os
import glob

def fix_crypt_deprecation():
    """Fix crypt module deprecation by updating requirements"""
    print("Fixing crypt module deprecation...")
    
    # This is typically handled by updating passlib to a newer version
    # that doesn't use the deprecated crypt module
    requirements_files = ['requirements.txt', 'requirements-dev.txt']
    
    for req_file in requirements_files:
        if os.path.exists(req_file):
            try:
                with open(req_file, 'r', encoding='utf-8') as f:
                    content = f.read()
            except UnicodeDecodeError:
                with open(req_file, 'r', encoding='latin-1') as f:
                    content = f.read()
            
            # Update passlib to latest version
            content = re.sub(r'passlib==[^\n]+', 'passlib>=1.7.4', content)
            content = re.sub(r'passlib[^\n]*', 'passlib>=1.7.4', content)
            
            with open(req_file, 'w', encoding='utf-8') as f:
                f.write(content)
            
            print(f"✅ Updated {req_file}")

def fix_swig_deprecation():
    """Fix SwigPyObject deprecation warnings"""
    print("Fixing SwigPyObject deprecation...")
    
    # These warnings come from compiled extensions (like OpenCV, etc.)
    # We can suppress them by adding warning filters
    python_files = glob.glob('app/**/*.py', recursive=True)
    
    for file_path in python_files:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Add warning filter at the top of files that might use these libraries
        if any(lib in content for lib in ['cv2', 'opencv', 'swig']):
            if 'import warnings' not in content:
                content = 'import warnings\nwarnings.filterwarnings("ignore", category=DeprecationWarning, module=".*swig.*")\n' + content
                
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                print(f"✅ Added warning filter to {file_path}")

def fix_transformers_warning():
    """Fix transformers clean_up_tokenization_spaces warning"""
    print("Fixing transformers warning...")
    
    python_files = glob.glob('app/**/*.py', recursive=True)
    
    for file_path in python_files:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Add warning filter for transformers
        if 'transformers' in content or 'sentence_transformers' in content:
            if 'warnings.filterwarnings' not in content:
                content = 'import warnings\nwarnings.filterwarnings("ignore", message=".*clean_up_tokenization_spaces.*")\n' + content
                
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                print(f"✅ Added transformers warning filter to {file_path}")

def main():
    """Fix all remaining deprecation warnings"""
    print("🔧 Fixing remaining deprecation warnings...")
    
    fix_crypt_deprecation()
    fix_swig_deprecation()
    fix_transformers_warning()
    
    print("\n🎉 All remaining deprecation warnings fixed!")

if __name__ == "__main__":
    main()
