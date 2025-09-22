#!/usr/bin/env python3
"""
Script to fix AuthService(db).get_current_user dependencies in all endpoint files
"""

import os
import re

# List of endpoint files to fix
endpoint_files = [
    "app/api/api_v1/endpoints/analytics.py",
    "app/api/api_v1/endpoints/analytics_enhanced.py", 
    "app/api/api_v1/endpoints/billing.py",
    "app/api/api_v1/endpoints/billing_enhanced.py",
    "app/api/api_v1/endpoints/chat_sessions.py",
    "app/api/api_v1/endpoints/documents.py",
    "app/api/api_v1/endpoints/embed_enhanced.py",
    "app/api/api_v1/endpoints/rag_query.py",
    "app/api/api_v1/endpoints/vector_search.py",
    "app/api/api_v1/endpoints/workspace.py",
    "app/api/api_v1/endpoints/white_label.py"
]

def fix_file(file_path):
    """Fix dependencies in a single file"""
    if not os.path.exists(file_path):
        print(f"File not found: {file_path}")
        return
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Add import if not already present
    if "from app.api.api_v1.dependencies import get_current_user" not in content:
        # Find the last import line
        lines = content.split('\n')
        import_end = 0
        for i, line in enumerate(lines):
            if line.startswith('from ') or line.startswith('import '):
                import_end = i
        
        # Insert the import after the last import
        lines.insert(import_end + 1, "from app.api.api_v1.dependencies import get_current_user")
        content = '\n'.join(lines)
    
    # Replace all occurrences
    old_pattern = r'current_user: User = Depends\(AuthService\(db\)\.get_current_user\)'
    new_pattern = 'current_user: User = Depends(get_current_user)'
    
    new_content = re.sub(old_pattern, new_pattern, content)
    
    if new_content != content:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print(f"Fixed: {file_path}")
    else:
        print(f"No changes needed: {file_path}")

def main():
    """Fix all endpoint files"""
    for file_path in endpoint_files:
        fix_file(file_path)
    print("All files processed!")

if __name__ == "__main__":
    main()
