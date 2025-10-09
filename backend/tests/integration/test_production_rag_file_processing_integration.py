"""
Integration tests for production RAG file processing system
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch, AsyncMock
from sqlalchemy.orm import Session
from datetime import datetime
import tempfile
import os

from app.main import app
from app.models.user import User
from app.models.workspace import Workspace
from app.models.document import Document, DocumentChunk
from app.core.database import get_db
from app.api.api_v1.dependencies import get_current_user


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def db_session():
    from app.db.session import SessionLocal
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def test_workspace(db_session):
    workspace = Workspace(
        id="test-workspace-id",
        name="Test Workspace",
        description="Test workspace for file processing"
    )
    db_session.add(workspace)
    db_session.commit()
    return workspace


@pytest.fixture
def test_user(db_session, test_workspace):
    user = User(
        id="test-user-id",
        email="test@example.com",
        username="testuser",
        hashed_password="hashed_password",
        workspace_id=test_workspace.id
    )
    db_session.add(user)
    db_session.commit()
    return user


@pytest.fixture
def auth_token(test_user):
    from app.services.auth import AuthService
    auth_service = AuthService()
    return auth_service.create_access_token({"sub": test_user.email})


def test_pdf_file_processing():
    """Test PDF file processing with production RAG system"""
    from app.services.production_rag_system import ProductionFileProcessor, FileType
    
    processor = ProductionFileProcessor()
    
    # Create a temporary PDF file
    with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_file:
        # Write minimal PDF content
        temp_file.write(b'%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n/Pages 2 0 R\n>>\nendobj\n')
        temp_file.flush()
        
        with patch('app.services.production_rag_system.fitz') as mock_fitz:
            mock_doc = Mock()
            mock_page = Mock()
            mock_page.get_text.return_value = "Sample PDF content for testing"
            mock_doc.__len__ = Mock(return_value=1)
            mock_doc.__getitem__ = Mock(return_value=mock_page)
            mock_fitz.open.return_value = mock_doc
            
            result = await processor.process_file(temp_file.name, FileType.PDF.value)
            
            assert len(result) > 0
            assert result[0].content == "Sample PDF content for testing"
            assert result[0].content_type == FileType.PDF.value
        
        os.unlink(temp_file.name)


def test_docx_file_processing():
    """Test DOCX file processing with production RAG system"""
    from app.services.production_rag_system import ProductionFileProcessor, FileType
    
    processor = ProductionFileProcessor()
    
    # Create a temporary DOCX file
    with tempfile.NamedTemporaryFile(suffix='.docx', delete=False) as temp_file:
        # Write minimal DOCX content
        temp_file.write(b'PK\x03\x04\x14\x00\x00\x00\x08\x00')
        temp_file.flush()
        
        with patch('app.services.production_rag_system.DocxDocument') as mock_docx:
            mock_doc = Mock()
            mock_paragraph = Mock()
            mock_paragraph.text = "Sample DOCX content for testing"
            mock_doc.paragraphs = [mock_paragraph]
            mock_docx.return_value = mock_doc
            
            result = await processor.process_file(temp_file.name, FileType.DOCX.value)
            
            assert len(result) > 0
            assert result[0].content == "Sample DOCX content for testing"
            assert result[0].content_type == FileType.DOCX.value
        
        os.unlink(temp_file.name)


def test_txt_file_processing():
    """Test TXT file processing with production RAG system"""
    from app.services.production_rag_system import ProductionFileProcessor, FileType
    
    processor = ProductionFileProcessor()
    
    # Create a temporary TXT file
    with tempfile.NamedTemporaryFile(suffix='.txt', delete=False) as temp_file:
        temp_file.write(b"Sample text content for testing\nThis is a multi-line text file.")
        temp_file.flush()
        
        result = await processor.process_file(temp_file.name, FileType.TXT.value)
        
        assert len(result) > 0
        assert "Sample text content for testing" in result[0].content
        assert result[0].content_type == FileType.TXT.value
        
        os.unlink(temp_file.name)


def test_markdown_file_processing():
    """Test Markdown file processing with production RAG system"""
    from app.services.production_rag_system import ProductionFileProcessor, FileType
    
    processor = ProductionFileProcessor()
    
    # Create a temporary MD file
    with tempfile.NamedTemporaryFile(suffix='.md', delete=False) as temp_file:
        temp_file.write(b"# Sample Markdown\n\nThis is **bold** text and *italic* text.")
        temp_file.flush()
        
        result = await processor.process_file(temp_file.name, FileType.MD.value)
        
        assert len(result) > 0
        assert "Sample Markdown" in result[0].content
        assert result[0].content_type == FileType.MD.value
        
        os.unlink(temp_file.name)


def test_csv_file_processing():
    """Test CSV file processing with production RAG system"""
    from app.services.production_rag_system import ProductionFileProcessor, FileType
    
    processor = ProductionFileProcessor()
    
    # Create a temporary CSV file
    with tempfile.NamedTemporaryFile(suffix='.csv', delete=False) as temp_file:
        temp_file.write(b"Name,Age,City\nJohn,25,New York\nJane,30,San Francisco")
        temp_file.flush()
        
        with patch('pandas.read_csv') as mock_pd:
            mock_df = Mock()
            mock_df.to_string.return_value = "Name,Age,City\nJohn,25,New York\nJane,30,San Francisco"
            mock_pd.return_value = mock_df
            
            result = await processor.process_file(temp_file.name, FileType.CSV.value)
            
            assert len(result) > 0
            assert "Name,Age,City" in result[0].content
            assert result[0].content_type == FileType.CSV.value
        
        os.unlink(temp_file.name)


def test_xlsx_file_processing():
    """Test XLSX file processing with production RAG system"""
    from app.services.production_rag_system import ProductionFileProcessor, FileType
    
    processor = ProductionFileProcessor()
    
    # Create a temporary XLSX file
    with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as temp_file:
        temp_file.write(b'PK\x03\x04\x14\x00\x00\x00\x08\x00')
        temp_file.flush()
        
        with patch('openpyxl.load_workbook') as mock_openpyxl:
            mock_wb = Mock()
            mock_ws = Mock()
            mock_ws.iter_rows.return_value = [
                ['Name', 'Age', 'City'],
                ['John', 25, 'New York'],
                ['Jane', 30, 'San Francisco']
            ]
            mock_wb.active = mock_ws
            mock_openpyxl.return_value = mock_wb
            
            result = await processor.process_file(temp_file.name, FileType.XLSX.value)
            
            assert len(result) > 0
            assert "Name" in result[0].content
            assert result[0].content_type == FileType.XLSX.value
        
        os.unlink(temp_file.name)


def test_json_file_processing():
    """Test JSON file processing with production RAG system"""
    from app.services.production_rag_system import ProductionFileProcessor, FileType
    
    processor = ProductionFileProcessor()
    
    # Create a temporary JSON file
    with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as temp_file:
        temp_file.write(b'{"name": "John", "age": 25, "city": "New York"}')
        temp_file.flush()
        
        result = await processor.process_file(temp_file.name, FileType.JSON.value)
        
        assert len(result) > 0
        assert "John" in result[0].content
        assert result[0].content_type == FileType.JSON.value
        
        os.unlink(temp_file.name)


def test_html_file_processing():
    """Test HTML file processing with production RAG system"""
    from app.services.production_rag_system import ProductionFileProcessor, FileType
    
    processor = ProductionFileProcessor()
    
    # Create a temporary HTML file
    with tempfile.NamedTemporaryFile(suffix='.html', delete=False) as temp_file:
        temp_file.write(b'<html><body><h1>Sample HTML</h1><p>This is a test paragraph.</p></body></html>')
        temp_file.flush()
        
        with patch('BeautifulSoup') as mock_bs:
            mock_soup = Mock()
            mock_soup.get_text.return_value = "Sample HTML\nThis is a test paragraph."
            mock_bs.return_value = mock_soup
            
            result = await processor.process_file(temp_file.name, FileType.HTML.value)
            
            assert len(result) > 0
            assert "Sample HTML" in result[0].content
            assert result[0].content_type == FileType.HTML.value
        
        os.unlink(temp_file.name)


def test_unsupported_file_type():
    """Test processing unsupported file type"""
    from app.services.production_rag_system import ProductionFileProcessor
    
    processor = ProductionFileProcessor()
    
    with tempfile.NamedTemporaryFile(suffix='.xyz', delete=False) as temp_file:
        temp_file.write(b"Some content")
        temp_file.flush()
        
        with pytest.raises(ValueError, match="Unsupported content type"):
            await processor.process_file(temp_file.name, "application/xyz")
        
        os.unlink(temp_file.name)


def test_file_processing_error_handling():
    """Test file processing error handling"""
    from app.services.production_rag_system import ProductionFileProcessor, FileType
    
    processor = ProductionFileProcessor()
    
    with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_file:
        temp_file.write(b"Invalid PDF content")
        temp_file.flush()
        
        with patch('app.services.production_rag_system.fitz') as mock_fitz:
            mock_fitz.open.side_effect = Exception("PDF parsing error")
            
            with pytest.raises(Exception, match="PDF parsing error"):
                await processor.process_file(temp_file.name, FileType.PDF.value)
        
        os.unlink(temp_file.name)


def test_file_processing_with_ml_models():
    """Test file processing with ML models enabled"""
    from app.services.production_rag_system import ProductionFileProcessor, FileType
    
    processor = ProductionFileProcessor()
    processor.ml_available = True
    
    with patch('app.services.production_rag_system.SentenceTransformer') as mock_st, \
         patch('app.services.production_rag_system.CrossEncoder') as mock_ce, \
         patch('app.services.production_rag_system.TfidfVectorizer') as mock_tfidf:
        
        # Mock ML models
        mock_st.return_value.encode.return_value = [[0.1, 0.2, 0.3]]
        mock_ce.return_value.predict.return_value = [0.8]
        mock_tfidf.return_value.fit_transform.return_value = Mock()
        
        with tempfile.NamedTemporaryFile(suffix='.txt', delete=False) as temp_file:
            temp_file.write(b"Sample text for ML processing")
            temp_file.flush()
            
            result = await processor.process_file(temp_file.name, FileType.TXT.value)
            
            assert len(result) > 0
            assert result[0].content == "Sample text for ML processing"
        
        os.unlink(temp_file.name)


def test_file_processing_chunking_strategies():
    """Test file processing with different chunking strategies"""
    from app.services.production_rag_system import ProductionFileProcessor, FileType, ChunkingStrategy
    
    # Test semantic chunking
    processor = ProductionFileProcessor(chunking_strategy=ChunkingStrategy.SEMANTIC)
    
    with tempfile.NamedTemporaryFile(suffix='.txt', delete=False) as temp_file:
        temp_file.write(b"This is a long text that should be chunked into smaller pieces for better processing and retrieval.")
        temp_file.flush()
        
        result = await processor.process_file(temp_file.name, FileType.TXT.value)
        
        assert len(result) > 0
        # Should be chunked based on semantic boundaries
        assert any("This is a long text" in chunk.content for chunk in result)
        
        os.unlink(temp_file.name)


def test_file_processing_integration_with_document_upload(client, db_session, test_user, auth_token):
    """Test file processing integration with document upload endpoint"""
    from app.models.document import Document
    
    # Create a test document
    document = Document(
        id="test-doc-id",
        workspace_id=test_user.workspace_id,
        filename="test.pdf",
        content_type="application/pdf",
        status="processing",
        file_size=1024
    )
    db_session.add(document)
    db_session.commit()
    
    with patch('app.services.production_rag_system.ProductionFileProcessor') as mock_processor_class:
        mock_processor = Mock()
        mock_processor.process_file.return_value = [
            Mock(content="Chunk 1 content", content_type="application/pdf"),
            Mock(content="Chunk 2 content", content_type="application/pdf")
        ]
        mock_processor_class.return_value = mock_processor
        
        with patch('app.services.document_service.DocumentService') as mock_doc_service:
            mock_doc_service_instance = Mock()
            mock_doc_service_instance.process_document.return_value = {
                "success": True,
                "chunks_created": 2
            }
            mock_doc_service.return_value = mock_doc_service_instance
            
            # Test document processing
            response = client.post(
                "/api/v1/documents/process",
                json={"document_id": "test-doc-id"},
                headers={"Authorization": f"Bearer {auth_token}"}
            )
            
            # Should process successfully
            assert response.status_code in [200, 201]


def test_file_processing_performance():
    """Test file processing performance with large files"""
    from app.services.production_rag_system import ProductionFileProcessor, FileType
    import time
    
    processor = ProductionFileProcessor()
    
    # Create a large text file
    large_content = "Sample text content. " * 1000  # ~20KB
    
    with tempfile.NamedTemporaryFile(suffix='.txt', delete=False) as temp_file:
        temp_file.write(large_content.encode())
        temp_file.flush()
        
        start_time = time.time()
        result = await processor.process_file(temp_file.name, FileType.TXT.value)
        end_time = time.time()
        
        processing_time = end_time - start_time
        
        # Should process within reasonable time (adjust threshold as needed)
        assert processing_time < 5.0  # 5 seconds max
        assert len(result) > 0
        
        os.unlink(temp_file.name)


def test_file_processing_memory_efficiency():
    """Test file processing memory efficiency"""
    from app.services.production_rag_system import ProductionFileProcessor, FileType
    import psutil
    import os
    
    processor = ProductionFileProcessor()
    
    # Get initial memory usage
    process = psutil.Process(os.getpid())
    initial_memory = process.memory_info().rss
    
    # Process multiple files
    for i in range(10):
        with tempfile.NamedTemporaryFile(suffix='.txt', delete=False) as temp_file:
            temp_file.write(f"Sample text content {i}".encode())
            temp_file.flush()
            
            result = await processor.process_file(temp_file.name, FileType.TXT.value)
            assert len(result) > 0
            
            os.unlink(temp_file.name)
    
    # Check memory usage hasn't grown excessively
    final_memory = process.memory_info().rss
    memory_growth = final_memory - initial_memory
    
    # Should not use more than 50MB for 10 small files
    assert memory_growth < 50 * 1024 * 1024  # 50MB

