"""
Standalone test that doesn't use pytest
"""

def test_python_imports():
    """Test that basic Python imports work"""
    import json
    import uuid
    import datetime
    print("✓ Python imports work")

def test_pydantic_imports():
    """Test that Pydantic imports work"""
    from pydantic import BaseModel
    from pydantic_settings import BaseSettings
    print("✓ Pydantic imports work")

def test_sqlalchemy_imports():
    """Test that SQLAlchemy imports work"""
    from sqlalchemy import Column, String, Integer
    from sqlalchemy.ext.declarative import declarative_base
    print("✓ SQLAlchemy imports work")

def test_fastapi_imports():
    """Test that FastAPI imports work"""
    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    print("✓ FastAPI imports work")

def test_basic_math():
    """Test basic Python functionality"""
    assert 2 + 2 == 4
    assert "hello" + " " + "world" == "hello world"
    print("✓ Basic math works")

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
    print("✓ File operations work")

def test_json_operations():
    """Test JSON operations"""
    import json
    
    data = {"key": "value", "number": 42}
    json_str = json.dumps(data)
    parsed_data = json.loads(json_str)
    
    assert parsed_data == data
    print("✓ JSON operations work")

def test_environment_variables():
    """Test environment variable access"""
    import os
    
    # Test that we can read environment variables
    path = os.environ.get('PATH')
    assert path is not None
    print("✓ Environment variables work")

def test_uuid_generation():
    """Test UUID generation"""
    import uuid
    
    # Generate a UUID
    test_uuid = uuid.uuid4()
    assert str(test_uuid) is not None
    print("✓ UUID generation works")

def test_datetime_operations():
    """Test datetime operations"""
    import datetime
    
    now = datetime.datetime.now()
    assert now is not None
    print("✓ Datetime operations work")

if __name__ == "__main__":
    print("Running standalone tests...")
    print("=" * 50)
    
    try:
        test_python_imports()
        test_pydantic_imports()
        test_sqlalchemy_imports()
        test_fastapi_imports()
        test_basic_math()
        test_file_operations()
        test_json_operations()
        test_environment_variables()
        test_uuid_generation()
        test_datetime_operations()
        
        print("=" * 50)
        print("✅ ALL TESTS PASSED!")
        print("The basic Python environment is working correctly.")
        
    except Exception as e:
        print("=" * 50)
        print(f"❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()

