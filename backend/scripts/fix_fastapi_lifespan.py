#!/usr/bin/env python3
"""
Script to fix FastAPI on_event deprecation warnings
Replace @app.on_event with lifespan event handlers
"""

import re
import os
import glob

def fix_fastapi_file(file_path):
    """Fix FastAPI on_event usage in a file"""
    print(f"Fixing {file_path}...")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original_content = content
    
    # Add contextlib import if not present
    if 'from contextlib import asynccontextmanager' not in content:
        content = re.sub(
            r'(from fastapi import.*?\n)',
            r'\1from contextlib import asynccontextmanager\n',
            content
        )
    
    # Find startup and shutdown events
    startup_match = re.search(r'@app\.on_event\("startup"\)\s*\n\s*async def startup_event\(\):(.*?)(?=@app\.on_event\("shutdown"\)|$)', content, re.DOTALL)
    shutdown_match = re.search(r'@app\.on_event\("shutdown"\)\s*\n\s*async def shutdown_event\(\):(.*?)(?=if __name__|$)', content, re.DOTALL)
    
    if startup_match and shutdown_match:
        startup_code = startup_match.group(1).strip()
        shutdown_code = shutdown_match.group(1).strip()
        
        # Create lifespan function
        lifespan_code = f'''
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan event handler for startup and shutdown"""
    # Startup
{startup_code}
    
    yield
    
    # Shutdown
{shutdown_code}
'''
        
        # Remove old event handlers
        content = re.sub(r'@app\.on_event\("startup"\)\s*\n\s*async def startup_event\(\):.*?(?=@app\.on_event\("shutdown"\)|$)', '', content, flags=re.DOTALL)
        content = re.sub(r'@app\.on_event\("shutdown"\)\s*\n\s*async def shutdown_event\(\):.*?(?=if __name__|$)', '', content, flags=re.DOTALL)
        
        # Add lifespan function before app creation
        app_creation_match = re.search(r'(app = FastAPI\([^)]*\))', content)
        if app_creation_match:
            app_creation = app_creation_match.group(1)
            content = content.replace(app_creation, f'{lifespan_code}\n{app_creation}')
            
            # Update app creation to include lifespan
            content = re.sub(
                r'app = FastAPI\(([^)]*)\)',
                r'app = FastAPI(\1, lifespan=lifespan)',
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
    """Fix all Python files with FastAPI on_event usage"""
    python_files = glob.glob('app/**/*.py', recursive=True)
    
    fixed_count = 0
    for file_path in python_files:
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                if '@app.on_event' in content:
                    if fix_fastapi_file(file_path):
                        fixed_count += 1
    
    print(f"\n🎉 Fixed {fixed_count} files with FastAPI lifespan event issues")

if __name__ == "__main__":
    main()
