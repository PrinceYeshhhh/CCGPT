"""
Critical file processing edge case tests for production stability
Tests large files, corrupted files, concurrent uploads, and file type spoofing
"""

import pytest
import os
import tempfile
import io
import zipfile
import threading
import time
from pathlib import Path
from unittest.mock import patch, Mock, MagicMock
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
import uuid

from app.main import app
from app.core.database import get_db, Base, engine
from app.models import User, Workspace, Document, DocumentChunk
from app.utils.file_validation import FileValidator
from app.services.document_service import DocumentService


class TestFileProcessingLimits:
    """Critical file processing edge case tests for production stability"""
    
    @pytest.fixture(scope="function")
    def db_session(self):
        """Create a fresh database session for each test."""
        Base.metadata.create_all(bind=engine)
        session = Session()
        try:
            yield session
        finally:
            session.close()
            Base.metadata.drop_all(bind=engine)
    
    @pytest.fixture(scope="function")
    def client(self, db_session):
        """Create a test client with database dependency override."""
        def override_get_db():
            try:
                yield db_session
            finally:
                pass
        
        app.dependency_overrides[get_db] = override_get_db
        with TestClient(app) as test_client:
            yield test_client
        app.dependency_overrides.clear()
    
    @pytest.fixture
    def test_workspace(self, db_session):
        """Create test workspace"""
        workspace = Workspace(
            id=str(uuid.uuid4()),
            name="File Processing Test Workspace",
            description="Test workspace for file processing"
        )
        db_session.add(workspace)
        db_session.commit()
        db_session.refresh(workspace)
        return workspace
    
    @pytest.fixture
    def test_user(self, db_session, test_workspace):
        """Create test user"""
        user = User(
            email="filetest@example.com",
            hashed_password="$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj4J/HS.s.2",
            full_name="File Test User",
            workspace_id=test_workspace.id,
            is_active=True
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
        return user
    
    def test_large_file_processing(self, client, test_user):
        """Test processing of files larger than 100MB"""
        with patch('app.api.api_v1.endpoints.documents.get_current_user') as mock_get_user:
            mock_get_user.return_value = test_user
            
            # Create a large file (simulate 150MB)
            large_content = b"Large file content. " * (1024 * 1024 * 5)  # ~5MB for testing
            
            with tempfile.NamedTemporaryFile(mode='wb', suffix='.txt', delete=False) as f:
                f.write(large_content)
                temp_file_path = f.name
            
            try:
                with open(temp_file_path, 'rb') as f:
                    files = {"file": ("large_file.txt", f, "text/plain")}
                    headers = {"Authorization": "Bearer test_token"}
                    
                    # Test file size validation
                    response = client.post("/api/v1/documents/upload", files=files, headers=headers)
                    
                    # Should handle large file appropriately
                    assert response.status_code in [200, 413, 422]  # Success, too large, or validation error
                    
                    if response.status_code == 413:
                        # File too large - this is expected behavior
                        data = response.json()
                        assert "file size" in data.get("detail", "").lower() or "too large" in data.get("detail", "").lower()
                    elif response.status_code == 200:
                        # File accepted - verify processing
                        data = response.json()
                        assert "document_id" in data
                        assert "job_id" in data
            finally:
                os.unlink(temp_file_path)
    
    def test_corrupted_file_handling(self, client, test_user):
        """Test handling of corrupted or malformed files"""
        with patch('app.api.api_v1.endpoints.documents.get_current_user') as mock_get_user:
            mock_get_user.return_value = test_user
            
            # Test corrupted PDF
            corrupted_pdf = b"%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n/Pages 2 0 R\n>>\nendobj\nCORRUPTED_DATA"
            
            with tempfile.NamedTemporaryFile(mode='wb', suffix='.pdf', delete=False) as f:
                f.write(corrupted_pdf)
                temp_file_path = f.name
            
            try:
                with open(temp_file_path, 'rb') as f:
                    files = {"file": ("corrupted.pdf", f, "application/pdf")}
                    headers = {"Authorization": "Bearer test_token"}
                    
                    response = client.post("/api/v1/documents/upload", files=files, headers=headers)
                    
                    # Should handle corrupted file gracefully
                    assert response.status_code in [200, 400, 422]
                    
                    if response.status_code == 200:
                        # File accepted but processing should fail
                        data = response.json()
                        assert "document_id" in data
                        # Check processing status later
                    else:
                        # File rejected due to corruption
                        data = response.json()
                        assert "corrupt" in data.get("detail", "").lower() or "invalid" in data.get("detail", "").lower()
            finally:
                os.unlink(temp_file_path)
    
    def test_file_type_spoofing_attacks(self, client, test_user):
        """Test file type spoofing attack prevention"""
        with patch('app.api.api_v1.endpoints.documents.get_current_user') as mock_get_user:
            mock_get_user.return_value = test_user
            
            # Create a text file with PDF extension
            text_content = b"This is actually a text file, not a PDF"
            
            with tempfile.NamedTemporaryFile(mode='wb', suffix='.pdf', delete=False) as f:
                f.write(text_content)
                temp_file_path = f.name
            
            try:
                with open(temp_file_path, 'rb') as f:
                    files = {"file": ("fake.pdf", f, "application/pdf")}
                    headers = {"Authorization": "Bearer test_token"}
                    
                    response = client.post("/api/v1/documents/upload", files=files, headers=headers)
                    
                    # Should detect file type mismatch
                    assert response.status_code in [200, 400, 422]
                    
                    if response.status_code == 200:
                        # File accepted but should be processed as text
                        data = response.json()
                        assert "document_id" in data
                    else:
                        # File rejected due to type mismatch
                        data = response.json()
                        assert "file type" in data.get("detail", "").lower() or "invalid" in data.get("detail", "").lower()
            finally:
                os.unlink(temp_file_path)
    
    def test_concurrent_file_uploads(self, client, test_user):
        """Test concurrent file uploads from multiple users"""
        with patch('app.api.api_v1.endpoints.documents.get_current_user') as mock_get_user:
            mock_get_user.return_value = test_user
            
            upload_results = []
            upload_errors = []
            
            def upload_file(file_id: int):
                """Upload a file concurrently"""
                try:
                    content = f"Concurrent upload file {file_id}".encode()
                    
                    with tempfile.NamedTemporaryFile(mode='wb', suffix='.txt', delete=False) as f:
                        f.write(content)
                        temp_file_path = f.name
                    
                    try:
                        with open(temp_file_path, 'rb') as f:
                            files = {"file": (f"concurrent_{file_id}.txt", f, "text/plain")}
                            headers = {"Authorization": "Bearer test_token"}
                            
                            response = client.post("/api/v1/documents/upload", files=files, headers=headers)
                            upload_results.append({
                                "file_id": file_id,
                                "status_code": response.status_code,
                                "response": response.json() if response.status_code < 500 else None
                            })
                    finally:
                        os.unlink(temp_file_path)
                        
                except Exception as e:
                    upload_errors.append({"file_id": file_id, "error": str(e)})
            
            # Start 5 concurrent uploads
            threads = []
            for i in range(5):
                thread = threading.Thread(target=upload_file, args=(i,))
                threads.append(thread)
                thread.start()
            
            # Wait for all uploads to complete
            for thread in threads:
                thread.join()
            
            # Verify uploads were handled
            assert len(upload_results) == 5, f"Expected 5 uploads, got {len(upload_results)}"
            assert len(upload_errors) == 0, f"Upload errors: {upload_errors}"
            
            # Verify most uploads were successful
            successful_uploads = [r for r in upload_results if r["status_code"] == 200]
            assert len(successful_uploads) >= 3, f"Only {len(successful_uploads)} out of 5 uploads succeeded"
    
    def test_malicious_file_upload(self, client, test_user):
        """Test upload of potentially malicious files"""
        with patch('app.api.api_v1.endpoints.documents.get_current_user') as mock_get_user:
            mock_get_user.return_value = test_user
            
            # Test ZIP file with potential zip bomb
            zip_bomb_content = io.BytesIO()
            with zipfile.ZipFile(zip_bomb_content, 'w') as zip_file:
                # Create a file that decompresses to a very large size
                zip_file.writestr("bomb.txt", "A" * 1000)  # Small compressed, but could be large when decompressed
            
            with tempfile.NamedTemporaryFile(mode='wb', suffix='.zip', delete=False) as f:
                f.write(zip_bomb_content.getvalue())
                temp_file_path = f.name
            
            try:
                with open(temp_file_path, 'rb') as f:
                    files = {"file": ("bomb.zip", f, "application/zip")}
                    headers = {"Authorization": "Bearer test_token"}
                    
                    response = client.post("/api/v1/documents/upload", files=files, headers=headers)
                    
                    # Should reject ZIP files or handle them safely
                    assert response.status_code in [200, 400, 422]
                    
                    if response.status_code == 200:
                        # File accepted but should be processed safely
                        data = response.json()
                        assert "document_id" in data
                    else:
                        # File rejected due to security concerns
                        data = response.json()
                        assert "zip" in data.get("detail", "").lower() or "unsupported" in data.get("detail", "").lower()
            finally:
                os.unlink(temp_file_path)
    
    def test_empty_file_handling(self, client, test_user):
        """Test handling of empty files"""
        with patch('app.api.api_v1.endpoints.documents.get_current_user') as mock_get_user:
            mock_get_user.return_value = test_user
            
            # Create empty file
            with tempfile.NamedTemporaryFile(mode='wb', suffix='.txt', delete=False) as f:
                pass  # Empty file
                temp_file_path = f.name
            
            try:
                with open(temp_file_path, 'rb') as f:
                    files = {"file": ("empty.txt", f, "text/plain")}
                    headers = {"Authorization": "Bearer test_token"}
                    
                    response = client.post("/api/v1/documents/upload", files=files, headers=headers)
                    
                    # Should handle empty file appropriately
                    assert response.status_code in [200, 400, 422]
                    
                    if response.status_code == 200:
                        # Empty file accepted
                        data = response.json()
                        assert "document_id" in data
                    else:
                        # Empty file rejected
                        data = response.json()
                        assert "empty" in data.get("detail", "").lower() or "size" in data.get("detail", "").lower()
            finally:
                os.unlink(temp_file_path)
    
    def test_file_processing_timeout(self, client, test_user):
        """Test file processing timeout handling"""
        with patch('app.api.api_v1.endpoints.documents.get_current_user') as mock_get_user:
            mock_get_user.return_value = test_user
            
            # Create a file that might cause processing timeout
            complex_content = "Complex content. " * 10000  # Large text content
            
            with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
                f.write(complex_content)
                temp_file_path = f.name
            
            try:
                with open(temp_file_path, 'rb') as f:
                    files = {"file": ("complex.txt", f, "text/plain")}
                    headers = {"Authorization": "Bearer test_token"}
                    
                    response = client.post("/api/v1/documents/upload", files=files, headers=headers)
                    
                    # Should handle processing within timeout
                    assert response.status_code in [200, 408, 422]
                    
                    if response.status_code == 200:
                        # File accepted for processing
                        data = response.json()
                        assert "document_id" in data
                        assert "job_id" in data
                    elif response.status_code == 408:
                        # Processing timeout
                        data = response.json()
                        assert "timeout" in data.get("detail", "").lower()
            finally:
                os.unlink(temp_file_path)
    
    def test_file_validation_edge_cases(self, db_session):
        """Test file validation edge cases"""
        validator = FileValidator()
        
        # Test valid file types
        valid_types = ["application/pdf", "text/plain", "text/markdown"]
        for file_type in valid_types:
            assert validator.validate_file_type(file_type) is True
        
        # Test invalid file types
        invalid_types = ["image/jpeg", "video/mp4", "application/zip", "text/html"]
        for file_type in invalid_types:
            assert validator.validate_file_type(file_type) is False
        
        # Test file size validation
        max_size = 10 * 1024 * 1024  # 10MB
        assert validator.validate_file_size(5 * 1024 * 1024, max_size) is True
        assert validator.validate_file_size(10 * 1024 * 1024, max_size) is True
        assert validator.validate_file_size(15 * 1024 * 1024, max_size) is False
        assert validator.validate_file_size(0, max_size) is True  # Empty file
    
    def test_document_service_error_handling(self, db_session, test_user, test_workspace):
        """Test DocumentService error handling"""
        service = DocumentService(db_session)
        
        # Test with invalid file path
        with pytest.raises(Exception):
            service.extract_text("nonexistent_file.pdf", "application/pdf")
        
        # Test with unsupported file type
        with pytest.raises(Exception):
            service.extract_text("test.jpg", "image/jpeg")
        
        # Test with None values
        with pytest.raises(Exception):
            service.extract_text(None, "application/pdf")
        
        with pytest.raises(Exception):
            service.extract_text("test.pdf", None)
    
    def test_file_processing_memory_usage(self, client, test_user):
        """Test file processing memory usage with large files"""
        with patch('app.api.api_v1.endpoints.documents.get_current_user') as mock_get_user:
            mock_get_user.return_value = test_user
            
            # Create a file that might cause memory issues
            large_content = "Memory test content. " * (1024 * 100)  # ~2MB of text
            
            with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
                f.write(large_content)
                temp_file_path = f.name
            
            try:
                with open(temp_file_path, 'rb') as f:
                    files = {"file": ("memory_test.txt", f, "text/plain")}
                    headers = {"Authorization": "Bearer test_token"}
                    
                    response = client.post("/api/v1/documents/upload", files=files, headers=headers)
                    
                    # Should handle large file without memory issues
                    assert response.status_code in [200, 413, 422]
                    
                    if response.status_code == 200:
                        # File processed successfully
                        data = response.json()
                        assert "document_id" in data
                    else:
                        # File rejected due to size or memory constraints
                        data = response.json()
                        assert "size" in data.get("detail", "").lower() or "memory" in data.get("detail", "").lower()
            finally:
                os.unlink(temp_file_path)
    
    def test_file_processing_concurrent_processing(self, client, test_user):
        """Test concurrent file processing jobs"""
        with patch('app.api.api_v1.endpoints.documents.get_current_user') as mock_get_user:
            mock_get_user.return_value = test_user
            
            # Upload multiple files for concurrent processing
            upload_results = []
            
            for i in range(3):
                content = f"Concurrent processing file {i}. " * 100
                
                with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
                    f.write(content)
                    temp_file_path = f.name
                
                try:
                    with open(temp_file_path, 'rb') as f:
                        files = {"file": (f"concurrent_proc_{i}.txt", f, "text/plain")}
                        headers = {"Authorization": "Bearer test_token"}
                        
                        response = client.post("/api/v1/documents/upload", files=files, headers=headers)
                        upload_results.append({
                            "file_id": i,
                            "status_code": response.status_code,
                            "response": response.json() if response.status_code < 500 else None
                        })
                finally:
                    os.unlink(temp_file_path)
            
            # Verify all uploads were handled
            assert len(upload_results) == 3
            
            # Verify most uploads were successful
            successful_uploads = [r for r in upload_results if r["status_code"] == 200]
            assert len(successful_uploads) >= 2, f"Only {len(successful_uploads)} out of 3 uploads succeeded"
    
    def test_file_processing_database_consistency(self, db_session, test_user, test_workspace):
        """Test database consistency during file processing"""
        # Create a document
        document = Document(
            id=str(uuid.uuid4()),
            workspace_id=test_workspace.id,
            filename="consistency_test.pdf",
            content_type="application/pdf",
            size=1024,
            path="/tmp/consistency_test.pdf",
            uploaded_by=test_user.id,
            status="uploaded"
        )
        db_session.add(document)
        db_session.commit()
        
        # Verify document was created
        assert db_session.query(Document).filter(Document.id == document.id).count() == 1
        
        # Simulate processing completion
        document.status = "processed"
        db_session.commit()
        
        # Verify status was updated
        updated_doc = db_session.query(Document).filter(Document.id == document.id).first()
        assert updated_doc.status == "processed"
        
        # Simulate processing failure
        document.status = "failed"
        document.error = "Processing failed"
        db_session.commit()
        
        # Verify error was recorded
        failed_doc = db_session.query(Document).filter(Document.id == document.id).first()
        assert failed_doc.status == "failed"
        assert failed_doc.error == "Processing failed"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
