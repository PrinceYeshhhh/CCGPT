"""
Simple tests that don't require full app initialization
"""

import pytest
import sys
import os

# Add the app directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

def test_python_imports():
    """Test that basic Python imports work"""
    import json
    import uuid
    import datetime
    assert True

def test_pydantic_imports():
    """Test that Pydantic imports work"""
    from pydantic import BaseModel
    from pydantic_settings import BaseSettings
    assert True

def test_sqlalchemy_imports():
    """Test that SQLAlchemy imports work"""
    from sqlalchemy import Column, String, Integer
    from sqlalchemy.ext.declarative import declarative_base
    assert True

def test_fastapi_imports():
    """Test that FastAPI imports work"""
    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    assert True

def test_basic_math():
    """Test basic Python functionality"""
    assert 2 + 2 == 4
    assert "hello" + " " + "world" == "hello world"

def test_file_operations():
    """Test basic file operations"""
    import tempfile
    import os
    
    # Create a temporary file
    with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
        f.write("test content")
        temp_file = f.name
    
    # Read it back
    with open(temp_file, 'r') as f:
        content = f.read()
    
    # Clean up
    os.unlink(temp_file)
    
    assert content == "test content"

def test_json_operations():
    """Test JSON operations"""
    import json
    
    data = {"key": "value", "number": 42}
    json_str = json.dumps(data)
    parsed_data = json.loads(json_str)
    
    assert parsed_data == data

if __name__ == "__main__":
    pytest.main([__file__, "-v"])

