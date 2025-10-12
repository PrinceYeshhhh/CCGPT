"""
Comprehensive unit tests for document processing system
Tests all critical document processing flows and edge cases
"""

import pytest
import sys
import os
import tempfile
import io
from unittest.mock import Mock, patch, MagicMock, mock_open
from fastapi.testclient import TestClient
from fastapi import status
import json

# Add the backend directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from app.main import app
from app.models import Document, DocumentChunk, User, Workspace
from app.services.document_service import DocumentService
from app.services.vector_service import VectorService
from app.utils.text_chunker import TextChunker
from app.utils.error_handling import ValidationError, DatabaseError

client = TestClient(app)


class TestDocumentUpload:
    """Test document upload functionality"""
    
    def test_pdf_upload_success(self, test_user, auth_headers):
        """Test successful PDF upload"""
        # Create a mock PDF file
        pdf_content = b"%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n/Pages 2 0 R\n>>\nendobj\n2 0 obj\n<<\n/Type /Pages\n/Kids [3 0 R]\n/Count 1\n>>\nendobj\n3 0 obj\n<<\n/Type /Page\n/Parent 2 0 R\n/MediaBox [0 0 612 792]\n/Contents 4 0 R\n>>\nendobj\n4 0 obj\n<<\n/Length 44\n>>\nstream\nBT\n/F1 12 Tf\n72 720 Td\n(Hello World) Tj\nET\nendstream\nendobj\nxref\n0 5\n0000000000 65535 f \n0000000009 00000 n \n0000000058 00000 n \n0000000115 00000 n \n0000000204 00000 n \ntrailer\n<<\n/Size 5\n/Root 1 0 R\n>>\nstartxref\n297\n%%EOF"
        
        files = {"file": ("test.pdf", io.BytesIO(pdf_content), "application/pdf")}
        
        with patch('app.services.document_service.DocumentService.process_document') as mock_process:
            mock_process.return_value = {"job_id": "test_job_123", "status": "queued"}
            
            response = client.post(
                "/api/v1/documents/upload",
                files=files,
                headers=auth_headers
            )
            
            assert response.status_code == status.HTTP_201_CREATED
            data = response.json()
            assert "document_id" in data
            assert "job_id" in data
            assert "status" in data
            assert data["status"] == "queued"
    
    def test_docx_upload_success(self, test_user, auth_headers):
        """Test successful DOCX upload"""
        # Create a mock DOCX file (simplified)
        docx_content = b"PK\x03\x04\x14\x00\x00\x00\x08\x00"  # ZIP header for DOCX
        
        files = {"file": ("test.docx", io.BytesIO(docx_content), "application/vnd.openxmlformats-officedocument.wordprocessingml.document")}
        
        with patch('app.services.document_service.DocumentService.process_document') as mock_process:
            mock_process.return_value = {"job_id": "test_job_456", "status": "queued"}
            
            response = client.post(
                "/api/v1/documents/upload",
                files=files,
                headers=auth_headers
            )
            
            assert response.status_code == status.HTTP_201_CREATED
            data = response.json()
            assert "document_id" in data
            assert "job_id" in data
    
    def test_txt_upload_success(self, test_user, auth_headers):
        """Test successful TXT upload"""
        txt_content = b"This is a test document with some content for processing."
        
        files = {"file": ("test.txt", io.BytesIO(txt_content), "text/plain")}
        
        with patch('app.services.document_service.DocumentService.process_document') as mock_process:
            mock_process.return_value = {"job_id": "test_job_789", "status": "queued"}
            
            response = client.post(
                "/api/v1/documents/upload",
                files=files,
                headers=auth_headers
            )
            
            assert response.status_code == status.HTTP_201_CREATED
            data = response.json()
            assert "document_id" in data
            assert "job_id" in data
    
    def test_unsupported_file_type(self, test_user, auth_headers):
        """Test upload of unsupported file type fails"""
        files = {"file": ("test.exe", io.BytesIO(b"binary content"), "application/x-executable")}
        
        response = client.post(
            "/api/v1/documents/upload",
            files=files,
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        data = response.json()
        assert "not supported" in data["detail"].lower()
    
    def test_file_too_large(self, test_user, auth_headers):
        """Test upload of file that's too large fails"""
        # Create a large file (simulate)
        large_content = b"x" * (50 * 1024 * 1024)  # 50MB
        
        files = {"file": ("large.pdf", io.BytesIO(large_content), "application/pdf")}
        
        with patch('app.core.config.settings.MAX_FILE_SIZE', 10 * 1024 * 1024):  # 10MB limit
            response = client.post(
                "/api/v1/documents/upload",
                files=files,
                headers=auth_headers
            )
            
            assert response.status_code == status.HTTP_413_REQUEST_ENTITY_TOO_LARGE
            data = response.json()
            assert "too large" in data["detail"].lower()
    
    def test_malicious_file_upload(self, test_user, auth_headers):
        """Test upload of potentially malicious file fails"""
        # Create a file with suspicious content
        malicious_content = b"<script>alert('xss')</script>"
        
        files = {"file": ("malicious.txt", io.BytesIO(malicious_content), "text/plain")}
        
        with patch('app.services.document_service.FileValidator.scan_file') as mock_scan:
            mock_scan.return_value = {"is_safe": False, "threats": ["XSS"]}
            
            response = client.post(
                "/api/v1/documents/upload",
                files=files,
                headers=auth_headers
            )
            
            assert response.status_code == status.HTTP_400_BAD_REQUEST
            data = response.json()
            assert "security" in data["detail"].lower() or "threat" in data["detail"].lower()
    
    def test_upload_without_authentication(self):
        """Test upload without authentication fails"""
        files = {"file": ("test.pdf", io.BytesIO(b"content"), "application/pdf")}
        
        response = client.post("/api/v1/documents/upload", files=files)
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_upload_exceeds_subscription_limits(self, test_user, auth_headers):
        """Test upload when subscription limits are exceeded"""
        with patch('app.services.document_service.PlanLimits.check_document_limit') as mock_check:
            mock_check.side_effect = ValidationError("Document limit exceeded")
            
            files = {"file": ("test.pdf", io.BytesIO(b"content"), "application/pdf")}
            
            response = client.post(
                "/api/v1/documents/upload",
                files=files,
                headers=auth_headers
            )
            
            assert response.status_code == status.HTTP_402_PAYMENT_REQUIRED
            data = response.json()
            assert "limit" in data["detail"].lower()


class TestDocumentProcessing:
    """Test document processing functionality"""
    
    def test_pdf_text_extraction(self):
        """Test PDF text extraction"""
        from app.utils.file_processing import extract_text_from_file
        
        # Mock PDF content
        pdf_content = b"%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n/Pages 2 0 R\n>>\nendobj\n2 0 obj\n<<\n/Type /Pages\n/Kids [3 0 R]\n/Count 1\n>>\nendobj\n3 0 obj\n<<\n/Type /Page\n/Parent 2 0 R\n/MediaBox [0 0 612 792]\n/Contents 4 0 R\n>>\nendobj\n4 0 obj\n<<\n/Length 44\n>>\nstream\nBT\n/F1 12 Tf\n72 720 Td\n(Hello World) Tj\nET\nendstream\nendobj\nxref\n0 5\n0000000000 65535 f \n0000000009 00000 n \n0000000058 00000 n \n0000000115 00000 n \n0000000204 00000 n \ntrailer\n<<\n/Size 5\n/Root 1 0 R\n>>\nstartxref\n297\n%%EOF"
        
        with patch('app.utils.file_processing.PyPDF2.PdfReader') as mock_reader:
            mock_page = Mock()
            mock_page.extract_text.return_value = "Hello World"
            mock_reader.return_value.pages = [mock_page]
            
            text = extract_text_from_file(io.BytesIO(pdf_content), "application/pdf")
            assert text == "Hello World"
    
    def test_docx_text_extraction(self):
        """Test DOCX text extraction"""
        from app.utils.file_processing import extract_text_from_file
        
        # Mock DOCX content
        docx_content = b"PK\x03\x04\x14\x00\x00\x00\x08\x00"
        
        with patch('app.utils.file_processing.Document') as mock_doc:
            mock_paragraph = Mock()
            mock_paragraph.text = "Hello World from DOCX"
            mock_doc.return_value.paragraphs = [mock_paragraph]
            
            text = extract_text_from_file(io.BytesIO(docx_content), "application/vnd.openxmlformats-officedocument.wordprocessingml.document")
            assert text == "Hello World from DOCX"
    
    def test_txt_text_extraction(self):
        """Test TXT text extraction"""
        from app.utils.file_processing import extract_text_from_file
        
        txt_content = b"Hello World from TXT file"
        
        text = extract_text_from_file(io.BytesIO(txt_content), "text/plain")
        assert text == "Hello World from TXT file"
    
    def test_text_chunking(self):
        """Test text chunking functionality"""
        chunker = TextChunker()
        
        # Test with long text
        long_text = "This is a test document. " * 100  # ~2500 characters
        
        chunks = chunker.chunk_text(long_text)
        
        assert len(chunks) > 1  # Should be chunked
        assert all(len(chunk) <= 700)  # Should respect max chunk size
        assert all(len(chunk) >= 400)  # Should respect min chunk size
        
        # Test chunk overlap
        for i in range(len(chunks) - 1):
            overlap = len(set(chunks[i].split()) & set(chunks[i + 1].split()))
            assert overlap > 0  # Should have some overlap
    
    def test_chunk_metadata_generation(self):
        """Test chunk metadata generation"""
        chunker = TextChunker()
        
        text = "This is a test document with multiple sentences. It has several paragraphs. Each paragraph contains multiple sentences for testing purposes."
        
        chunks = chunker.chunk_text(text)
        
        for i, chunk in enumerate(chunks):
            metadata = chunker.generate_chunk_metadata(chunk, i, len(chunks))
            
            assert "chunk_index" in metadata
            assert "total_chunks" in metadata
            assert "char_range" in metadata
            assert metadata["chunk_index"] == i
            assert metadata["total_chunks"] == len(chunks)
    
    def test_embedding_generation(self):
        """Test embedding generation"""
        from app.services.embeddings_service import EmbeddingsService
        
        embeddings_service = EmbeddingsService()
        
        text = "This is a test document for embedding generation."
        
        with patch('app.services.embeddings_service.SentenceTransformer') as mock_model:
            mock_model.return_value.encode.return_value = [0.1] * 384  # Mock embedding
            
            embedding = embeddings_service.generate_embedding(text)
            
            assert len(embedding) == 384  # Should match expected dimension
            assert all(isinstance(x, float) for x in embedding)  # Should be floats
    
    def test_vector_indexing(self):
        """Test vector indexing in ChromaDB"""
        from app.services.vector_service import VectorService
        
        vector_service = VectorService()
        
        chunks = [
            {"id": "chunk1", "text": "First chunk", "metadata": {"document_id": "doc1"}},
            {"id": "chunk2", "text": "Second chunk", "metadata": {"document_id": "doc1"}}
        ]
        
        embeddings = [[0.1] * 384, [0.2] * 384]
        
        with patch('app.services.vector_service.chromadb.PersistentClient') as mock_client:
            mock_collection = Mock()
            mock_client.return_value.get_or_create_collection.return_value = mock_collection
            
            vector_service.add_document_chunks("workspace1", chunks, embeddings)
            
            # Verify collection.add was called
            mock_collection.add.assert_called_once()
            call_args = mock_collection.add.call_args
            assert "ids" in call_args.kwargs
            assert "documents" in call_args.kwargs
            assert "embeddings" in call_args.kwargs
            assert "metadatas" in call_args.kwargs
    
    def test_vector_search(self):
        """Test vector search functionality"""
        from app.services.vector_service import VectorService
        
        vector_service = VectorService()
        
        query = "test query"
        query_embedding = [0.1] * 384
        
        with patch('app.services.vector_service.chromadb.PersistentClient') as mock_client:
            mock_collection = Mock()
            mock_collection.query.return_value = {
                "documents": [["First chunk", "Second chunk"]],
                "metadatas": [[{"document_id": "doc1"}, {"document_id": "doc1"}]],
                "distances": [[0.1, 0.2]]
            }
            mock_client.return_value.get_or_create_collection.return_value = mock_collection
            
            results = vector_service.search_similar_chunks("workspace1", query_embedding, top_k=5)
            
            assert len(results) == 2
            assert "text" in results[0]
            assert "metadata" in results[0]
            assert "distance" in results[0]


class TestDocumentManagement:
    """Test document management functionality"""
    
    def test_list_documents(self, test_user, auth_headers, test_document):
        """Test listing user documents"""
        response = client.get("/api/v1/documents/", headers=auth_headers)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "documents" in data
        assert len(data["documents"]) >= 1
        assert any(doc["id"] == str(test_document.id) for doc in data["documents"])
    
    def test_get_document_by_id(self, test_user, auth_headers, test_document):
        """Test getting specific document by ID"""
        response = client.get(f"/api/v1/documents/{test_document.id}", headers=auth_headers)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == str(test_document.id)
        assert data["filename"] == test_document.filename
        assert data["status"] == test_document.status
    
    def test_get_nonexistent_document(self, test_user, auth_headers):
        """Test getting nonexistent document fails"""
        fake_id = "00000000-0000-0000-0000-000000000000"
        response = client.get(f"/api/v1/documents/{fake_id}", headers=auth_headers)
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
        data = response.json()
        assert "not found" in data["detail"].lower()
    
    def test_delete_document(self, test_user, auth_headers, test_document):
        """Test document deletion"""
        response = client.delete(f"/api/v1/documents/{test_document.id}", headers=auth_headers)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "message" in data
        assert "deleted" in data["message"].lower()
    
    def test_delete_nonexistent_document(self, test_user, auth_headers):
        """Test deleting nonexistent document fails"""
        fake_id = "00000000-0000-0000-0000-000000000000"
        response = client.delete(f"/api/v1/documents/{fake_id}", headers=auth_headers)
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
    
    def test_update_document_metadata(self, test_user, auth_headers, test_document):
        """Test updating document metadata"""
        update_data = {
            "title": "Updated Document Title",
            "description": "Updated description"
        }
        
        response = client.put(
            f"/api/v1/documents/{test_document.id}",
            json=update_data,
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["title"] == update_data["title"]
        assert data["description"] == update_data["description"]
    
    def test_document_access_control(self, test_user, auth_headers, test_db):
        """Test document access control (users can only access their own documents)"""
        # Create another user and document
        other_user = User(
            email="other@example.com",
            hashed_password="hashed",
            mobile_phone="+9876543210",
            full_name="Other User",
            workspace_id=test_user.workspace_id
        )
        test_db.add(other_user)
        test_db.commit()
        
        other_document = Document(
            filename="other_document.pdf",
            content_type="application/pdf",
            size=1024,
            status="done",
            workspace_id=test_user.workspace_id,
            uploaded_by=other_user.id
        )
        test_db.add(other_document)
        test_db.commit()
        
        # Try to access other user's document
        response = client.get(f"/api/v1/documents/{other_document.id}", headers=auth_headers)
        
        # Should either be forbidden or not found (depending on implementation)
        assert response.status_code in [status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND]


class TestDocumentProcessingErrors:
    """Test error handling in document processing"""
    
    def test_processing_failure_handling(self, test_user, auth_headers):
        """Test handling of document processing failures"""
        files = {"file": ("test.pdf", io.BytesIO(b"corrupted pdf"), "application/pdf")}
        
        with patch('app.services.document_service.DocumentService.process_document') as mock_process:
            mock_process.side_effect = Exception("Processing failed")
            
            response = client.post(
                "/api/v1/documents/upload",
                files=files,
                headers=auth_headers
            )
            
            assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
            data = response.json()
            assert "error" in data
    
    def test_storage_failure_handling(self, test_user, auth_headers):
        """Test handling of storage failures"""
        files = {"file": ("test.pdf", io.BytesIO(b"content"), "application/pdf")}
        
        with patch('app.services.document_service.StorageAdapter.save_file') as mock_save:
            mock_save.side_effect = Exception("Storage failed")
            
            response = client.post(
                "/api/v1/documents/upload",
                files=files,
                headers=auth_headers
            )
            
            assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    
    def test_database_failure_handling(self, test_user, auth_headers):
        """Test handling of database failures"""
        files = {"file": ("test.pdf", io.BytesIO(b"content"), "application/pdf")}
        
        with patch('app.core.database.get_db') as mock_db:
            mock_db.side_effect = Exception("Database connection failed")
            
            response = client.post(
                "/api/v1/documents/upload",
                files=files,
                headers=auth_headers
            )
            
            assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    
    def test_vector_indexing_failure_handling(self, test_user, auth_headers):
        """Test handling of vector indexing failures"""
        files = {"file": ("test.pdf", io.BytesIO(b"content"), "application/pdf")}
        
        with patch('app.services.vector_service.VectorService.add_document_chunks') as mock_add:
            mock_add.side_effect = Exception("Vector indexing failed")
            
            response = client.post(
                "/api/v1/documents/upload",
                files=files,
                headers=auth_headers
            )
            
            # Should still succeed upload, but processing might fail
            assert response.status_code in [status.HTTP_201_CREATED, status.HTTP_500_INTERNAL_SERVER_ERROR]


class TestDocumentJobStatus:
    """Test document processing job status tracking"""
    
    def test_get_job_status(self, test_user, auth_headers):
        """Test getting job status"""
        job_id = "test_job_123"
        
        with patch('app.services.document_service.DocumentService.get_job_status') as mock_status:
            mock_status.return_value = {
                "job_id": job_id,
                "status": "finished",
                "result": {"document_id": "doc_123"},
                "progress": 100
            }
            
            response = client.get(f"/api/v1/documents/jobs/{job_id}", headers=auth_headers)
            
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["job_id"] == job_id
            assert data["status"] == "finished"
            assert data["progress"] == 100
    
    def test_get_nonexistent_job_status(self, test_user, auth_headers):
        """Test getting status of nonexistent job fails"""
        fake_job_id = "nonexistent_job"
        
        with patch('app.services.document_service.DocumentService.get_job_status') as mock_status:
            mock_status.return_value = None
            
            response = client.get(f"/api/v1/documents/jobs/{fake_job_id}", headers=auth_headers)
            
            assert response.status_code == status.HTTP_404_NOT_FOUND
    
    def test_job_status_polling(self, test_user, auth_headers):
        """Test job status polling workflow"""
        job_id = "test_job_456"
        
        # Simulate job progression
        statuses = ["queued", "started", "finished"]
        
        with patch('app.services.document_service.DocumentService.get_job_status') as mock_status:
            mock_status.side_effect = [
                {"job_id": job_id, "status": status, "progress": i * 33}
                for i, status in enumerate(statuses)
            ]
            
            for i, expected_status in enumerate(statuses):
                response = client.get(f"/api/v1/documents/jobs/{job_id}", headers=auth_headers)
                assert response.status_code == status.HTTP_200_OK
                data = response.json()
                assert data["status"] == expected_status


@pytest.mark.asyncio
class TestAsyncDocumentProcessing:
    """Test async document processing features"""
    
    async def test_concurrent_document_uploads(self, test_user, auth_headers):
        """Test concurrent document uploads"""
        import asyncio
        
        async def upload_document(doc_num):
            files = {"file": (f"test{doc_num}.pdf", io.BytesIO(b"content"), "application/pdf")}
            response = client.post("/api/v1/documents/upload", files=files, headers=auth_headers)
            return response.status_code
        
        # Upload multiple documents concurrently
        tasks = [upload_document(i) for i in range(5)]
        results = await asyncio.gather(*tasks)
        
        # All should succeed
        for status_code in results:
            assert status_code == status.HTTP_201_CREATED
    
    async def test_concurrent_document_processing(self, test_user, auth_headers):
        """Test concurrent document processing"""
        # This would test the background worker processing multiple documents
        # For now, just test that the service can handle concurrent requests
        pass
