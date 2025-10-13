#!/usr/bin/env python3
"""
Comprehensive script to fix all deprecation warnings
"""

import os
import subprocess
import sys

def run_script(script_name):
    """Run a maintenance script"""
    script_path = f"scripts/{script_name}"
    if os.path.exists(script_path):
        print(f"\n🔧 Running {script_name}...")
        try:
            result = subprocess.run([sys.executable, script_path], 
                                  capture_output=True, text=True, cwd='.')
            if result.returncode == 0:
                print(f"✅ {script_name} completed successfully")
                if result.stdout:
                    print(result.stdout)
            else:
                print(f"❌ {script_name} failed:")
                print(result.stderr)
        except Exception as e:
            print(f"❌ Error running {script_name}: {e}")
    else:
        print(f"⚠️  Script {script_name} not found")

def main():
    """Run all deprecation warning fixes"""
    print("🚀 Starting comprehensive deprecation warning fixes...")
    
    scripts_to_run = [
        "fix_pydantic_validators.py",
        "fix_testclient_usage.py", 
        "fix_fastapi_lifespan.py",
        "fix_query_regex_deprecation.py",
        "fix_pypdf2_deprecation.py"
    ]
    
    for script in scripts_to_run:
        run_script(script)
    
    print("\n🎉 All deprecation warning fixes completed!")
    print("\nNext steps:")
    print("1. Run tests to verify fixes")
    print("2. Update requirements.txt if needed")
    print("3. Run coverage analysis")

if __name__ == "__main__":
    main()
