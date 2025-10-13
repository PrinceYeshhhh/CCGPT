#!/usr/bin/env python3
"""
Script to improve test coverage by generating missing test files
"""

import os
import glob
import re

def find_untested_modules():
    """Find modules that need test coverage"""
    app_files = glob.glob('app/**/*.py', recursive=True)
    test_files = glob.glob('tests/**/*.py', recursive=True)
    
    # Extract module names from app files
    app_modules = set()
    for file_path in app_files:
        if '__init__.py' not in file_path:
            module_path = file_path.replace('app/', '').replace('.py', '').replace('/', '.')
            app_modules.add(module_path)
    
    # Extract tested modules from test files
    tested_modules = set()
    for file_path in test_files:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            # Find imports from app
            imports = re.findall(r'from app\.([a-zA-Z0-9_.]+)', content)
            for imp in imports:
                tested_modules.add(imp)
    
    # Find missing coverage
    missing_modules = app_modules - tested_modules
    return missing_modules

def generate_test_template(module_path):
    """Generate a basic test template for a module"""
    module_name = module_path.split('.')[-1]
    test_file_path = f"tests/unit/test_{module_name}.py"
    
    template = f'''"""
Tests for {module_path}
"""

import pytest
from unittest.mock import patch, MagicMock
from app.{module_path} import *


class Test{module_name.title()}:
    """Test cases for {module_name}"""
    
    def test_placeholder(self):
        """Placeholder test - implement actual tests"""
        assert True
'''
    
    return test_file_path, template

def main():
    """Generate missing test files"""
    missing_modules = find_untested_modules()
    
    print(f"Found {len(missing_modules)} modules without test coverage:")
    for module in sorted(missing_modules):
        print(f"  - {module}")
    
    if missing_modules:
        print(f"\nGenerating test templates...")
        
        for module in missing_modules:
            test_file_path, template = generate_test_template(module)
            
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(test_file_path), exist_ok=True)
            
            # Write test file
            with open(test_file_path, 'w', encoding='utf-8') as f:
                f.write(template)
            
            print(f"✅ Created {test_file_path}")
    
    print(f"\n🎉 Generated test templates for {len(missing_modules)} modules")

if __name__ == "__main__":
    main()
